-- ---------------------------------------------------------------------------
-- Notes System Schema
-- ---------------------------------------------------------------------------
-- Run this script in the Supabase SQL editor (or via psql) to provision the
-- database objects needed for the Notion-like notes experience. The script is
-- idempotent where possible and assumes the "uuid-ossp" extension is available
-- (Supabase enables it by default).
-- ---------------------------------------------------------------------------

begin;

-- Ensure uuid extension exists (safe to run multiple times)
create extension if not exists "uuid-ossp";

-- ===========================================================================
-- note_folders: hierarchical folders for organizing notes
-- ===========================================================================
create table if not exists public.note_folders (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references auth.users (id) on delete cascade,
    parent_id uuid references public.note_folders (id) on delete cascade,
    name text not null,
    color text,
    icon text,
    position integer default 0,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create index if not exists note_folders_user_id_idx on public.note_folders (user_id);
create index if not exists note_folders_parent_id_idx on public.note_folders (parent_id);
create index if not exists note_folders_position_idx on public.note_folders (user_id, parent_id, position);

alter table public.note_folders enable row level security;
alter table public.note_folders force row level security;

drop policy if exists "Users can view their own folders" on public.note_folders;
create policy "Users can view their own folders"
    on public.note_folders
    for select
    using (auth.uid() = user_id);

drop policy if exists "Users can create their own folders" on public.note_folders;
create policy "Users can create their own folders"
    on public.note_folders
    for insert
    with check (auth.uid() = user_id);

drop policy if exists "Users can update their own folders" on public.note_folders;
create policy "Users can update their own folders"
    on public.note_folders
    for update
    using (auth.uid() = user_id);

drop policy if exists "Users can delete their own folders" on public.note_folders;
create policy "Users can delete their own folders"
    on public.note_folders
    for delete
    using (auth.uid() = user_id);

-- ===========================================================================
-- learning_notes: rich documents stored as Tiptap JSON + derived representations
-- ===========================================================================
create table if not exists public.learning_notes (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references auth.users (id) on delete cascade,
    folder_id uuid references public.note_folders (id) on delete set null,
    title text not null default 'Untitled Note',
    content_json jsonb not null default '{"type":"doc","content":[]}'::jsonb,
    content_html text,
    content_text text default '',
    is_favorite boolean default false,
    is_archived boolean default false,
    tags text[] default '{}',
    position integer default 0,
    metadata jsonb default '{}'::jsonb,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create index if not exists learning_notes_user_id_idx on public.learning_notes (user_id);
create index if not exists learning_notes_folder_id_idx on public.learning_notes (folder_id);
create index if not exists learning_notes_position_idx on public.learning_notes (user_id, folder_id, position);
create index if not exists learning_notes_created_at_idx on public.learning_notes (created_at desc);
create index if not exists learning_notes_updated_at_idx on public.learning_notes (updated_at desc);
create index if not exists learning_notes_tags_idx on public.learning_notes using gin (tags);
create index if not exists learning_notes_content_text_idx on public.learning_notes using gin (to_tsvector('english'::regconfig, coalesce(content_text, '')));

alter table public.learning_notes enable row level security;
alter table public.learning_notes force row level security;

drop policy if exists "Users can view their own learning_notes" on public.learning_notes;
create policy "Users can view their own learning_notes"
    on public.learning_notes
    for select
    using (auth.uid() = user_id);

drop policy if exists "Users can create their own learning_notes" on public.learning_notes;
create policy "Users can create their own learning_notes"
    on public.learning_notes
    for insert
    with check (auth.uid() = user_id);

drop policy if exists "Users can update their own learning_notes" on public.learning_notes;
create policy "Users can update their own learning_notes"
    on public.learning_notes
    for update
    using (auth.uid() = user_id);

drop policy if exists "Users can delete their own learning_notes" on public.learning_notes;
create policy "Users can delete their own learning_notes"
    on public.learning_notes
    for delete
    using (auth.uid() = user_id);

-- ===========================================================================
-- note_chat_links: audit log of chat messages injected into notes
-- ===========================================================================
create table if not exists public.note_chat_links (
    id uuid primary key default uuid_generate_v4(),
    note_id uuid not null references public.learning_notes (id) on delete cascade,
    chat_message_id uuid,
    user_id uuid not null references auth.users (id) on delete cascade,
    content text not null,
    injected_at timestamptz default now(),
    metadata jsonb default '{}'::jsonb
);

create index if not exists note_chat_links_note_id_idx on public.note_chat_links (note_id);
create index if not exists note_chat_links_user_id_idx on public.note_chat_links (user_id);
create index if not exists note_chat_links_injected_at_idx on public.note_chat_links (injected_at desc);

alter table public.note_chat_links enable row level security;
alter table public.note_chat_links force row level security;

drop policy if exists "Users can view their own note chat links" on public.note_chat_links;
create policy "Users can view their own note chat links"
    on public.note_chat_links
    for select
    using (auth.uid() = user_id);

drop policy if exists "Users can create their own note chat links" on public.note_chat_links;
create policy "Users can create their own note chat links"
    on public.note_chat_links
    for insert
    with check (auth.uid() = user_id);

drop policy if exists "Users can delete their own note chat links" on public.note_chat_links;
create policy "Users can delete their own note chat links"
    on public.note_chat_links
    for delete
    using (auth.uid() = user_id);

-- ===========================================================================
-- chat_history enhancements: track linkage to notes
-- ===========================================================================
alter table public.chat_history
    add column if not exists saved_to_note boolean default false;

alter table public.chat_history
    add column if not exists note_id uuid references public.learning_notes (id) on delete set null;

create index if not exists chat_history_note_id_idx on public.chat_history (note_id);
create index if not exists chat_history_saved_idx on public.chat_history (saved_to_note);

commit;

-- ---------------------------------------------------------------------------
-- Post-run checklist
--   1. Verify RLS policies via Supabase Auth → Policies UI.
--   2. Grant "authenticated" role usage on the new tables if required.
--   3. Deploy edge functions or backend changes that rely on these tables.
-- ---------------------------------------------------------------------------
