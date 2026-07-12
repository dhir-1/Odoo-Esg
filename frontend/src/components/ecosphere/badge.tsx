import { cn } from "@/lib/utils";

export type BadgeVariant =
  | "primary"
  | "secondary"
  | "accent"
  | "gold"
  | "warning"
  | "danger"
  | "info";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variants: Record<BadgeVariant, string> = {
  primary: "bg-primary-50 text-primary-700",
  secondary: "bg-secondary-50 text-secondary-700",
  accent: "bg-accent-50 text-accent-700",
  gold: "bg-gold-50 text-gold-700",
  warning: "bg-warning/10 text-warning",
  danger: "bg-danger/10 text-danger",
  info: "bg-info/10 text-info",
};

export function Badge({
  variant = "primary",
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium font-body",
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
