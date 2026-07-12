import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

export type CardAccent = "primary" | "secondary" | "accent" | "gold" | "none";

interface CardProps extends HTMLMotionProps<"div"> {
  accent?: CardAccent;
  hover?: boolean;
}

const accentClasses: Record<CardAccent, string> = {
  primary: "border-l-4 border-l-primary",
  secondary: "border-l-4 border-l-secondary",
  accent: "border-l-4 border-l-accent",
  gold: "border-l-4 border-l-gold",
  none: "",
};

export function Card({
  accent = "none",
  hover = true,
  className,
  children,
  ...props
}: CardProps) {
  return (
    <motion.div
      whileHover={
        hover
          ? {
              y: -2,
              boxShadow: "var(--shadow-card-hover)",
            }
          : undefined
      }
      transition={{ duration: 0.2, ease: "easeOut" as const }}
      className={cn(
        "bg-card rounded-card border border-border shadow-card p-5",
        accentClasses[accent],
        className,
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
}
