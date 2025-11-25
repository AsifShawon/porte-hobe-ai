import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Flag } from "lucide-react";

export default function MilestonesPage() {
  return (
    <PlaceholderPage
      title="Milestones"
      description="Key learning milestones achieved"
      icon={Flag}
      backLink="/dashboard/achievements"
    />
  );
}
