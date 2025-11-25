import { PlaceholderPage } from "@/components/PlaceholderPage";
import { History } from "lucide-react";

export default function PracticeHistoryPage() {
  return (
    <PlaceholderPage
      title="Past Attempts"
      description="Review your practice history"
      icon={History}
      backLink="/dashboard/practice"
    />
  );
}
