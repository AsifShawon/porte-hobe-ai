import { PlaceholderPage } from "@/components/PlaceholderPage";
import { HelpCircle } from "lucide-react";

export default function QuizzesPage() {
  return (
    <PlaceholderPage
      title="Quizzes"
      description="Test your knowledge with quizzes"
      icon={HelpCircle}
      backLink="/dashboard/practice"
    />
  );
}
