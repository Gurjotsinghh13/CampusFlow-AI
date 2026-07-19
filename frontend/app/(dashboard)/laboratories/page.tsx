import { RoomsPageContent } from "@/components/modules/rooms-page-content";

export default function LaboratoriesPage() {
  return (
    <RoomsPageContent
      roomType="LAB"
      title="Laboratories"
      description="Labs available for practical sessions"
      entityLabel="Laboratory"
    />
  );
}
