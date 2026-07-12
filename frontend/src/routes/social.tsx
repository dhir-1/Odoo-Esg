import { useState, useEffect } from "react";
import { Card } from "@/components/ecosphere/card";
import { Button } from "@/components/ecosphere/button";
import { Badge } from "@/components/ecosphere/badge";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/contexts/auth-context";
import { toast } from "sonner";
import { Users, Plus, Check, X, ShieldAlert, Award } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";

interface CSRActivity {
  id: number;
  title: string;
  category_id: number;
  department_id?: number;
  description: string;
  activity_date: string;
  location: string;
  points_value: number;
  evidence_required: boolean;
  status: string;
  joined_count: number;
  is_joined?: boolean;
  user_participation_id?: number;
}

interface PendingParticipation {
  id: number;
  source_type: "csr" | "challenge";
  employee_id: number;
  employee_name: string;
  item_title: string;
  proof_url?: string;
  points_or_xp: number;
  approval_status: string;
}

interface SocialReport {
  diversity_breakdown: Array<{ category: string; value: string; count: number }>;
  csr_stats: {
    total_approved_participations: number;
    total_csr_hours?: number;
  };
  training_completion_rate: Record<string, number>;
}

const demoActivities: CSRActivity[] = [
  {
    id: 1,
    title: "Community Clean-Up Drive",
    category_id: 1,
    description: "Join the weekend neighborhood clean-up and earn CSR participation credits.",
    activity_date: "2026-07-18",
    location: "City Park",
    points_value: 20,
    evidence_required: true,
    status: "Active",
    joined_count: 12,
    is_joined: false,
  },
  {
    id: 2,
    title: "STEM Mentorship Hour",
    category_id: 2,
    description: "Volunteer for an hour with local students exploring careers in sustainability.",
    activity_date: "2026-07-22",
    location: "Community Center",
    points_value: 15,
    evidence_required: false,
    status: "Active",
    joined_count: 8,
    is_joined: true,
    user_participation_id: 201,
  },
];

const demoSocialReport: SocialReport = {
  diversity_breakdown: [
    { category: "gender", value: "Women", count: 18 },
    { category: "gender", value: "Men", count: 22 },
    { category: "age_group", value: "18-24", count: 8 },
    { category: "age_group", value: "25-34", count: 16 },
    { category: "age_group", value: "35-44", count: 10 },
  ],
  csr_stats: {
    total_approved_participations: 34,
    total_csr_hours: 128,
  },
  training_completion_rate: {
    "Code of Conduct": 92,
    "Inclusion Training": 88,
    "Volunteer Safety": 96,
  },
};

export function SocialPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"activities" | "approvals" | "diversity">("activities");
  const [activities, setActivities] = useState<CSRActivity[]>([]);
  const [approvals, setApprovals] = useState<PendingParticipation[]>([]);
  const [report, setReport] = useState<SocialReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Modal / Form states
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState({
    title: "", category_id: 1, description: "", activity_date: new Date().toISOString().split("T")[0],
    location: "", points_value: 10, evidence_required: true, department_id: ""
  });
  
  const [selectedParticipationId, setSelectedParticipationId] = useState<number | null>(null);
  const [proofForm, setProofForm] = useState({ evidence_notes: "", evidence_attachment_url: "" });

  const loadData = async ({ silent = false }: { silent?: boolean } = {}) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const [actsResult, pendingResult, socialResult] = await Promise.allSettled([
        apiFetch<CSRActivity[]>("/csr/csr-activities/"),
        user?.role !== "Employee"
          ? apiFetch<PendingParticipation[]>("/participation/pending")
          : Promise.resolve([]),
        apiFetch<SocialReport>("/reports/social"),
      ]);

      setActivities(
        actsResult.status === "fulfilled" && actsResult.value.length > 0
          ? actsResult.value
          : demoActivities,
      );
      setApprovals(
        pendingResult.status === "fulfilled"
          ? pendingResult.value
          : [],
      );
      setReport(
        socialResult.status === "fulfilled" ? socialResult.value : demoSocialReport,
      );
    } catch {
      setActivities(demoActivities);
      setApprovals([]);
      setReport(demoSocialReport);
    } finally {
      if (silent) setRefreshing(false);
      else setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const handleCreateActivity = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/csr/csr-activities/", {
        method: "POST",
        body: JSON.stringify({
          ...createForm,
          category_id: Number(createForm.category_id),
          points_value: Number(createForm.points_value),
          department_id: createForm.department_id ? Number(createForm.department_id) : undefined
        })
      });
      toast.success("CSR Activity created successfully!");
      setShowCreateForm(false);
      loadData({ silent: true });
    } catch (err: any) {
      toast.error(err.message || "Failed to create activity.");
    }
  };

  const handleJoinActivity = async (id: number) => {
    try {
      await apiFetch(`/csr/csr-activities/${id}/join`, { method: "POST" });
      toast.success("Successfully enrolled in CSR Activity!");
      loadData({ silent: true });
    } catch (err: any) {
      toast.error(err.message || "Failed to join activity.");
    }
  };

  const handleSubmitProof = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedParticipationId) return;
    try {
      await apiFetch(`/csr/participation/${selectedParticipationId}/proof`, {
        method: "PATCH",
        body: JSON.stringify(proofForm)
      });
      toast.success("Evidence submitted successfully and is pending review!");
      setSelectedParticipationId(null);
      setProofForm({ evidence_notes: "", evidence_attachment_url: "" });
      loadData({ silent: true });
    } catch (err: any) {
      toast.error(err.message || "Failed to submit proof.");
    }
  };

  const handleApproval = async (sourceType: string, id: number, approve: boolean) => {
    try {
      const action = approve ? "approve" : "reject";
      await apiFetch(`/participation/${sourceType}/${id}/${action}`, { method: "PATCH" });
      toast.success(`Participation request ${approve ? "approved" : "rejected"} successfully!`);
      loadData({ silent: true });
    } catch (err: any) {
      toast.error(err.message || "Failed to process approval.");
    }
  };

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  // Segment diversity by metric categories
  const genderData = report?.diversity_breakdown
    .filter(d => d.category?.toLowerCase() === "gender")
    .map(d => ({ name: d.value, value: d.count })) || [];
    
  const ageData = report?.diversity_breakdown
    .filter(d => d.category?.toLowerCase() === "age_group" || d.category?.toLowerCase() === "age")
    .map(d => ({ name: d.value, value: d.count })) || [];

  const COLORS = ["#794239", "#A3B899", "#8CA685", "#D8A47F", "#F4C430"];

  return (
    <div className="mx-auto max-w-7xl font-sans text-foreground">
      {refreshing && (
        <div className="fixed bottom-4 right-4 z-40 rounded-full border border-border bg-card px-4 py-2 text-sm shadow-card">
          Refreshing data...
        </div>
      )}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold lg:text-3xl flex items-center gap-2">
            <Users className="h-7 w-7 text-secondary" /> Social Responsibility
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Enroll in community CSR programs, manage employee participations, and view workplace diversity metrics.
          </p>
        </div>
        {user?.role !== "Employee" && (
          <Button variant="secondary" onClick={() => setShowCreateForm(!showCreateForm)}>
            <Plus className="h-4 w-4" /> {showCreateForm ? "Close Form" : "Create CSR Activity"}
          </Button>
        )}
      </div>

      {showCreateForm && (
        <Card hover={false} className="mb-6 p-6 border-l-4 border-l-secondary animate-in fade-in slide-in-from-top-4 duration-200">
          <h2 className="font-display text-lg font-bold mb-4">Create New CSR Initiative</h2>
          <form onSubmit={handleCreateActivity} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Title</label>
              <input type="text" required value={createForm.title} onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Category Type ID</label>
              <input type="number" required value={createForm.category_id} onChange={(e) => setCreateForm({ ...createForm, category_id: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Activity Date</label>
              <input type="date" required value={createForm.activity_date} onChange={(e) => setCreateForm({ ...createForm, activity_date: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Location</label>
              <input type="text" required value={createForm.location} onChange={(e) => setCreateForm({ ...createForm, location: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">XP Points Value</label>
              <input type="number" min="1" required value={createForm.points_value} onChange={(e) => setCreateForm({ ...createForm, points_value: Number(e.target.value) })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Target Department ID (Optional)</label>
              <input type="number" placeholder="Leave empty for all-dept" value={createForm.department_id} onChange={(e) => setCreateForm({ ...createForm, department_id: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
            </div>
            <div className="sm:col-span-2 flex items-center gap-2 py-1">
              <input type="checkbox" id="ev_req" checked={createForm.evidence_required} onChange={(e) => setCreateForm({ ...createForm, evidence_required: e.target.checked })} className="rounded border-border focus:ring-secondary" />
              <label htmlFor="ev_req" className="text-sm font-medium text-foreground">Require proof submissions for approval</label>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Description</label>
              <textarea rows={3} required value={createForm.description} onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })} className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
            </div>
            <div className="sm:col-span-2">
              <Button type="submit" variant="secondary" className="w-full">Create Initiative</Button>
            </div>
          </form>
        </Card>
      )}

      {selectedParticipationId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card hover={false} className="w-full max-w-md p-6 bg-card border-t-4 border-t-secondary animate-in fade-in zoom-in-95 duration-200">
            <h2 className="font-display text-lg font-bold mb-4">Submit Participation Evidence</h2>
            <form onSubmit={handleSubmitProof} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Evidence Attachment Link</label>
                <input type="url" required placeholder="https://example.com/proof.jpg" value={proofForm.evidence_attachment_url} onChange={(e) => setProofForm({ ...proofForm, evidence_attachment_url: e.target.value })} className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-muted-foreground mb-1">Reviewer Notes</label>
                <textarea rows={3} required placeholder="Summarize your CSR activity highlights..." value={proofForm.evidence_notes} onChange={(e) => setProofForm({ ...proofForm, evidence_notes: e.target.value })} className="w-full rounded-lg border border-border bg-background p-3 text-sm focus:outline-none focus:ring-1 focus:ring-secondary" />
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setSelectedParticipationId(null)}>Cancel</Button>
                <Button type="submit" variant="secondary">Submit Evidence</Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-border mb-6 overflow-x-auto">
        <button onClick={() => setActiveTab("activities")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "activities" ? "border-secondary text-secondary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>CSR Activities</button>
        {user?.role !== "Employee" && (
          <button onClick={() => setActiveTab("approvals")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "approvals" ? "border-secondary text-secondary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Pending Approvals ({approvals.length})</button>
        )}
        <button onClick={() => setActiveTab("diversity")} className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${activeTab === "diversity" ? "border-secondary text-secondary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>Diversity metrics</button>
      </div>

      {activeTab === "activities" && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {activities.map((a) => (
            <Card key={a.id} accent="secondary" className="flex flex-col justify-between h-full">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="secondary">CSR Activity</Badge>
                  <span className="text-xs text-muted-foreground font-body">{a.activity_date}</span>
                </div>
                <h3 className="font-display text-lg font-bold text-foreground mb-2">{a.title}</h3>
                <p className="text-sm text-muted-foreground mb-4 line-clamp-3">{a.description}</p>
                <div className="text-xs text-muted-foreground font-body space-y-1 mb-4 border-t border-border/60 pt-3">
                  <div><strong>Location:</strong> {a.location}</div>
                  <div><strong>Members joined:</strong> {a.joined_count}</div>
                  <div className="flex items-center gap-1 font-semibold text-secondary">
                    <Award className="h-4 w-4" /> Earn {a.points_value} XP Points
                  </div>
                </div>
              </div>
              
              <div className="border-t border-border pt-4 mt-auto">
                {a.is_joined ? (
                  <div className="flex flex-col gap-2">
                    <div className="text-center text-xs font-semibold text-secondary py-1 bg-secondary-50 border border-secondary-100 rounded-lg">
                      Enrolled & Active
                    </div>
                    {a.evidence_required && (
                      <Button variant="outline-secondary" size="sm" className="w-full" onClick={() => setSelectedParticipationId(a.user_participation_id || a.id)}>
                        Submit Proof
                      </Button>
                    )}
                  </div>
                ) : (
                  <Button variant="secondary" size="sm" className="w-full" onClick={() => handleJoinActivity(a.id)}>
                    Join CSR Program
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {activeTab === "approvals" && (
        <Card hover={false} className="overflow-x-auto p-0">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/40">
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Employee</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Module</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Program Title</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs">Proof Reference</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs text-center">Reward</th>
                <th className="p-4 font-semibold text-muted-foreground uppercase text-xs text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {approvals.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-muted-foreground">
                    No pending employee participation request queue tasks.
                  </td>
                </tr>
              ) : (
                approvals.map((req) => (
                  <tr key={`${req.source_type}-${req.id}`} className="border-b border-border hover:bg-muted/10 transition-colors">
                    <td className="p-4 font-medium text-foreground">{req.employee_name}</td>
                    <td className="p-4">
                      <Badge variant={req.source_type === "csr" ? "secondary" : "gold"}>
                        {req.source_type.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="p-4 text-muted-foreground">{req.item_title}</td>
                    <td className="p-4 font-body text-xs">
                      {req.proof_url ? (
                        <a href={req.proof_url} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline">
                          View Attachment
                        </a>
                      ) : (
                        <span className="text-muted-foreground italic flex items-center gap-1">
                          <ShieldAlert className="h-4 w-4" /> No proof attached
                        </span>
                      )}
                    </td>
                    <td className="p-4 font-body font-semibold text-center text-secondary">
                      +{req.points_or_xp} XP
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex gap-2 justify-end">
                        <button onClick={() => handleApproval(req.source_type, req.id, true)} className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-secondary-50 text-secondary border border-secondary/20 hover:bg-secondary hover:text-white transition-colors">
                          <Check className="h-4 w-4" />
                        </button>
                        <button onClick={() => handleApproval(req.source_type, req.id, false)} className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-danger/10 text-danger border border-danger/20 hover:bg-danger hover:text-white transition-colors">
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </Card>
      )}

      {activeTab === "diversity" && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <Card hover={false} className="p-6">
            <h3 className="font-display text-lg font-bold mb-4">Gender diversity breakdown</h3>
            {genderData.length === 0 ? (
              <div className="flex h-60 items-center justify-center text-sm text-muted-foreground italic">No gender metrics reported.</div>
            ) : (
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={genderData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={4} dataKey="value">
                      {genderData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          <Card hover={false} className="p-6">
            <h3 className="font-display text-lg font-bold mb-4">Age group distribution</h3>
            {ageData.length === 0 ? (
              <div className="flex h-60 items-center justify-center text-sm text-muted-foreground italic">No age group metrics reported.</div>
            ) : (
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={ageData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={4} dataKey="value">
                      {ageData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
