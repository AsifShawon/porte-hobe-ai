"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { useRouter, useParams } from "next/navigation";
import { NoteEditor } from "@/components/notes/NoteEditor";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, Trash2, Star } from "lucide-react";
import { useDebouncedCallback } from "use-debounce";

interface Note {
  id: string;
  title: string;
  content_json: Record<string, unknown>;
  folder_id?: string | null;
  is_favorite?: boolean;
  is_archived?: boolean;
  created_at?: string;
  updated_at?: string;
}

export default function NoteDetailPage() {
  const { user, session, loading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const noteId = params.id as string;

  const [note, setNote] = useState<Note | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [title, setTitle] = useState("");

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user && session && noteId) {
      fetchNote();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, session, noteId]);

  const fetchNote = async () => {
    if (!session?.access_token) return;

    setIsLoading(true);
    try {
      const response = await fetch(`/api/notes/${noteId}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });
      if (!response.ok) {
        throw new Error("Failed to fetch note");
      }
      const data = await response.json();
      setNote(data.note);
      setTitle(data.note.title || "Untitled Note");
    } catch (error) {
      console.error("Failed to fetch note:", error);
      router.push("/dashboard/resources/notes");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveContent = async (content: Record<string, unknown>) => {
    if (!session?.access_token) return;

    try {
      await fetch(`/api/notes/${noteId}`, {
        method: "PATCH",
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ content_json: content }),
      });
    } catch (error) {
      console.error("Failed to save note content:", error);
    }
  };

  const debouncedSaveTitle = useDebouncedCallback(async (newTitle: string) => {
    if (!session?.access_token) return;

    try {
      await fetch(`/api/notes/${noteId}`, {
        method: "PATCH",
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ title: newTitle }),
      });
    } catch (error) {
      console.error("Failed to save note title:", error);
    }
  }, 500);

  const handleTitleChange = (newTitle: string) => {
    setTitle(newTitle);
    debouncedSaveTitle(newTitle);
  };

  const handleToggleFavorite = async () => {
    if (!note || !session?.access_token) return;
    const newFavoriteState = !note.is_favorite;

    try {
      await fetch(`/api/notes/${noteId}`, {
        method: "PATCH",
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ is_favorite: newFavoriteState }),
      });
      setNote({ ...note, is_favorite: newFavoriteState });
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this note?") || !session?.access_token) return;

    try {
      await fetch(`/api/notes/${noteId}`, {
        method: "DELETE",
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });
      router.push("/dashboard/resources/notes");
    } catch (error) {
      console.error("Failed to delete note:", error);
    }
  };

  if (loading || isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">Loading note...</p>
      </div>
    );
  }

  if (!note) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">Note not found</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
        <div className="flex items-center gap-4 p-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push("/dashboard/resources/notes")}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <Input
            value={title}
            onChange={(e) => handleTitleChange(e.target.value)}
            className="flex-1 border-none bg-transparent text-xl font-semibold focus-visible:ring-0"
            placeholder="Untitled Note"
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={handleToggleFavorite}
            className={note.is_favorite ? "text-yellow-500" : ""}
          >
            <Star className={`h-4 w-4 ${note.is_favorite ? "fill-current" : ""}`} />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleDelete}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden p-6">
        <NoteEditor
          noteId={noteId}
          initialContent={note.content_json}
          onSave={handleSaveContent}
        />
      </div>
    </div>
  );
}
