import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { type EmissionsPoint } from "@/lib/dashboard-mock-data";
import { useMounted } from "@/hooks/use-mounted";

interface EmissionsTrendChartProps {
  data: EmissionsPoint[];
}

export function EmissionsTrendChart({ data }: EmissionsTrendChartProps) {
  const mounted = useMounted();

  if (!mounted) {
    return (
      <div className="h-[300px] w-full animate-pulse rounded-xl bg-muted" />
    );
  }

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <defs>
            <linearGradient
              id="emissionsGradient"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="5%"
                stopColor="var(--color-accent)"
                stopOpacity={0.3}
              />
              <stop
                offset="95%"
                stopColor="var(--color-accent)"
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-border)"
            vertical={false}
          />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 12, fill: "var(--color-muted-foreground)" }}
            axisLine={{ stroke: "var(--color-border)" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "var(--color-muted-foreground)" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--color-card)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-card)",
              boxShadow: "var(--shadow-card)",
            }}
            labelStyle={{ color: "var(--color-foreground)" }}
            itemStyle={{ color: "var(--color-accent)" }}
          />
          <Area
            type="monotone"
            dataKey="co2e"
            stroke="var(--color-accent)"
            strokeWidth={3}
            fill="url(#emissionsGradient)"
            animationDuration={1500}
            animationEasing="ease-out"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
