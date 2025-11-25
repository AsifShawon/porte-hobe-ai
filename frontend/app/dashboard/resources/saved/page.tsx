import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Bookmark } from "lucide-react";

export default function SavedMaterialsPage() {
  return (
    <PlaceholderPage
      title="Saved Materials"
      description="Learning materials you've saved"
      icon={Bookmark}
      backLink="/dashboard/resources"
    />
  );
}
