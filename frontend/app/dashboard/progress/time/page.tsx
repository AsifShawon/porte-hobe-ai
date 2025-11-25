import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Clock } from "lucide-react";

export default function StudyTimePage() {
  return (
    <PlaceholderPage
      title="Study Time Tracker"
      description="Track time spent on learning"
      icon={Clock}
      backLink="/dashboard/progress"
    />
  );
}
