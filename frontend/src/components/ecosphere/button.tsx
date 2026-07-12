import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "accent"
  | "gold"
  | "outline"
  | "outline-secondary";

interface ButtonProps extends HTMLMotionProps<"button"> {
  variant?: ButtonVariant;
  size?: "sm" | "md" | "lg";
}

const base =
  "inline-flex items-center justify-center gap-2 rounded-button font-body font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50";

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-primary-foreground hover:bg-primary-600 active:bg-primary-700",
  secondary:
    "bg-secondary text-primary-foreground hover:bg-secondary-600 active:bg-secondary-700",
  accent:
    "bg-accent text-primary-foreground hover:bg-accent-600 active:bg-accent-700",
  gold:
    "bg-gold text-primary-foreground hover:bg-gold-600 active:bg-gold-700",
  outline:
    "border border-border bg-card text-foreground hover:bg-muted",
  "outline-secondary":
    "border border-secondary bg-secondary-50 text-secondary-700 hover:bg-secondary-100",
};

const sizes = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-base",
};

export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <motion.button
      whileTap={{ scale: 0.97 }}
      transition={{ duration: 0.1 }}
      className={cn(base, variants[variant], sizes[size], className)}
      {...props}
    >
      {children}
    </motion.button>
  );
}
