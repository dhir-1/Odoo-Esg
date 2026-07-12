import { Card, type CardAccent } from "./card";
import { AnimatedNumber } from "./animated-number";

interface KpiTileProps {
  label: string;
  score: number;
  max?: number;
  accent: CardAccent;
}

export function KpiTile({ label, score, max = 100, accent }: KpiTileProps) {
  return (
    <Card accent={accent} className="flex flex-col justify-between gap-3">
      <span className="text-sm font-medium text-muted-foreground font-body">
        {label}
      </span>
      <div className="flex items-baseline gap-1">
        <span className="font-display text-4xl font-semibold text-foreground tabular-nums">
          <AnimatedNumber value={score} />
        </span>
        <span className="text-sm font-medium text-muted-foreground font-body">
          / {max}
        </span>
      </div>
    </Card>
  );
}
