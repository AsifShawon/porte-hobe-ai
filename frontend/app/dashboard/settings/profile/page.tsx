import { PlaceholderPage } from "@/components/PlaceholderPage";
import { User } from "lucide-react";

export default function ProfilePage() {
  return (
    <PlaceholderPage
      title="Profile Settings"
      description="Manage your profile information"
      icon={User}
      backLink="/dashboard/settings"
    />
  );
}
