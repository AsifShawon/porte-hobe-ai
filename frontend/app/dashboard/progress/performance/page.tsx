import { PlaceholderPage } from "@/components/PlaceholderPage";
import { BarChart3 } from "lucide-react";

export default function PerformancePage() {
  return (
    <PlaceholderPage
      title="Performance Analytics"
      description="Analyze your learning performance"
      icon={BarChart3}
      backLink="/dashboard/progress"
    />
  );
}
