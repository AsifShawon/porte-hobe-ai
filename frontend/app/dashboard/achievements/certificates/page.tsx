import { PlaceholderPage } from "@/components/PlaceholderPage";
import { FileCheck } from "lucide-react";

export default function CertificatesPage() {
  return (
    <PlaceholderPage
      title="Certificates"
      description="Certificates of completion"
      icon={FileCheck}
      backLink="/dashboard/achievements"
    />
  );
}
