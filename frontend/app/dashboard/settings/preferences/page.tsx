import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Sliders } from "lucide-react";

export default function PreferencesPage() {
  return (
    <PlaceholderPage
      title="Learning Preferences"
      description="Customize your learning experience"
      icon={Sliders}
      backLink="/dashboard/settings"
    />
  );
}
