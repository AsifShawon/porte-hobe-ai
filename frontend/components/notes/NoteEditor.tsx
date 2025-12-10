"use client";

import { useEffect, useMemo } from "react";
import { useDebouncedCallback } from "use-debounce";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Link from "@tiptap/extension-link";
import CodeBlockLowlight from "@tiptap/extension-code-block-lowlight";
import Mathematics from "@tiptap/extension-mathematics";
import { createLowlight } from "lowlight";

import "katex/dist/katex.min.css";

import { NoteToolbar } from "@/components/notes/NoteToolbar";

interface NoteEditorProps {
  noteId?: string;
  initialContent: Record<string, unknown>;
  readOnly?: boolean;
  onSave: (content: Record<string, unknown>) => Promise<void>;
}

const AUTOSAVE_DELAY_MS = 800;

export function NoteEditor({ initialContent, readOnly, onSave }: NoteEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: false, // We provide our own extension with highlighting
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: "text-primary underline decoration-dotted",
          target: "_blank",
          rel: "noopener noreferrer",
        },
      }),
      CodeBlockLowlight.configure({ lowlight: createLowlight() }),
      Mathematics.configure({
        katexOptions: {
          output: "html",
        },
      }),
    ],
    content: initialContent,
    editable: !readOnly,
    autofocus: true,
    onUpdate: ({ editor }) => debouncedSave(editor.getJSON() as Record<string, unknown>),
  });

  useEffect(() => {
    if (editor && editor.isEmpty && initialContent) {
      editor.commands.setContent(initialContent);
    }
  }, [editor, initialContent]);

  const debouncedSave = useDebouncedCallback(async (content: Record<string, unknown>) => {
    if (readOnly) return;
    try {
      await onSave(content);
    } catch (error) {
      console.error("Failed to auto-save note", error);
    }
  }, AUTOSAVE_DELAY_MS);

  useEffect(() => {
    return () => {
      debouncedSave.flush();
    };
  }, [debouncedSave]);

  const editorClassName = useMemo(
    () =>
      [
        "prose",
        "prose-sm",
        "dark:prose-invert",
        "max-w-none",
        "focus:outline-none",
        "min-h-[60vh]",
      ].join(" "),
    []
  );

  if (!editor) {
    return (
      <div className="flex h-full items-center justify-center border border-dashed border-muted-foreground/40 p-6 text-sm text-muted-foreground">
        Loading editor...
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {!readOnly && <NoteToolbar editor={editor} />}
      <div className="flex-1 overflow-y-auto">
        <EditorContent editor={editor} className={editorClassName} />
      </div>
    </div>
  );
}
