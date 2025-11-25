import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Code } from "lucide-react";

export default function ChallengesPage() {
  return (
    <PlaceholderPage
      title="Coding Challenges"
      description="Test your skills with coding challenges"
      icon={Code}
      backLink="/dashboard/practice"
    />
  );
}
