import { RoomsPageContent } from "@/components/modules/rooms-page-content";

export default function RoomsPage() {
  return (
    <RoomsPageContent
      roomType="CLASSROOM"
      title="Rooms"
      description="Classrooms available for theory sessions"
      entityLabel="Room"
    />
  );
}
