import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { message, history } = await request.json()

    const backendUrl = `${process.env.FASTAPI_URL || 'http://localhost:8000'}/api/chat`

    const upstream = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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
