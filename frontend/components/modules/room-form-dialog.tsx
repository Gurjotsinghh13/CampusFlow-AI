"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiErrorMessage } from "@/lib/api-client";
import { roomFormSchema, type RoomFormValues } from "@/lib/validators/room";
import type { Room, RoomType } from "@/lib/types";

interface RoomFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  room: Room | null;
  roomType: RoomType;
  entityLabel: string;
  onCreate: (values: RoomFormValues) => Promise<unknown>;
  onUpdate: (id: string, values: RoomFormValues) => Promise<unknown>;
}

export function RoomFormDialog({
  open,
  onOpenChange,
  room,
  roomType,
  entityLabel,
  onCreate,
  onUpdate,
}: RoomFormDialogProps) {
  const isEditing = room !== null;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<RoomFormValues>({
    resolver: zodResolver(roomFormSchema),
    defaultValues: { room_number: "", capacity: 60, room_type: roomType },
  });

  useEffect(() => {
    if (open) {
      reset(
        room
          ? { room_number: room.room_number, capacity: room.capacity, room_type: room.room_type }
          : { room_number: "", capacity: 60, room_type: roomType }
      );
    }
  }, [open, room, roomType, reset]);

  async function onSubmit(values: RoomFormValues) {
    try {
      if (isEditing) {
        await onUpdate(room.id, values);
        toast.success(`${entityLabel} updated`);
      } else {
        await onCreate(values);
        toast.success(`${entityLabel} created`);
      }
      onOpenChange(false);
    } catch (error) {
      toast.error(apiErrorMessage(error));
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? `Edit ${entityLabel}` : `New ${entityLabel}`}</DialogTitle>
          <DialogDescription>
            {isEditing ? `Update this ${entityLabel.toLowerCase()}'s details.` : `Add a new ${entityLabel.toLowerCase()}.`}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <input type="hidden" {...register("room_type")} />
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="room_number">Room Number</Label>
            <Input id="room_number" placeholder="B-204" {...register("room_number")} />
            {errors.room_number && <p className="text-xs text-destructive">{errors.room_number.message}</p>}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="capacity">Capacity</Label>
            <Input id="capacity" type="number" min={1} max={1000} {...register("capacity")} />
            {errors.capacity && <p className="text-xs text-destructive">{errors.capacity.message}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEditing ? "Save Changes" : `Create ${entityLabel}`}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
