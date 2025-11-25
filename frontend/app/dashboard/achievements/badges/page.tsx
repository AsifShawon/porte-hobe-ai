import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Award } from "lucide-react";

export default function BadgesPage() {
  return (
    <PlaceholderPage
      title="My Badges"
      description="Badges you've earned through learning"
      icon={Award}
      backLink="/dashboard/achievements"
    />
  );
}
