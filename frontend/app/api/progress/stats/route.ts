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

    const backendUrl = `${process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'}/api/progress/stats`

    const upstream = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`
      }
    })

    if (!upstream.ok) {
      const errorText = await upstream.text()
      throw new Error(`Backend error: ${upstream.status} - ${errorText}`)
    }

    const data = await upstream.json()
    return NextResponse.json(data)

  } catch (e) {
    console.error('Progress stats proxy error', e)
    const errorMessage = e instanceof Error ? e.message : 'Failed to fetch progress stats'
    return new NextResponse(
      JSON.stringify({ error: errorMessage }), 
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
}
