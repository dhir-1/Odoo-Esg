import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { type DepartmentRank } from "@/lib/dashboard-mock-data";
import { useMounted } from "@/hooks/use-mounted";

interface DepartmentRankingChartProps {
  data: DepartmentRank[];
}

export function DepartmentRankingChart({ data }: DepartmentRankingChartProps) {
  const mounted = useMounted();

  const maxIndex = data.reduce(
    (maxIdx, item, idx) => (item.score > data[maxIdx].score ? idx : maxIdx),
    0,
  );

  if (!mounted) {
    return (
      <div className="h-[300px] w-full animate-pulse rounded-xl bg-muted" />
    );
  }

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-border)"
            horizontal={false}
          />
          <XAxis
            type="number"
            domain={[0, 100]}
            tick={{ fontSize: 12, fill: "var(--color-muted-foreground)" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="department"
            width={110}
            tick={{ fontSize: 12, fill: "var(--color-foreground)" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: "var(--color-muted)" }}
            contentStyle={{
              backgroundColor: "var(--color-card)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-card)",
              boxShadow: "var(--shadow-card)",
            }}
            labelStyle={{ color: "var(--color-foreground)" }}
          />
          <Bar
            dataKey="score"
            radius={[0, 6, 6, 0]}
            animationDuration={1200}
            animationEasing="ease-out"
          >
            {data.map((entry, index) => (
              <Cell
                key={entry.department}
                fill={
                  index === maxIndex
                    ? "var(--color-accent)"
                    : "var(--color-primary)"
                }
              />
            ))}
            <LabelList
              dataKey="score"
              position="right"
              className="fill-foreground text-xs font-body font-medium"
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
