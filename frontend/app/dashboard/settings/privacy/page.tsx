import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Shield } from "lucide-react";

export default function PrivacyPage() {
  return (
    <PlaceholderPage
      title="Privacy Settings"
      description="Manage your privacy and data"
      icon={Shield}
      backLink="/dashboard/settings"
    />
  );
}
