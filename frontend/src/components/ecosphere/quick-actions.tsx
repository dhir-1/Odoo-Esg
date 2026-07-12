import { Plus, Trophy, FileBarChart } from "lucide-react";
import { Button } from "./button";

export function QuickActions() {
  return (
    <div>
      <h3 className="font-display text-lg font-semibold text-foreground">
        Quick Actions
      </h3>
      <div className="mt-4 grid grid-cols-1 gap-3">
        <Button variant="accent" size="lg" className="w-full justify-start">
          <Plus className="h-5 w-5" />
          Log Carbon Data
        </Button>
        <Button variant="gold" size="lg" className="w-full justify-start">
          <Trophy className="h-5 w-5" />
          Start Challenge
        </Button>
        <Button
          variant="outline-secondary"
          size="lg"
          className="w-full justify-start"
        >
          <FileBarChart className="h-5 w-5" />
          View Reports
        </Button>
      </div>
    </div>
  );
}
