import { Plus, Trophy, FileBarChart } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "./button";

export function QuickActions() {
  const navigate = useNavigate();

  return (
    <div>
      <h3 className="font-display text-lg font-semibold text-foreground">
        Quick Actions
      </h3>
      <div className="mt-4 grid grid-cols-1 gap-3">
        <Button
          variant="accent"
          size="lg"
          className="w-full justify-start"
          onClick={() => navigate("/environmental?tab=transactions&action=create")}
        >
          <Plus className="h-5 w-5" />
          Log Carbon Data
        </Button>
        <Button
          variant="gold"
          size="lg"
          className="w-full justify-start"
          onClick={() => navigate("/gamification?tab=challenges")}
        >
          <Trophy className="h-5 w-5" />
          Start Challenge
        </Button>
        <Button
          variant="outline-secondary"
          size="lg"
          className="w-full justify-start"
          onClick={() => navigate("/reports")}
        >
          <FileBarChart className="h-5 w-5" />
          View Reports
        </Button>
      </div>
    </div>
  );
}
