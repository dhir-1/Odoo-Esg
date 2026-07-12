import { useState, useEffect } from "react";
import { Card } from "@/components/ecosphere/card";
import { Button } from "@/components/ecosphere/button";
import { Badge } from "@/components/ecosphere/badge";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/contexts/auth-context";
import { toast } from "sonner";
import { Trophy, Gift, Award, Star, Flame, CheckCircle, Lock, Compass, Plus, UserRound, Building2 } from "lucide-react";

interface Challenge {
  id: number;
  title: string;
  category_id: number;
  description: string;
  xp_reward: number;
  difficulty: "Easy" | "Medium" | "Hard";
  evidence_required: boolean;
  deadline: string;
  status: string;
  has_joined?: boolean;
  joined_count?: number;
}

interface ChallengeParticipation {
  id: number;
  challenge_id: number;
  challenge_title?: string;
  progress: number;
  proof_url?: string;
  approval_status: string;
  xp_awarded: number;
}

interface BadgeItem {
  id: number;
  name: string;
  description: string;
  unlock_rule: Record<string, any>;
  icon_url?: string;
}

interface EmployeeBadge {
  id: number;
  badge_id: number;
  unlocked_at: string;
}

interface Reward {
  id: number;
  name: string;
  description: string;
  points_required: number;
  stock: number;
}

interface LeaderboardEntry {
  rank: number;
  entry_type: "employee" | "department";
  id: number;
  name: string;
  value: number;
}

interface UnifiedParticipation {
  id: number;
  source_type: "csr" | "challenge";
  item_title: string;
  proof_url?: string | null;
  approval_status: string;
  points_or_xp: number;
}

export function GamificationPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"challenges" | "my-challenges" | "badges" | "rewards" | "leaderboard">("challenges");
  
  // Data lists
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [myParticipations, setMyParticipations] = useState<UnifiedParticipation[]>([]);
  const [allBadges, setAllBadges] = useState<BadgeItem[]>([]);
  const [earnedBadges, setEarnedBadges] = useState<EmployeeBadge[]>([]);
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Challenge Status Filter
  const [challengeFilter, setChallengeFilter] = useState<string>("Active");

  // Progress submission modal states
  const [submittingProgressId, setSubmittingProgressId] = useState<number | null>(null);
  const [progressForm, setProgressForm] = useState({ progress: 50, proof_url: "" });

  const loadData = async ({ silent = false }: { silent?: boolean } = {}) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const [challs, bgs, rewds, lead, mine] = await Promise.all([
        apiFetch<Challenge[]>("/challenges/challenges/"),
        apiFetch<BadgeItem[]>("/badges/"),
        apiFetch<Reward[]>("/rewards/"),
        apiFetch<LeaderboardEntry[]>("/leaderboard"),
        apiFetch<UnifiedParticipation[]>("/participation/me")
      ]);

      // Load user earned badges if logged in
      let earned: EmployeeBadge[] = [];
      if (user?.id) {
        try {
          earned = await apiFetch<EmployeeBadge[]>(`/employees/${user.id}/badges`);
        } catch {
          earned = [];
        }
      }

      setChallenges(challs);
      setAllBadges(bgs);
      setEarnedBadges(earned);
      setRewards(rewds);
      setLeaderboard(lead);
      setMyParticipations(mine);
      setError(null);
    } catch (err: any) {
      toast.error(err.message || "Failed to load Gamification system data.");
    } finally {
      if (silent) setRefreshing(false);
      else setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const [error, setError] = useState<string | null>(null);

  const handleJoinChallenge = async (id: number) => {
    try {
      await apiFetch(`/challenges/challenges/${id}/join`, { method: "POST" });
      toast.success("Successfully joined the challenge! Let's build a greener future!");
      loadData({ silent: true });
    } catch (err: any) {
      toast.error(err.message || "Failed to join challenge.");
    }
  };

  const handleProgressSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!submittingProgressId) return;
    try {
      await apiFetch(`/challenges/participation/${submittingProgressId}/progress`, {
        method: "PATCH",
        body: JSON.stringify({
          progress: Number(progressForm.progress),
          proof_url: progressForm.proof_url || undefined
        })
      });
      toast.success("Challenge progress logged successfully!");
      setSubmittingProgressId(null);
      setProgressForm({ progress: 50, proof_url: "" });
      loadData({ silent: true });
    } catch (err: any) {
      toast.error(err.message || "Failed to log challenge progress.");
    }
  };

  const handleRedeemReward = async (reward: Reward) => {
    if ((user?.points_balance || 0) < reward.points_required) {
      toast.error("Insufficient points balance to redeem this reward.");
      return;
    }
    if (reward.stock <= 0) {
      toast.error("This item is currently out of stock!");
      return;
    }

    try {
      await apiFetch(`/rewards/${reward.id}/redeem`, { method: "POST" });
      toast.success(`Successfully redeemed ${reward.name}! Enjoy your reward.`);
      loadData({ silent: true });
    } catch (err: any) {
      if (err.status === 409) {
        toast.warning("Conflict error: Out of stock or already redeemed!");
      } else {
        toast.error(err.message || "Failed to redeem reward.");
      }
    }
  };

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  // Filter challenges by selected status filter
  const filteredChallenges = challenges.filter(c => c.status === challengeFilter);

  // Set of earned badge IDs
  const earnedIds = new Set(earnedBadges.map(eb => eb.badge_id));

  return (
    <div className="mx-auto max-w-7xl font-sans text-foreground">
      {refreshing && (
        <div className="fixed bottom-4 right-4 z-40 rounded-full border border-border bg-card px-4 py-2 text-sm shadow-card">
          Refreshing data...
        </div>
      )}
      {/* Rewards score header banner */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3 mb-6 bg-gradient-to-r from-gold-50 to-amber-50/50 border border-gold-200 rounded-card p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gold text-white shadow-md">
            <Trophy className="h-6 w-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-gold-700 uppercase tracking-wide">Workplace Rank</div>
            <div className="font-display text-xl font-bold text-foreground">
              #{leaderboard.find(l => l.entry_type === "employee" && l.id === user?.id)?.rank || "10+"} Overall
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent text-white shadow-md">
            <Flame className="h-6 w-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-accent-700 uppercase tracking-wide">Total XP Points</div>
            <div className="font-display text-xl font-bold text-foreground">{user?.xp_points || 0} XP</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-white shadow-md">
            <Star className="h-6 w-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-primary-700 uppercase tracking-wide">Reward Points Balance</div>
            <div className="font-display text-xl font-bold text-foreground">{user?.points_balance || 0} Points</div>
          </div>
        </div>
      </div>

      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl flex items-center gap-2">
            <Trophy className="h-7 w-7 text-gold" /> Gamification & Rewards
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Complete sustainability challenges, claim unique badges, and redeem points for premium rewards.
          </p>
        </div>
      </div>

      {submittingProgressId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card hover={false} className="w-full max-w-md p-6 bg-card border-t-4 border-t-gold animate-in fade-in zoom-in-95 duration-200">
            <h2 className="font-display text-lg font-bold mb-4">Log Challenge Progress</h2>
            <form onSubmit={handleProgressSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Completion Progress (%)</label>
                <input type="number" min="0" max="100" required value={progressForm.progress} onChange={(e) => setProgressForm({ ...progressForm, progress: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-gold" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Evidence URL (Optional)</label>
                <input type="url" placeholder="https://example.com/progress-screenshot" value={progressForm.proof_url} onChange={(e) => setProgressForm({ ...progressForm, proof_url: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-gold" />
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setSubmittingProgressId(null)}>Cancel</Button>
                <Button type="submit" variant="gold">Submit Progress</Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-border mb-6 overflow-x-auto">
        <button onClick={() => setActiveTab("challenges")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "challenges" ? "border-gold text-gold" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Active Challenges</button>
        <button onClick={() => setActiveTab("my-challenges")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "my-challenges" ? "border-gold text-gold" : "border-transparent text-muted-foreground hover:text-foreground"}`}>My Enrollments</button>
        <button onClick={() => setActiveTab("badges")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "badges" ? "border-gold text-gold" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Badges Gallery</button>
        <button onClick={() => setActiveTab("rewards")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "rewards" ? "border-gold text-gold" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Rewards Shop</button>
        <button onClick={() => setActiveTab("leaderboard")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "leaderboard" ? "border-gold text-gold" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Leaderboard</button>
      </div>

      {activeTab === "challenges" && (
        <div>
          {/* Status Subfilters */}
          <div className="flex gap-2 mb-6 overflow-x-auto py-1">
            {["Draft", "Active", "Under Review", "Completed", "Archived"].map((st) => (
              <button key={st} onClick={() => setChallengeFilter(st)} className={`px-3 py-1 text-xs font-semibold rounded-full border transition-all ${challengeFilter === st ? "bg-gold border-gold text-white" : "border-border text-muted-foreground hover:bg-muted"}`}>{st}</button>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredChallenges.length === 0 ? (
              <div className="col-span-full py-12 text-center text-muted-foreground border border-dashed border-border rounded-card">No challenges found matching status subfilter.</div>
            ) : (
              filteredChallenges.map((c) => (
                <Card key={c.id} accent="gold" className="flex flex-col justify-between h-full">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant="gold">{c.difficulty} Challenge</Badge>
                      <span className="text-xs text-muted-foreground font-body">Deadline: {c.deadline}</span>
                    </div>
                    <h3 className="font-display text-lg font-bold text-foreground mb-2">{c.title}</h3>
                    <p className="text-sm text-muted-foreground mb-4 line-clamp-3">{c.description}</p>
                    <div className="text-xs font-body font-semibold text-gold mb-4">
                      Reward: +{c.xp_reward} XP points
                    </div>
                  </div>

                  <div className="border-t border-border pt-4 mt-auto">
                    {c.has_joined ? (
                      <div className="text-center text-xs font-semibold text-gold py-1 bg-gold-50 border border-gold-100 rounded-lg">
                        Joined & In Progress
                      </div>
                    ) : (
                      <Button variant="gold" size="sm" className="w-full" onClick={() => handleJoinChallenge(c.id)}>
                        Join Challenge
                      </Button>
                    )}
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === "my-challenges" && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {myParticipations.length === 0 ? (
            <div className="col-span-full py-12 text-center text-muted-foreground border border-dashed border-border rounded-card">
              You haven't joined any active challenges yet. Go to the challenges directory to start!
            </div>
          ) : (
            myParticipations.map((part) => (
              <Card key={part.id} accent="gold" className="flex flex-col justify-between h-full">
                <div>
                  <div className="mb-2">
                    <Badge variant={part.source_type === "challenge" ? "gold" : "secondary"}>
                      {part.source_type === "challenge" ? "Challenge" : "CSR"}
                    </Badge>
                  </div>
                  <h3 className="font-display text-lg font-bold text-foreground mb-4">{part.item_title}</h3>
                  <div className="mb-4">
                    <div className="flex justify-between text-xs font-semibold mb-1">
                      <span>Completion Status</span>
                      <span>{part.approval_status}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Reward: {part.points_or_xp} {part.source_type === "challenge" ? "XP" : "points"}
                    </div>
                    {part.proof_url && (
                      <a
                        href={part.proof_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-block text-xs text-gold hover:underline"
                      >
                        View proof
                      </a>
                    )}
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {activeTab === "badges" && (
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {allBadges.map((badge) => {
            const earned = earnedIds.has(badge.id);
            return (
              <Card key={badge.id} hover={earned} className={`flex flex-col items-center text-center p-6 ${!earned ? "opacity-60 bg-muted/20" : "bg-card border-gold/30"}`}>
                <div className={`relative flex h-16 w-16 items-center justify-center rounded-full mb-3 ${earned ? "bg-gold text-white shadow-md" : "bg-muted text-muted-foreground"}`}>
                  {earned ? (
                    <Award className="h-8 w-8" />
                  ) : (
                    <>
                      <Award className="h-8 w-8 grayscale" />
                      <Lock className="absolute bottom-0 right-0 h-4 w-4 bg-muted border border-border text-muted-foreground rounded-full p-0.5" />
                    </>
                  )}
                </div>
                <h4 className="font-display text-sm font-bold text-foreground mb-1 leading-tight">{badge.name}</h4>
                <p className="text-xs text-muted-foreground leading-normal">{badge.description}</p>
                {!earned && badge.unlock_rule && (
                  <span className="text-[10px] font-semibold text-muted-foreground mt-2 uppercase tracking-wide">
                    Threshold: {badge.unlock_rule.threshold || badge.unlock_rule.points || 100}
                  </span>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {activeTab === "rewards" && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {rewards.map((r) => {
            const canAfford = (user?.points_balance || 0) >= r.points_required;
            const inStock = r.stock > 0;
            return (
              <Card key={r.id} accent={canAfford && inStock ? "gold" : "none"} className="flex flex-col justify-between h-full">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="gold">{r.points_required} Points</Badge>
                    <span className="text-xs text-muted-foreground font-body">Stock: {r.stock}</span>
                  </div>
                  <h3 className="font-display text-lg font-bold text-foreground mb-2">{r.name}</h3>
                  <p className="text-sm text-muted-foreground mb-4">{r.description}</p>
                </div>

                <div className="border-t border-border pt-4 mt-auto">
                  <Button
                    variant="gold"
                    size="sm"
                    className="w-full"
                    disabled={!canAfford || !inStock}
                    onClick={() => handleRedeemReward(r)}
                  >
                    {!inStock ? "Out of Stock" : !canAfford ? "Insufficient Points" : "Redeem Reward"}
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {activeTab === "leaderboard" && (
        <Card hover={false} className="overflow-x-auto p-0 border-l-4 border-l-gold">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs text-center w-16">Rank</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Entry</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs text-right">Value</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((l) => (
                <tr
                  key={`${l.entry_type}-${l.id}`}
                  className={`border-b border-border hover:bg-muted/10 transition-colors ${
                    l.entry_type === "employee" && l.id === user?.id ? "bg-gold-50/40" : ""
                  }`}
                >
                  <td className="p-4 text-center font-display font-bold">
                    {l.rank === 1 ? "🥇" : l.rank === 2 ? "🥈" : l.rank === 3 ? "🥉" : l.rank}
                  </td>
                  <td className="p-4 font-medium text-foreground">
                    <div className="flex items-center gap-2">
                      <Badge variant={l.entry_type === "department" ? "secondary" : "accent"} className="flex items-center gap-1">
                        {l.entry_type === "department" ? <Building2 className="h-3.5 w-3.5" /> : <UserRound className="h-3.5 w-3.5" />}
                        {l.entry_type === "department" ? "Department" : "Employee"}
                      </Badge>
                      <span>{l.name}</span>
                      {l.entry_type === "employee" && l.id === user?.id && <Badge variant="gold">You</Badge>}
                    </div>
                  </td>
                  <td className="p-4 font-body font-bold text-right text-gold">{l.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
