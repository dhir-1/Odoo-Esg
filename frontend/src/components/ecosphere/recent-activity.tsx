import { motion } from "framer-motion";
import { BarChart3, CheckCircle2, FileText, AlertTriangle } from "lucide-react";
import { type ActivityItem, type ActivityType } from "@/lib/dashboard-mock-data";

interface RecentActivityProps {
  items: ActivityItem[];
}

const iconConfig: Record<ActivityType, { icon: typeof CheckCircle2; color: string; bg: string }> = {
  success: {
    icon: CheckCircle2,
    color: "text-accent",
    bg: "bg-accent-50",
  },
  warning: {
    icon: AlertTriangle,
    color: "text-warning",
    bg: "bg-warning/10",
  },
  info: {
    icon: BarChart3,
    color: "text-info",
    bg: "bg-info/10",
  },
  document: {
    icon: FileText,
    color: "text-primary",
    bg: "bg-primary-50",
  },
};

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.07,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: -12 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: "easeOut" as const },
  },
};

export function RecentActivity({ items }: RecentActivityProps) {
  return (
    <div>
      <h3 className="font-display text-lg font-semibold text-foreground">
        Recent Activity
      </h3>
      <motion.ul
        variants={container}
        initial="hidden"
        animate="show"
        className="mt-4 space-y-3"
      >
        {items.map((activity) => {
          const { icon: Icon, color, bg } = iconConfig[activity.type];
          return (
            <motion.li
              key={activity.text}
              variants={item}
              className="flex items-start gap-3"
            >
              <div
                className={`mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${bg}`}
              >
                <Icon className={`h-4 w-4 ${color}`} />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium leading-relaxed text-foreground font-body">
                  {activity.text}
                </p>
                <p className="text-xs text-muted-foreground font-body">
                  {activity.timestamp}
                </p>
              </div>
            </motion.li>
          );
        })}
      </motion.ul>
    </div>
  );
}
