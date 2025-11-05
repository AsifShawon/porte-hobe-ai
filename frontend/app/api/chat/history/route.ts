import { NextRequest, NextResponse } from 'next/server'
import { createSupabaseServerClient } from '@/lib/supabase/server'

export async function GET(request: NextRequest) {
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

    const { searchParams } = new URL(request.url)
    const limit = searchParams.get('limit') || '50'
    const conversation_id = searchParams.get('conversation_id')

    let backendUrl = `${process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'}/api/chat/history?limit=${limit}`
    if (conversation_id) {
      backendUrl += `&conversation_id=${conversation_id}`
    }

    const upstream = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`
      }
    })

    if (!upstream.ok) {
      throw new Error(`Backend error: ${upstream.status}`)
    }

    const data = await upstream.json()
    return NextResponse.json(data)

  } catch (e) {
    console.error('Chat history proxy error', e)
    return new NextResponse(
      JSON.stringify({ error: 'Failed to fetch chat history' }), 
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
}
