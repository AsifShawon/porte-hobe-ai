import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServerClient } from '@/lib/supabase/server'

export async function POST(request: NextRequest) {
  try {
    // Verify authentication
    const supabase = await createSupabaseServerClient()
    const { data: { session } } = await supabase.auth.getSession()

    if (!session) {
      return new NextResponse(
        JSON.stringify({ error: 'Unauthorized' }), 
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    const { message, history } = await request.json()

    const backendUrl = `${process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'}/api/chat`

    const upstream = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`
      },
      body: JSON.stringify({ message, history })
    })

    if (!upstream.ok || !upstream.body) {
      throw new Error(`Backend error: ${upstream.status}`)
    }

    return new NextResponse(upstream.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      }
    })
  } catch (e) {
    console.error('Chat proxy error', e)
    return new NextResponse(JSON.stringify({ error: 'Chat service unavailable' }), { status: 500 })
  }
}
