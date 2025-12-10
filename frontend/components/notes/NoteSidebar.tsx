"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronDown, ChevronRight, FolderPlus, PlusCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/components/auth-provider";

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

interface NoteSidebarProps {
  notes: NoteListItem[];
  folders: Folder[];
  onRefresh: () => Promise<void> | void;
  onCreateNote: () => Promise<void> | void;
}

interface FolderNode extends Folder {
  children: FolderNode[];
}

const ROOT_ID = "root";

function buildFolderTree(folders: Folder[]): FolderNode[] {
  const map = new Map<string, FolderNode>();
  const roots: FolderNode[] = [];

  folders.forEach((folder) => {
    map.set(folder.id, { ...folder, children: [] });
  });

  folders.forEach((folder) => {
    const node = map.get(folder.id)!;
    if (folder.parent_id && map.has(folder.parent_id)) {
      map.get(folder.parent_id)!.children.push(node);
    } else {
      roots.push(node);
    }
  });

  roots.sort((a, b) => a.name.localeCompare(b.name));
  map.forEach((node) => node.children.sort((a, b) => a.name.localeCompare(b.name)));

  return roots;
}

export function NoteSidebar({ notes, folders, onRefresh, onCreateNote }: NoteSidebarProps) {
  const { session } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");

  const folderTree = useMemo(() => buildFolderTree(folders), [folders]);

  const activeFolder = searchParams.get("folder") ?? ROOT_ID;

  const handleCreateFolder = async () => {
    if (!newFolderName.trim() || !session?.access_token) {
      return;
    }

    try {
      const response = await fetch("/api/notes/folders", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ name: newFolderName.trim() }),
      });

      if (!response.ok) {
        throw new Error("Failed to create folder");
      }

      setNewFolderName("");
      setIsCreatingFolder(false);
      await onRefresh();
    } catch (error) {
      console.error(error);
    }
  };

  const rootNotesCount = useMemo(() => notes.filter((note) => !note.folder_id).length, [notes]);
  const rootNotes = useMemo(() => notes.filter((note) => !note.folder_id), [notes]);

  const toggleFolder = (folderId: string) => {
    setExpanded((prev) => ({ ...prev, [folderId]: !prev[folderId] }));
  };

  const navigateToFolder = (folderId: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (!folderId) {
      params.delete("folder");
    } else {
      params.set("folder", folderId);
    }
    router.push(`/dashboard/resources/notes?${params.toString()}`);
  };

  const renderFolder = (node: FolderNode) => {
    const isOpen = expanded[node.id] ?? true;
    const folderNotes = notes.filter((note) => note.folder_id === node.id);

    return (
      <div key={node.id} className="space-y-1">
        <button
          type="button"
          onClick={() => {
            toggleFolder(node.id);
            navigateToFolder(node.id);
          }}
          className={`flex w-full items-center justify-between rounded px-2 py-1 text-sm transition hover:bg-muted ${
            activeFolder === node.id ? "bg-muted" : ""
          }`}
        >
          <span className="flex items-center gap-2">
            {isOpen ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            <span>{node.icon ?? "📁"}</span>
            <span>{node.name}</span>
          </span>
          <span className="text-xs text-muted-foreground">{folderNotes.length}</span>
        </button>
        {isOpen && (
          <div className="ml-7 space-y-1">
            {folderNotes.map((note) => (
              <Link
                key={note.id}
                href={`/dashboard/resources/notes/${note.id}`}
                className="block rounded px-2 py-1 text-sm text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
              >
                {note.title || "Untitled"}
              </Link>
            ))}
            {node.children.map((child) => (
              <div key={child.id} className="mt-1">
                {renderFolder(child)}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <aside className="hidden w-[260px] shrink-0 border-r bg-muted/30 p-4 lg:block">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Notebooks
        </h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCreatingFolder(true)}
          title="New folder"
        >
          <FolderPlus className="h-4 w-4" />
        </Button>
      </div>
      <div className="mt-4 space-y-1">
        <button
          type="button"
          onClick={() => navigateToFolder(null)}
          className={`flex w-full items-center gap-2 rounded px-2 py-1 text-sm transition hover:bg-muted ${
            activeFolder === ROOT_ID ? "bg-muted" : ""
          }`}
        >
          <ChevronRight className="h-4 w-4 opacity-0" />
          <span>All notes</span>
          <span className="ml-auto text-xs text-muted-foreground">{rootNotesCount}</span>
        </button>
        
        {/* Display root notes (notes without folders) */}
        {rootNotes.map((note) => (
          <Link
            key={note.id}
            href={`/dashboard/resources/notes/${note.id}`}
            className="block rounded px-2 py-1 ml-6 text-sm text-muted-foreground transition hover:bg-accent hover:text-accent-foreground"
          >
            {note.title || "Untitled"}
          </Link>
        ))}
        
        {folderTree.map((node) => renderFolder(node))}
      </div>

      <Separator className="my-4" />

      <Button size="sm" className="w-full justify-start gap-2" onClick={() => onCreateNote()}>
        <PlusCircle className="h-4 w-4" />
        New note
      </Button>

      {isCreatingFolder && (
        <div className="mt-4 space-y-2 rounded border border-dashed border-primary/40 p-3">
          <Input
            autoFocus
            placeholder="Folder name"
            value={newFolderName}
            onChange={(event) => setNewFolderName(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleCreateFolder();
              }
              if (event.key === "Escape") {
                setIsCreatingFolder(false);
                setNewFolderName("");
              }
            }}
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={handleCreateFolder}>
              Save
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setIsCreatingFolder(false);
                setNewFolderName("");
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}
    </aside>
  );
}
