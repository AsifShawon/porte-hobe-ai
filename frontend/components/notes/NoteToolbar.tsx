"use client";

import { Editor } from "@tiptap/react";
import {
  Bold,
  Code,
  Heading1,
  Heading2,
  Heading3,
  Italic,
  Link as LinkIcon,
  List,
  ListOrdered,
  Quote,
  Redo,
  Strikethrough,
  Undo,
} from "lucide-react";

import { Button } from "@/components/ui/button";

interface NoteToolbarProps {
  editor: Editor | null;
}

const TOOLBAR_BUTTON_CLASS = "h-4 w-4";

export function NoteToolbar({ editor }: NoteToolbarProps) {
  if (!editor) {
    return null;
  }

  const toggleLink = () => {
    const previousUrl = editor.getAttributes("link").href as string | undefined;
    const url = window.prompt("Enter URL", previousUrl ?? "https://");

    if (url === null) {
      return;
    }

    if (!url) {
      editor.chain().focus().unsetLink().run();
      return;
    }

    editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
  };

  return (
    <div className="flex flex-wrap items-center gap-1 border-b bg-background/95 p-2 text-sm shadow-sm">
      <Button
        variant={editor.isActive("bold") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleBold().run()}
      >
        <Bold className={TOOLBAR_BUTTON_CLASS} />
      </Button>
      <Button
        variant={editor.isActive("italic") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleItalic().run()}
      >
        <Italic className={TOOLBAR_BUTTON_CLASS} />
      </Button>
      <Button
        variant={editor.isActive("strike") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleStrike().run()}
      >
        <Strikethrough className={TOOLBAR_BUTTON_CLASS} />
      </Button>
      <Button
        variant={editor.isActive("code") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleCode().run()}
      >
        <Code className={TOOLBAR_BUTTON_CLASS} />
      </Button>

      <span className="mx-2 h-5 w-px bg-border" />

      <Button
        variant={editor.isActive("heading", { level: 1 }) ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
      >
        <Heading1 className={TOOLBAR_BUTTON_CLASS} />
      </Button>
      <Button
        variant={editor.isActive("heading", { level: 2 }) ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
      >
        <Heading2 className={TOOLBAR_BUTTON_CLASS} />
      </Button>
      <Button
        variant={editor.isActive("heading", { level: 3 }) ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
      >
        <Heading3 className={TOOLBAR_BUTTON_CLASS} />
      </Button>

      <span className="mx-2 h-5 w-px bg-border" />

      <Button
        variant={editor.isActive("bulletList") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleBulletList().run()}
      >
        <List className={TOOLBAR_BUTTON_CLASS} />
      </Button>
      <Button
        variant={editor.isActive("orderedList") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
      >
        <ListOrdered className={TOOLBAR_BUTTON_CLASS} />
      </Button>
      <Button
        variant={editor.isActive("blockquote") ? "secondary" : "ghost"}
        size="icon"
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
      >
        <Quote className={TOOLBAR_BUTTON_CLASS} />
      </Button>
      <Button
        variant={editor.isActive("link") ? "secondary" : "ghost"}
        size="icon"
        onClick={toggleLink}
      >
        <LinkIcon className={TOOLBAR_BUTTON_CLASS} />
      </Button>

      <span className="mx-2 h-5 w-px bg-border" />

      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().undo().run()}
        disabled={!editor.can().undo()}
      >
        <Undo className={TOOLBAR_BUTTON_CLASS} />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => editor.chain().focus().redo().run()}
        disabled={!editor.can().redo()}
      >
        <Redo className={TOOLBAR_BUTTON_CLASS} />
      </Button>
    </div>
  );
}
