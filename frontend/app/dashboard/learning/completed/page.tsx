import { PlaceholderPage } from "@/components/PlaceholderPage";
import { CheckCircle } from "lucide-react";

export default function CompletedTopicsPage() {
  return (
    <PlaceholderPage
      title="Completed Topics"
      description="Topics you've mastered"
      icon={CheckCircle}
    />
  );
}
