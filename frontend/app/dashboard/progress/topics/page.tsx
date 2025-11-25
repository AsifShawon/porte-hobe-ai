import { PlaceholderPage } from "@/components/PlaceholderPage";
import { BookOpen } from "lucide-react";

export default function TopicProgressPage() {
  return (
    <PlaceholderPage
      title="Topic Progress"
      description="Detailed progress for each topic"
      icon={BookOpen}
      backLink="/dashboard/progress"
    />
  );
}
