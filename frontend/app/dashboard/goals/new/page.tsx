import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Plus } from "lucide-react";

export default function NewGoalPage() {
  return (
    <PlaceholderPage
      title="Set New Goal"
      description="Create a new learning goal"
      icon={Plus}
      backLink="/dashboard/goals"
    />
  );
}
