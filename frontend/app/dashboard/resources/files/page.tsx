import { PlaceholderPage } from "@/components/PlaceholderPage";
import { Upload } from "lucide-react";

export default function UploadedFilesPage() {
  return (
    <PlaceholderPage
      title="Uploaded Files"
      description="Files you've uploaded for learning"
      icon={Upload}
      backLink="/dashboard/resources"
    />
  );
}
