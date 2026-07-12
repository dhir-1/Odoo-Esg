import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card } from "@/components/ecosphere/card";
import { KpiTile } from "@/components/ecosphere/kpi-tile";
import { EmissionsTrendChart } from "@/components/ecosphere/emissions-trend-chart";
import { DepartmentRankingChart } from "@/components/ecosphere/department-ranking-chart";
import { RecentActivity } from "@/components/ecosphere/recent-activity";
import { QuickActions } from "@/components/ecosphere/quick-actions";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/contexts/auth-context";
import { toast } from "sonner";

interface SummaryData {
  environmental_score: number;
  social_score: number;
  governance_score: number;
  overall_esg_score: number;
}

interface TrendPoint {
  period: string;
  co2e: number;
}

interface RankPoint {
  department_id: number;
  department_name: string;
  total_score: number;
  environmental_score: number;
  social_score: number;
  governance_score: number;
}

interface ActivityItem {
  id: number;
  event_type: string;
  actor_name: string;
  summary_text: string;
  created_at: string;
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.075,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" as const },
  },
};

export function DashboardPage() {
  const { user, token } = useAuth();
  const [summary, setSummary] = useState<SummaryData>({
    environmental_score: 0,
    social_score: 0,
    governance_score: 0,
    overall_esg_score: 0,
  });
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [ranking, setRanking] = useState<RankPoint[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      const summaryPromise = apiFetch<SummaryData>("/dashboard/summary");
      const trendPromise = apiFetch<TrendPoint[]>("/dashboard/emissions-trend");
      const rankingPromise = user?.role === "Admin"
        ? apiFetch<RankPoint[]>("/dashboard/department-ranking")
        : Promise.resolve([]);
      const activitiesPromise = apiFetch<ActivityItem[]>("/dashboard/recent-activity");

      const [summaryData, trendData, rankingData, activitiesData] = await Promise.all([
        summaryPromise,
        trendPromise,
        rankingPromise,
        activitiesPromise,
      ]);

      setSummary(summaryData);
      setTrend(trendData);
      setRanking(rankingData);
      setActivities(activitiesData);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard statistics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // Establish WebSocket Connection for Live Updates
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1")
      .replace(/^https?:\/\//, "")
      .replace(/\/$/, "");
    const wsUrl = `${wsProto}//${wsHost}/ws/live?token=${encodeURIComponent(token || "")}`;

    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "score_calculated") {
          toast.info(`Recalculated Score: Dept ${payload.data.department_id} Overall is ${payload.data.total_score}`);
          fetchDashboardData();
        } else if (payload.event === "leaderboard_delta") {
          toast.success(`Leaderboard Update: ${payload.data.full_name} gained ${payload.data.delta} ${payload.data.metric}`);
          fetchDashboardData();
        } else if (payload.event === "notification") {
          toast.info(`Notification: ${payload.data.title}`);
          fetchDashboardData();
        }
      } catch (err) {
        console.error("Failed to parse WS event payload:", err);
      }
    };

    ws.onerror = (err) => {
      console.warn("WebSocket connection encountered an error:", err);
    };

    return () => {
      ws.close();
    };
  }, [user, token]);

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-lg text-center mt-12 bg-danger/10 border border-danger/20 p-6 rounded-card">
        <h2 className="font-display text-xl font-bold text-danger">Error Loading Dashboard</h2>
        <p className="mt-2 text-sm text-muted-foreground">{error}</p>
        <button
          onClick={() => {
            setLoading(true);
            fetchDashboardData();
          }}
          className="mt-4 rounded-button bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary-600"
        >
          Try Again
        </button>
      </div>
    );
  }

  // Format Recharts data shapes
  const rechartsTrend = trend.map((t) => ({
    month: t.period,
    emissions: t.co2e,
  }));

  const rechartsRanking = ranking.map((r) => ({
    name: r.department_name,
    score: r.total_score,
  }));

  return (
    <div className="mx-auto max-w-7xl font-sans">
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-foreground lg:text-3xl">
          Dashboard
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Welcome back, {user?.full_name || "Alex"}. Here's how your organization is performing today.
        </p>
      </div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="space-y-6"
      >
        <motion.div
          variants={item}
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
        >
          <KpiTile
            label="Environmental Score"
            score={summary.environmental_score}
            accent="accent"
          />
          <KpiTile
            label="Social Score"
            score={summary.social_score}
            accent="secondary"
          />
          <KpiTile
            label="Governance Score"
            score={summary.governance_score}
            accent="primary"
          />
          <KpiTile
            label="Overall ESG Score"
            score={summary.overall_esg_score}
            accent="primary"
          />
        </motion.div>

        <motion.div
          variants={item}
          className="grid grid-cols-1 gap-4 lg:grid-cols-2"
        >
          <Card className="h-[420px]">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold text-foreground">
                Emissions Trend ({trend.length} mo)
              </h2>
              <span className="text-xs text-muted-foreground">CO₂e (kg)</span>
            </div>
            <EmissionsTrendChart data={rechartsTrend} />
          </Card>
          
          <Card className="h-[420px]">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold text-foreground">
                Department ESG Ranking
              </h2>
              <span className="text-xs text-muted-foreground">
                {user?.role === "Admin" ? "Top performer highlighted" : "Scores comparison (Admin-only)"}
              </span>
            </div>
            {user?.role === "Admin" ? (
              <DepartmentRankingChart data={rechartsRanking} />
            ) : (
              <div className="flex h-full flex-col items-center justify-center border border-dashed border-border rounded-lg p-6">
                <p className="text-sm text-muted-foreground text-center">
                  Department ranking comparisons are restricted to administrators.
                </p>
              </div>
            )}
          </Card>
        </motion.div>

        <motion.div
          variants={item}
          className="grid grid-cols-1 gap-4 lg:grid-cols-2"
        >
          <Card className="h-full">
            <RecentActivity items={activities.map((a) => ({
              id: a.id,
              user: a.actor_name || "System",
              action: a.summary_text,
              time: new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            }))} />
          </Card>
          <Card className="h-full">
            <QuickActions />
          </Card>
        </motion.div>
      </motion.div>
    </div>
  );
}

