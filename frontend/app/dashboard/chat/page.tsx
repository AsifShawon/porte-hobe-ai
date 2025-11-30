"use client"

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useAuth } from '@/components/auth-provider'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Send, Bot, User, Loader2, Sparkles, History, Map, FileQuestion, CheckCircle2 } from "lucide-react"
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import 'katex/dist/katex.min.css'
import { useRoadmaps, useRoadmap } from '@/hooks/useRoadmap'
import { useQuizzes } from '@/hooks/useQuiz'
import type { CreateRoadmapRequest } from '@/types/roadmap'
import type { GenerateQuizRequest } from '@/types/quiz'
import { createSupabaseBrowserClient } from '@/lib/supabase/client'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  type?: 'thinking' | 'final_answer' | 'complete'
  thinking_content?: string
  request_id?: string
  roadmap_trigger?: RoadmapTrigger
  quiz_offer?: QuizOffer
}

interface RoadmapTrigger {
  topic: string | null
  domain: string
  user_level: string
  query: string
  conversation_id?: string
  user_id?: string
}

interface QuizOffer {
  topic: string | null
  domain: string
  trigger_reason: string
  subtopics?: string[]
}

// Client-side only timestamp component to avoid hydration mismatch
function TimeDisplay({ timestamp }: { timestamp: Date }) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  return <>{timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</>
}

export default function ChatPage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login')
    }
  }, [user, loading, router])

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hello! I'm your autonomous AI tutor. I'm here to help you with programming basics and mathematics. What would you like to learn today?",
      role: 'assistant',
      timestamp: new Date(),
      type: 'final_answer'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentThinkingMessage, setCurrentThinkingMessage] = useState<Message | null>(null)
  const [openThinking, setOpenThinking] = useState<{[key: string]: boolean}>({})
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const autoStartedRef = useRef(false)

  // Roadmap and Quiz state
  const [pendingRoadmapTrigger, setPendingRoadmapTrigger] = useState<RoadmapTrigger | null>(null)
  const [pendingQuizOffer, setPendingQuizOffer] = useState<QuizOffer | null>(null)
  const { createRoadmap } = useRoadmaps(undefined, { enabled: false })
  const { generateQuiz } = useQuizzes(undefined, { enabled: false })
  // Milestone context from query params
  const milestoneRoadmapId = searchParams.get('roadmap_id') || searchParams.get('roadmap')
  const milestonePhaseId = searchParams.get('phase_id') || searchParams.get('phase')
  const milestoneId = searchParams.get('milestone_id') || searchParams.get('milestone')
  const milestoneTitle = searchParams.get('milestone_title') || undefined
  const { completeMilestone, startMilestone, refetch: refetchRoadmap } = useRoadmap(milestoneRoadmapId)
  const [isCompleting, setIsCompleting] = useState(false)
  const [showMilestoneBanner, setShowMilestoneBanner] = useState<boolean>(
    Boolean(milestoneRoadmapId && milestonePhaseId && milestoneId)
  )

  // Check for roadmap/conversation linking from URL params
  useEffect(() => {
    const conversation = searchParams.get('conversation_id')
    if (conversation && !conversationId) {
      setConversationId(conversation)
    }
  }, [searchParams, conversationId])

  // Check for continued conversation from history (new unified tables)
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const conv = searchParams.get('conversation_id') || conversationId
        if (conv) {
          const supabase = createSupabaseBrowserClient()

          // Find session by legacy conversation_id
          const { data: sessionRows, error: sessionErr } = await supabase
            .from('chat_sessions')
            .select('id')
            .eq('conversation_id', conv)
            .limit(1)

          if (!sessionErr && sessionRows && sessionRows.length > 0) {
            const sessionId = sessionRows[0].id
            const { data: msgs, error: msgsErr } = await supabase
              .from('chat_messages')
              .select('id, role, content, thinking_content, metadata, created_at, message_type')
              .eq('session_id', sessionId)
              .order('created_at', { ascending: true })

            if (!msgsErr && Array.isArray(msgs)) {
              type DbMsg = { id: string; role: string; content: string; thinking_content?: string | null; metadata?: Record<string, unknown>; created_at?: string; message_type?: string }
              // Filter out system messages (roadmap_trigger, quiz_trigger, etc.)
              const loaded: Message[] = (msgs as DbMsg[])
                .filter(m => m.role !== 'system')
                .map(m => ({
                  id: m.id,
                  content: m.content || '',
                  role: m.role === 'assistant' ? 'assistant' : 'user',
                  timestamp: new Date(m.created_at || Date.now()),
                  type: m.role === 'assistant' ? 'final_answer' : undefined,
                  thinking_content: m.thinking_content || undefined
                }))
              setConversationId(conv)
              setMessages(prev => [prev[0], ...loaded])
              return
            }
          }
        }

        // Legacy fallback to old chat_history table if exists (in case migration not yet applied)
        try {
          if (conv) {
            const supabase = createSupabaseBrowserClient()
            const { data: legacyData, error: legacyErr } = await supabase
              .from('chat_history')
              .select('*')
              .eq('conversation_id', conv)
              .order('created_at', { ascending: true })
            if (!legacyErr && Array.isArray(legacyData) && legacyData.length) {
              type LegacyRow = { id?: string; message?: string; content?: string; role?: string; created_at?: string; thinking_content?: string }
              // Filter out system messages (roadmap_trigger, quiz_trigger, etc.)
              const loadedLegacy: Message[] = (legacyData as LegacyRow[])
                .filter(r => r.role !== 'system')
                .map(r => ({
                  id: r.id || `${r.created_at}`,
                  content: r.message || r.content || '',
                  role: r.role === 'assistant' ? 'assistant' : 'user',
                  timestamp: new Date(r.created_at || Date.now()),
                  type: r.role === 'assistant' ? 'final_answer' : undefined,
                  thinking_content: r.thinking_content || undefined
                }))
              setConversationId(conv)
              setMessages(prev => [prev[0], ...loadedLegacy])
              return
            }
          }
        } catch {
          // Ignore if legacy table missing
        }

        // Fallback: sessionStorage
        if (typeof window !== 'undefined') {
          const continueData = sessionStorage.getItem('continueChat')
          if (continueData) {
            type HistoryItem = { id?: string; message?: string; content?: string; role?: string; created_at?: string; thinking_content?: string }
            const parsed = JSON.parse(continueData) as { conversationId?: string; messages?: HistoryItem[] }
            const { conversationId: convId, messages: historyMessages } = parsed
            setConversationId(convId ?? null)
            const loadedMessages: Message[] = Array.isArray(historyMessages)
              ? historyMessages.map((msg: HistoryItem) => ({
                  id: msg.id || Date.now().toString(),
                  content: msg.message || msg.content || '',
                  role: msg.role === 'assistant' ? 'assistant' : 'user',
                  timestamp: new Date(msg.created_at || Date.now()),
                  type: (msg.role === 'assistant') ? 'final_answer' : undefined,
                  thinking_content: msg.thinking_content || undefined
                }))
              : []
            setMessages(prev => [prev[0], ...loadedMessages])
            sessionStorage.removeItem('continueChat')
          }
        }
      } catch (error) {
        console.error('Failed to load conversation history:', error)
      }
    }
    loadHistory()
  }, [searchParams, conversationId])

  const toggleThinking = (messageId: string) => {
    setOpenThinking(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }))
  }
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'auto', block: 'end' })
    }
  }

  useEffect(() => {
    // Use requestAnimationFrame for smoother scrolling
    requestAnimationFrame(() => {
      scrollToBottom()
    })
  }, [messages, currentThinkingMessage])

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input.trim(),
      role: 'user',
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    const thinkingId = 'thinking-' + Date.now()
    const initialThinking: Message = {
      id: thinkingId,
      content: '',
      role: 'assistant',
      timestamp: new Date(),
      type: 'thinking',
      thinking_content: ''
    }
    setCurrentThinkingMessage(initialThinking)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          history: messages.map(m => ({ role: m.role, content: m.content })),
          conversation_id: conversationId,  // Pass conversation_id for linking
          metadata: {
            roadmap_id: milestoneRoadmapId || undefined,
            topic_id: undefined
          }
        }),
      })

      if (!response.ok || !response.body) throw new Error('Failed to connect')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      let thinkingBuffer = ''
      let answerBuffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split(/\n/).filter(l => l.startsWith('data: '))
        for (const line of lines) {
          const jsonStr = line.slice(6).trim()
          if (!jsonStr) continue
          try {
            const evt = JSON.parse(jsonStr)
            
            // Capture session_id and conversation_id from any event
            if (evt.session_id && !sessionId) {
              setSessionId(evt.session_id)
            }
            if (evt.conversation_id && !conversationId) {
              setConversationId(evt.conversation_id)
            }
            
            switch (evt.type) {
              case 'thinking_start': {
                break
              }
              case 'thinking_delta': {
                thinkingBuffer += evt.delta
                setCurrentThinkingMessage(prev => prev ? { ...prev, thinking_content: thinkingBuffer } : prev)
                break
              }
              case 'thinking_complete': {
                thinkingBuffer = evt.thinking_content || thinkingBuffer
                setCurrentThinkingMessage(prev => prev ? { ...prev, thinking_content: thinkingBuffer } : prev)
                break
              }
              case 'answer_start': {
                // keep thinking visible until some answer tokens come
                break
              }
              case 'answer_delta': {
                answerBuffer += evt.delta
                // Strip any accidental ANSWER tags
                const cleaned = answerBuffer.replace(/<\/?ANSWER>/g, '')
                setCurrentThinkingMessage(prev => prev ? { ...prev, content: cleaned } : prev)
                break
              }
              case 'answer_complete': {
                answerBuffer = (evt.response || answerBuffer).replace(/<\/?ANSWER>/g, '')
                const finalMsg: Message = {
                  id: Date.now().toString(),
                  content: answerBuffer,
                  role: 'assistant',
                  timestamp: new Date(),
                  type: 'complete',
                  thinking_content: thinkingBuffer
                }
                setCurrentThinkingMessage(null)
                setMessages(prev => [...prev, finalMsg]);
                
                // Save both to chat_history and memory
                (async () => {
                  try {
                    // Save assistant message to chat_history
                    await fetch('/api/chat/save-message', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        role: 'assistant',
                        message: answerBuffer
                      })
                    })
                    
                    // Persist memory
                    const payload = {
                      query: userMessage.content,
                      response: answerBuffer,
                      summary: (thinkingBuffer || answerBuffer || '').slice(0, 400),
                      request_id: evt.request_id || undefined
                    }
                    await fetch('/api/memory/add', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(payload)
                    })
                  } catch (err) {
                    console.warn('Failed to persist messages', err)
                  }
                })()
                break
              }
              case 'roadmap_trigger': {
                // Store roadmap trigger data to show prompt
                setPendingRoadmapTrigger({
                  topic: evt.topic,
                  domain: evt.domain,
                  user_level: evt.user_level,
                  query: evt.query,
                  conversation_id: evt.conversation_id,
                  user_id: evt.user_id
                })
                // Update conversation_id state if provided
                if (evt.conversation_id && !conversationId) {
                  setConversationId(evt.conversation_id)
                }
                break
              }
              case 'quiz_offer': {
                // Store quiz offer data to show prompt
                setPendingQuizOffer({
                  topic: evt.topic,
                  domain: evt.domain,
                  trigger_reason: evt.trigger_reason,
                  subtopics: evt.subtopics
                })
                break
              }
              case 'error': {
                setCurrentThinkingMessage(null)
                const errMsg: Message = {
                  id: Date.now().toString(),
                  content: evt.response || 'Error occurred.',
                  role: 'assistant',
                  timestamp: new Date(),
                  type: 'final_answer'
                }
                setMessages(prev => [...prev, errMsg]);
                break
              }
            }
          } catch (e) {
            console.warn('Bad SSE line', line, e)
          }
        }
      }

    } catch (e) {
      console.error('Streaming failed', e)
      setCurrentThinkingMessage(null)
    } finally {
      setIsLoading(false)
    }
  }, [input, isLoading, messages, conversationId, milestoneRoadmapId, sessionId])

  // Auto-start teaching prompt from roadmap navigation (placed after sendMessage definition)
  useEffect(() => {
    const autoQuery = searchParams.get('auto_query') || searchParams.get('contextual_prompt')
    const autoStart = searchParams.get('auto_start')
    
    if (autoQuery && autoStart === 'true' && !autoStartedRef.current && !isLoading) {
      autoStartedRef.current = true
      setInput(autoQuery)
      // Auto-send after a short delay
      setTimeout(() => {
        sendMessage()
      }, 500)
    } else if (autoQuery && !autoStartedRef.current) {
      // Just pre-fill the input without auto-sending
      setInput(autoQuery)
      autoStartedRef.current = true
    }
  }, [searchParams, isLoading, sendMessage])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleGenerateRoadmap = async () => {
    if (!pendingRoadmapTrigger) return

    try {
      const request: CreateRoadmapRequest = {
        user_goal: pendingRoadmapTrigger.query,
        domain: (pendingRoadmapTrigger.domain === 'mathematics' ? 'math' : pendingRoadmapTrigger.domain) as 'programming' | 'math' | 'general',
        conversation_history: messages.map(m => ({
          role: m.role,
          content: m.content
        })),
        user_context: {
          user_level: pendingRoadmapTrigger.user_level,
          focus_areas: pendingRoadmapTrigger.topic ? [pendingRoadmapTrigger.topic] : []
        },
        conversation_id: pendingRoadmapTrigger.conversation_id || conversationId || undefined,
        chat_session_id: conversationId || undefined
      }

      const roadmap = await createRoadmap(request)

      if (roadmap) {
        // Add success message with "View Roadmap" button
        const successMsg: Message = {
          id: Date.now().toString(),
          content: `✅ I've created a personalized learning roadmap for **"${roadmap.title}"**!

[📚 View Roadmap](/dashboard/progress?roadmap=${roadmap.id})

You can continue our conversation here, and return to the roadmap anytime to track your progress.`,
          role: 'assistant',
          timestamp: new Date(),
          type: 'final_answer'
        }
        setMessages(prev => [...prev, successMsg])
        setPendingRoadmapTrigger(null)
      }
    } catch (error) {
      console.error('Failed to generate roadmap:', error)
    }
  }

  const handleGenerateQuiz = async () => {
    if (!pendingQuizOffer) return

    try {
      const request: GenerateQuizRequest = {
        topics: pendingQuizOffer.subtopics || (pendingQuizOffer.topic ? [pendingQuizOffer.topic] : []),
        conversation_context: messages.slice(-5).map(m => `${m.role}: ${m.content}`).join('\n'),
        num_questions: 5,
        difficulty: 'beginner',  // Could be inferred from conversation
      }

      const result = await generateQuiz(request)

      if (result) {
        // Add success message
        const successMsg: Message = {
          id: Date.now().toString(),
          content: `📝 I've created a quiz on "${pendingQuizOffer.topic}"! You can find it in your [Quiz Library](/dashboard/quiz).`,
          role: 'assistant',
          timestamp: new Date(),
          type: 'final_answer'
        }
        setMessages(prev => [...prev, successMsg])
        setPendingQuizOffer(null)
      }
    } catch (error) {
      console.error('Failed to generate quiz:', error)
    }
  }

  const handleDismissRoadmap = () => {
    setPendingRoadmapTrigger(null)
  }

  const handleDismissQuiz = () => {
    setPendingQuizOffer(null)
  }

  const handleStartMilestone = async () => {
    if (!milestoneRoadmapId || !milestonePhaseId || !milestoneId) return
    try {
      await startMilestone(milestonePhaseId, milestoneId)
      await refetchRoadmap()
    } catch (e) {
      console.error('Failed to start milestone:', e)
    }
  }

  const handleCompleteMilestone = async () => {
    if (!milestoneRoadmapId || !milestonePhaseId || !milestoneId) return
    setIsCompleting(true)
    try {
      const note = `Completed via chat on ${new Date().toISOString()}`
      const result = await completeMilestone(milestonePhaseId, milestoneId, note)
      if (result.success) {
        // Append a system-style assistant confirmation message
        const confirmMsg: Message = {
          id: Date.now().toString(),
          content: `✅ Marked milestone as completed${milestoneTitle ? `: **${milestoneTitle}**` : ''}. Progress synced to your roadmap.`,
          role: 'assistant',
          timestamp: new Date(),
          type: 'final_answer'
        }
        setMessages(prev => [...prev, confirmMsg])
        setShowMilestoneBanner(false)
        await refetchRoadmap()
      }
    } catch (e) {
      console.error('Failed to complete milestone:', e)
    } finally {
      setIsCompleting(false)
    }
  }

  const CodeBlock = ({ language, children }: {
    language: string;
    children: React.ReactNode;
  }) => {
    return (
      <div className="relative my-2 sm:my-4 rounded-lg overflow-hidden border border-border bg-[#1e1e1e] max-w-full">
        {/* VS Code-like header */}
        <div className="flex items-center justify-between px-3 sm:px-4 py-2 bg-[#2d2d30] border-b border-[#3e3e42] text-xs">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#ff5f57]"></div>
              <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#ffbd2e]"></div>
              <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-[#28ca42]"></div>
            </div>
            <span className="text-[#cccccc] ml-2 text-xs">{language || 'code'}</span>
          </div>
          <button 
            onClick={() => navigator.clipboard.writeText(String(children))}
            className="text-[#cccccc] hover:text-white text-xs px-2 py-1 rounded bg-[#3c3c3c] hover:bg-[#4c4c4c] transition-colors"
          >
            Copy
          </button>
        </div>
        <div className="overflow-x-auto">
          <pre className="m-0">
            <code
              className={`language-${language || 'text'}`}
              style={{
                display: 'block',
                padding: '12px 16px',
                background: '#1e1e1e',
                color: '#d4d4d4',
                fontSize: '13px',
                lineHeight: '1.5',
                fontFamily: 'SF Mono, Monaco, Inconsolata, "Roboto Mono", Consolas, "Courier New", monospace',
                whiteSpace: 'pre',
                wordBreak: 'normal',
                overflowWrap: 'normal',
              }}
            >
              {String(children).replace(/\n$/, '')}
            </code>
          </pre>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 left-[var(--sidebar-width)] top-16 flex flex-col bg-background">
      {/* Messages Area - Scrollable */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.role === 'assistant' && (
              <Avatar className="h-8 w-8 shrink-0 ring-2 ring-primary/10">
                <AvatarFallback className="bg-gradient-to-br from-primary to-primary/80 text-primary-foreground">
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            )}
            
            <div
              className={`rounded-2xl px-4 py-3 shadow-sm ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground max-w-[85%] sm:max-w-[70%]'
                  : 'bg-card border max-w-[95%] sm:max-w-[85%] lg:max-w-[80%]'
              }`}
            >
              {message.role === 'assistant' ? (
                <div className="text-sm leading-relaxed prose prose-sm dark:prose-invert max-w-none wrap-break-word">
                  {message.thinking_content && (
                    <Collapsible open={openThinking[message.id] || false} onOpenChange={() => toggleThinking(message.id)}>
                      <CollapsibleTrigger className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground mb-2 w-full text-left">
                        <span>🤔 Show thinking process</span>
                        <svg 
                          className={`w-3 h-3 transition-transform ${openThinking[message.id] ? 'rotate-180' : ''}`}
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </CollapsibleTrigger>
                      <CollapsibleContent className="border-l-2 border-blue-200 dark:border-blue-700 pl-3 mb-3 bg-blue-50/30 dark:bg-blue-950/20 rounded-r-md py-2 overflow-x-auto">
                        <div className="text-blue-600 dark:text-blue-400 font-medium mb-2 text-xs">🧠 AI Reasoning Process:</div>
                        <ReactMarkdown
                          remarkPlugins={[remarkMath, remarkGfm]}
                          rehypePlugins={[rehypeKatex]}
                          components={{
                            code({className, children, ...props}) {
                              const match = /language-(\w+)/.exec(className || '')
                              const language = match ? match[1] : ''
                              const isInline = !className?.includes('language-')
                              
                              if (!isInline && language) {
                                return <CodeBlock language={language}>{children}</CodeBlock>
                              }
                              
                              return (
                                <code className="bg-blue-100 dark:bg-blue-900 px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                                  {children}
                                </code>
                              )
                            },
                            p: ({children}) => <p className="mb-1 last:mb-0 text-xs text-blue-700 dark:text-blue-300">{children}</p>,
                            ul: ({children}) => <ul className="list-disc list-inside mb-1 space-y-0.5 text-blue-700 dark:text-blue-300">{children}</ul>,
                            li: ({children}) => <li className="text-xs">{children}</li>,
                            strong: ({children}) => <strong className="font-semibold text-blue-800 dark:text-blue-200">{children}</strong>,
                          }}
                        >
                          {message.thinking_content}
                        </ReactMarkdown>
                      </CollapsibleContent>
                    </Collapsible>
                  )}
                  
                  <ReactMarkdown
                    remarkPlugins={[remarkMath, remarkGfm]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      code({className, children, ...props}) {
                        const match = /language-(\w+)/.exec(className || '')
                        const language = match ? match[1] : ''
                        const isInline = !className?.includes('language-')
                        
                        if (!isInline && language) {
                          return <CodeBlock language={language}>{children}</CodeBlock>
                        }
                        
                        return (
                          <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                            {children}
                          </code>
                        )
                      },
                      p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                      h1: ({children}) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                      h2: ({children}) => <h2 className="text-base font-semibold mb-2">{children}</h2>,
                      h3: ({children}) => <h3 className="text-sm font-medium mb-1">{children}</h3>,
                      ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                      ol: ({children}) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                      li: ({children}) => <li className="text-sm">{children}</li>,
                      strong: ({children}) => <strong className="font-semibold">{children}</strong>,
                      em: ({children}) => <em className="italic">{children}</em>,
                      blockquote: ({children}) => (
                        <blockquote className="border-l-4 border-muted-foreground/20 pl-4 my-2 italic">
                          {children}
                        </blockquote>
                      )
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
              )}
              
              <div className="flex items-center gap-2 mt-2 text-xs opacity-70">
                <TimeDisplay timestamp={message.timestamp} />
              </div>
            </div>

            {message.role === 'user' && (
              <Avatar className="h-8 w-8 shrink-0 ring-2 ring-primary/20">
                <AvatarFallback className="bg-muted text-foreground">
                  <User className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        ))}

        {/* Current Thinking Message */}
        {currentThinkingMessage && (
          <div className="flex gap-3 animate-in fade-in slide-in-from-bottom-2">
            <Avatar className="h-8 w-8 shrink-0 ring-2 ring-primary/10">
              <AvatarFallback className="bg-gradient-to-br from-primary to-primary/80 text-primary-foreground">
                <Bot className="h-4 w-4" />
              </AvatarFallback>
            </Avatar>
            <div className="rounded-2xl px-4 py-3 bg-card border max-w-[95%] sm:max-w-[85%] lg:max-w-[80%] shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="text-sm font-medium">Thinking...</span>
              </div>
              {currentThinkingMessage.thinking_content && (
                <div className="border-l-2 border-primary/30 pl-3 mb-3 bg-primary/5 rounded-r-lg py-2 text-sm">
                  <div className="text-primary font-medium mb-1 text-xs">🧠 Reasoning:</div>
                  <ReactMarkdown remarkPlugins={[remarkMath, remarkGfm]} rehypePlugins={[rehypeKatex]}>
                    {currentThinkingMessage.thinking_content}
                  </ReactMarkdown>
                </div>
              )}
              {currentThinkingMessage.content && (
                <div className="prose prose-sm dark:prose-invert max-w-none text-sm">
                  <ReactMarkdown remarkPlugins={[remarkMath, remarkGfm]} rehypePlugins={[rehypeKatex]}>
                    {currentThinkingMessage.content}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        )}
          <div ref={messagesEndRef} className="h-0" />
        </div>
      </div>

      {/* Roadmap Generation Prompt */}
      {pendingRoadmapTrigger && (
        <div className="p-3 sm:p-4 border-t bg-blue-50 dark:bg-blue-950/20">
          <Card className="p-4 border-blue-200 dark:border-blue-800 bg-linear-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30">
            <div className="flex items-start gap-3">
              <div className="rounded-full bg-blue-100 dark:bg-blue-900 p-2">
                <Map className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-sm mb-1">🗺️ Create Learning Roadmap?</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  I can create a personalized learning roadmap for <strong>{pendingRoadmapTrigger.topic || 'this topic'}</strong>
                  {' '}({pendingRoadmapTrigger.domain}) at a {pendingRoadmapTrigger.user_level} level.
                </p>
                <div className="flex gap-2">
                  <Button
                    onClick={handleGenerateRoadmap}
                    size="sm"
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <CheckCircle2 className="h-4 w-4 mr-1" />
                    Create Roadmap
                  </Button>
                  <Button
                    onClick={handleDismissRoadmap}
                    size="sm"
                    variant="outline"
                  >
                    Not now
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Quiz Offer Prompt */}
      {pendingQuizOffer && (
        <div className="p-3 sm:p-4 border-t bg-green-50 dark:bg-green-950/20">
          <Card className="p-4 border-green-200 dark:border-green-800 bg-linear-to-r from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30">
            <div className="flex items-start gap-3">
              <div className="rounded-full bg-green-100 dark:bg-green-900 p-2">
                <FileQuestion className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-sm mb-1">📝 Test Your Knowledge?</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Ready to practice what you&apos;ve learned about <strong>{pendingQuizOffer.topic || 'this topic'}</strong>?
                  I can generate a quiz to help reinforce your understanding.
                </p>
                <div className="flex gap-2">
                  <Button
                    onClick={handleGenerateQuiz}
                    size="sm"
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <FileQuestion className="h-4 w-4 mr-1" />
                    Generate Quiz
                  </Button>
                  <Button
                    onClick={handleDismissQuiz}
                    size="sm"
                    variant="outline"
                  >
                    Maybe later
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Milestone Context Banner */}
      {showMilestoneBanner && milestoneRoadmapId && milestonePhaseId && milestoneId && (
        <div className="p-3 sm:p-4 border-t bg-amber-50 dark:bg-amber-950/20">
          <Card className="p-4 border-amber-200 dark:border-amber-800 bg-linear-to-r from-amber-50 to-yellow-50 dark:from-amber-950/30 dark:to-yellow-950/30">
            <div className="flex items-start gap-3">
              <div className="rounded-full bg-amber-100 dark:bg-amber-900 p-2">
                <Map className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-sm mb-1">Learning Milestone In Progress</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  You&apos;re working on a roadmap milestone{milestoneTitle ? `: ` : ''}
                  {milestoneTitle ? <strong>{milestoneTitle}</strong> : <span> — keep going!</span>}
                </p>
                <div className="flex gap-2">
                  <Button
                    onClick={handleStartMilestone}
                    size="sm"
                    variant="outline"
                  >
                    Set In Progress
                  </Button>
                  <Button
                    onClick={handleCompleteMilestone}
                    size="sm"
                    className="bg-amber-600 hover:bg-amber-700"
                    disabled={isCompleting}
                  >
                    {isCompleting ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-1" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 mr-1" />
                    )}
                    Mark Complete
                  </Button>
                  <Button
                    onClick={() => setShowMilestoneBanner(false)}
                    size="sm"
                    variant="ghost"
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Fixed Input Area */}
      <div className="shrink-0 border-t bg-background">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3">
          <div className="flex gap-3">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about programming or mathematics..."
              disabled={isLoading}
              className="flex-1 h-11 text-sm rounded-xl border-2 focus-visible:ring-2 focus-visible:ring-primary/20"
            />
            <Button 
              onClick={sendMessage} 
              disabled={!input.trim() || isLoading}
              size="icon"
              className="h-11 w-11 rounded-xl shrink-0"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            AI can make mistakes. Verify important information.
          </p>
        </div>
      </div>
    </div>
  )
}
