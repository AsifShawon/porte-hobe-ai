import { PlaceholderPage } from "@/components/PlaceholderPage";
import { StickyNote } from "lucide-react";

export default function NotesPage() {
  return (
    <PlaceholderPage
      title="My Notes"
      description="Personal notes and annotations"
      icon={StickyNote}
      backLink="/dashboard/resources"
    />
  );
}
