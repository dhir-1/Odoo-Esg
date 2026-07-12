import { Link } from "react-router-dom";
import { ArrowLeft, type LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import { Card } from "./card";
import { Button } from "./button";

interface ModulePlaceholderProps {
  title: string;
  color: "primary" | "secondary" | "accent" | "gold";
  icon: LucideIcon;
}

const colorMap = {
  primary: "border-l-primary text-primary",
  secondary: "border-l-secondary text-secondary",
  accent: "border-l-accent text-accent",
  gold: "border-l-gold text-gold",
};

export function ModulePlaceholder({
  title,
  color,
  icon: Icon,
}: ModulePlaceholderProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="mx-auto max-w-2xl"
    >
      <Card accent={color} className="p-10 text-center">
        <div
          className={`mx-auto mb-6 inline-flex h-16 w-16 items-center justify-center rounded-full bg-background border border-border ${colorMap[color]}`}
        >
          <Icon className="h-8 w-8" />
        </div>
        <h1 className="font-display text-3xl font-semibold text-foreground">
          {title}
        </h1>
        <p className="mt-2 text-muted-foreground">
          This module is coming soon. Check back for updates.
        </p>
        <div className="mt-8">
          <Link to="/">
            <Button variant="outline">
              <ArrowLeft className="h-4 w-4" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </Card>
    </motion.div>
  );
}
