"use client";

import { useState } from "react";

import { BookmarkPlus, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ChatToNoteButtonProps {
  messageId?: string;
  messageContent: string;
  defaultTitle?: string;
}

export function ChatToNoteButton({ messageId, messageContent, defaultTitle }: ChatToNoteButtonProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [noteTitle, setNoteTitle] = useState(defaultTitle ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetState = () => {
    setDialogOpen(false);
    setNoteTitle(defaultTitle ?? "");
    setIsSaving(false);
    setIsSaved(false);
    setError(null);
  };

  const handleSave = async () => {
    if (!messageContent.trim()) {
      return;
    }
    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch("/api/notes/inject-from-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_message_id: messageId,
          content: messageContent,
          title: noteTitle || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save note");
      }

      setIsSaved(true);
      setTimeout(() => {
        resetState();
      }, 1200);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={dialogOpen} onOpenChange={(open) => (!open ? resetState() : setDialogOpen(true))}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2 text-xs">
          <BookmarkPlus className="h-3.5 w-3.5" />
          Add to note
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Save assistant reply</DialogTitle>
          <DialogDescription>
            Send this response to your notes for future reference.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="note-title">Note title</Label>
            <Input
              id="note-title"
              placeholder="AI tutor insights"
              value={noteTitle}
              onChange={(event) => setNoteTitle(event.target.value)}
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button className="w-full" onClick={handleSave} disabled={isSaving || isSaved}>
            {isSaved ? (
              <span className="flex items-center justify-center gap-2">
                <Check className="h-4 w-4" />
                Saved
              </span>
            ) : isSaving ? (
              "Saving..."
            ) : (
              "Save to notes"
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
