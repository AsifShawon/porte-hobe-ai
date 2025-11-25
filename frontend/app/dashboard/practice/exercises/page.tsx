import { PlaceholderPage } from "@/components/PlaceholderPage";
import { FileText } from "lucide-react";

export default function ExercisesPage() {
  return (
    <PlaceholderPage
      title="All Exercises"
      description="Practice exercises for all topics"
      icon={FileText}
      backLink="/dashboard/practice"
    />
  );
}
