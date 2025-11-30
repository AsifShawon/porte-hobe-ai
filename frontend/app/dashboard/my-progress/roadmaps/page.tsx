"use client"

import React, { useEffect, useState, useCallback } from 'react'
import { createSupabaseBrowserClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/auth-provider'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, Map, ArrowRight } from 'lucide-react'
import Link from 'next/link'

interface RoadmapRow {
  id: string
  user_id: string
  title: string | null
  status: string | null
  created_at: string | null
  updated_at?: string | null
  progress_percentage?: number | null
}

export default function RoadmapsListingPage() {
  const { user, loading } = useAuth()
  const [roadmaps, setRoadmaps] = useState<RoadmapRow[]>([])
  const [fetching, setFetching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchRoadmaps = useCallback(async () => {
    if (!user) return
    try {
      setFetching(true)
      setError(null)
      const supabase = createSupabaseBrowserClient()
      const { data, error } = await supabase
        .from('learning_roadmaps')
        .select('id,user_id,title,status,created_at,updated_at,progress_percentage')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })

      if (error) throw error
      setRoadmaps(data || [])
    } catch (e) {
      const msg = (e instanceof Error) ? e.message : 'Failed to load roadmaps'
      setError(msg)
    } finally {
      setFetching(false)
    }
  }, [user])

  useEffect(() => {
    if (!loading && user) {
      void fetchRoadmaps()
    }
  }, [user, loading, fetchRoadmaps])


  if (!user && !loading) {
    return <div className="p-6 text-center text-sm">Please log in to view your roadmaps.</div>
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b flex items-center gap-2 bg-background/50 backdrop-blur">
        <Map className="h-5 w-5 text-primary" />
        <h1 className="text-lg font-semibold">My Learning Roadmaps</h1>
        <div className="ml-auto flex gap-2">
          <Button variant="outline" size="sm" onClick={() => fetchRoadmaps()} disabled={fetching}>
            {fetching ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Refresh'}
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {error && (
          <div className="text-sm text-red-600 dark:text-red-400 border border-red-300 dark:border-red-700 rounded p-3 bg-red-50/50 dark:bg-red-900/20">
            {error}
          </div>
        )}

        {fetching && roadmaps.length === 0 && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading roadmaps...
          </div>
        )}

        {!fetching && roadmaps.length === 0 && !error && (
          <Card className="p-6 text-center">
            <p className="text-sm mb-2">You have no learning roadmaps yet.</p>
            <p className="text-xs text-muted-foreground mb-4">Start a chat with the AI Tutor and describe what you want to learn to generate your first roadmap.</p>
            <Button asChild size="sm">
              <Link href="/dashboard/chat">Go to Chat</Link>
            </Button>
          </Card>
        )}

        {roadmaps.map(r => (
          <Card key={r.id} className="p-4 flex flex-col gap-3">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <h2 className="text-sm font-semibold">{r.title || 'Untitled Roadmap'}</h2>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{r.status || 'draft'}</span>
                  <span>•</span>
                  <span>Created {r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}</span>
                </div>
              </div>
              <Button asChild size="sm" variant="secondary">
                <Link href={`/dashboard/progress?roadmap=${r.id}`} className="flex items-center gap-1">
                  View <ArrowRight className="h-3 w-3" />
                </Link>
              </Button>
            </div>
            {typeof r.progress_percentage === 'number' && (
              <div className="w-full h-2 rounded bg-muted overflow-hidden">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${Math.min(100, Math.max(0, r.progress_percentage))}%` }}
                />
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  )
}
