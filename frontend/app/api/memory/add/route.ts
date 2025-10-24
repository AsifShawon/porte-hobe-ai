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

    const body = await request.json()
    const backendUrl = `${process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'}/api/memory/add`

    const upstream = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`
      },
      body: JSON.stringify(body)
    })

    if (!upstream.ok) {
      const text = await upstream.text()
      return new NextResponse(text, { status: upstream.status })
    }

    const json = await upstream.json()
    return NextResponse.json(json)
  } catch (e) {
    console.error('/api/memory/add proxy error', e)
    return new NextResponse(JSON.stringify({ error: 'Memory service unavailable' }), { status: 500 })
  }
}
