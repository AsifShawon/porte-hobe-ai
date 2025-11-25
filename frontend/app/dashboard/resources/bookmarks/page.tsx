import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Star } from "lucide-react";

export default function BookmarksPage() {
  return (
    <PlaceholderPage
      title="Bookmarks"
      description="Bookmarked topics and resources"
      icon={Star}
      backLink="/dashboard/resources"
    />
  );
}
