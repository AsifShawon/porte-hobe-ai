"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { useRouter } from "next/navigation";
import { NoteSidebar } from "@/components/notes/NoteSidebar";
import { Button } from "@/components/ui/button";
import { PlusCircle, StickyNote } from "lucide-react";

interface Folder {
  id: string;
  parent_id: string | null;
  name: string;
  color?: string | null;
  icon?: string | null;
}

interface NoteListItem {
  id: string;
  title: string;
  folder_id: string | null;
  updated_at?: string;
  is_favorite?: boolean;
}

export default function NotesPage() {
  const { user, session, loading } = useAuth();
  const router = useRouter();
  const [notes, setNotes] = useState<NoteListItem[]>([]);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user && session) {
      fetchNotesAndFolders();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, session]);

  const fetchNotesAndFolders = async () => {
    if (!session?.access_token) return;
    
    setIsLoading(true);
    try {
      const headers = {
        'Authorization': `Bearer ${session.access_token}`,
      };

      const [notesRes, foldersRes] = await Promise.all([
        fetch("/api/notes", { headers }),
        fetch("/api/notes/folders", { headers }),
      ]);

      if (notesRes.ok) {
        const notesData = await notesRes.json();
        setNotes(notesData.notes || []);
      }

      if (foldersRes.ok) {
        const foldersData = await foldersRes.json();
        setFolders(foldersData.folders || []);
      }
    } catch (error) {
      console.error("Failed to fetch notes:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateNote = async () => {
    if (!session?.access_token) {
      console.error('No session token available');
      return;
    }

    try {
      const response = await fetch("/api/notes", {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          title: "Untitled Note",
          content_json: { type: "doc", content: [] },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create note");
      }

      const { note } = await response.json();
      router.push(`/dashboard/resources/notes/${note.id}`);
    } catch (error) {
      console.error("Failed to create note:", error);
    }
  };

  if (loading || isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">Loading notes...</p>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      <NoteSidebar
        notes={notes}
        folders={folders}
        onRefresh={fetchNotesAndFolders}
        onCreateNote={handleCreateNote}
      />
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        {notes.length === 0 && folders.length === 0 ? (
          <div className="max-w-md space-y-4">
            <div className="rounded-full bg-muted p-6 w-24 h-24 mx-auto flex items-center justify-center">
              <StickyNote className="h-12 w-12 text-muted-foreground" />
            </div>
            <h2 className="text-2xl font-semibold">Your Notes</h2>
            <p className="text-muted-foreground">
              Create notes to capture your learning journey. Organize them with folders
              and save content directly from chat.
            </p>
            <Button onClick={handleCreateNote} className="gap-2">
              <PlusCircle className="h-4 w-4" />
              Create your first note
            </Button>
          </div>
        ) : (
          <div className="max-w-md space-y-4">
            <div className="rounded-full bg-muted p-6 w-24 h-24 mx-auto flex items-center justify-center">
              <StickyNote className="h-12 w-12 text-muted-foreground" />
            </div>
            <h2 className="text-2xl font-semibold">Select a Note</h2>
            <p className="text-muted-foreground">
              Choose a note from the sidebar to view and edit it, or create a new one.
            </p>
            <Button onClick={handleCreateNote} className="gap-2">
              <PlusCircle className="h-4 w-4" />
              Create new note
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
