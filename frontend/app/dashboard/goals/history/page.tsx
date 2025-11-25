import { PlaceholderPage } from "@/components/PlaceholderPage";
import { History } from "lucide-react";

export default function GoalHistoryPage() {
  return (
    <PlaceholderPage
      title="Goal History"
      description="Review your past goals"
      icon={History}
      backLink="/dashboard/goals"
    />
  );
}
