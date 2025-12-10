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
    
    const backendUrl = `${process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000'}/api/quizzes/generate`

    console.log('Proxying quiz generation request to:', backendUrl)
    console.log('Request body:', JSON.stringify(body, null, 2))

    const upstream = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${session.access_token}`
      },
      body: JSON.stringify(body)
    })

    if (!upstream.ok) {
      const errorText = await upstream.text()
      console.error('Backend quiz generation error:', upstream.status, errorText)
      return new NextResponse(
        JSON.stringify({ 
          error: 'Quiz generation failed', 
          detail: errorText,
          status: upstream.status 
        }), 
        { status: upstream.status, headers: { 'Content-Type': 'application/json' } }
      )
    }

    const data = await upstream.json()
    console.log('Quiz generated successfully:', data.quiz?.title || 'Unknown title')
    return NextResponse.json(data)

  } catch (e) {
    console.error('Quiz generation proxy error:', e)
    return new NextResponse(
      JSON.stringify({ 
        error: 'Failed to generate quiz', 
        detail: e instanceof Error ? e.message : 'Unknown error'
      }), 
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
}
