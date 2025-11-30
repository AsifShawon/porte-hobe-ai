"use client"

import React, { useState, useRef, useEffect } from 'react'
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
import { useRoadmaps } from '@/hooks/useRoadmap'
import { useQuizzes } from '@/hooks/useQuiz'
import type { CreateRoadmapRequest } from '@/types/roadmap'
import type { GenerateQuizRequest } from '@/types/quiz'

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
  const [roadmapId, setRoadmapId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Roadmap and Quiz state
  const [pendingRoadmapTrigger, setPendingRoadmapTrigger] = useState<RoadmapTrigger | null>(null)
  const [pendingQuizOffer, setPendingQuizOffer] = useState<QuizOffer | null>(null)
  const { createRoadmap } = useRoadmaps()
  const { generateQuiz } = useQuizzes()

  // Check for roadmap/conversation linking from URL params
  useEffect(() => {
    const roadmap = searchParams.get('roadmap')
    const conversation = searchParams.get('conversation_id')

    if (roadmap) {
      setRoadmapId(roadmap)
    }
    if (conversation && !conversationId) {
      setConversationId(conversation)
    }
  }, [searchParams, conversationId])

  // Check for continued conversation from history
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const continueData = sessionStorage.getItem('continueChat')
      if (continueData) {
        try {
          const parsed = JSON.parse(continueData) as { conversationId?: string; messages?: unknown }
          const { conversationId: convId, messages: historyMessages } = parsed
          setConversationId(convId ?? null)
          
          type HistoryItem = {
            id?: string
            message?: string
            content?: string
            role?: 'user' | 'assistant' | string
            created_at?: string | number
          }
          
          const loadedMessages: Message[] = Array.isArray(historyMessages)
            ? (historyMessages as HistoryItem[]).map((msg) => {
                const role = msg.role === 'assistant' ? 'assistant' : 'user'
                return {
                  id: msg.id || Date.now().toString(),
                  content: msg.message || msg.content || '',
                  role,
                  timestamp: new Date(msg.created_at || Date.now()),
                  type: role === 'assistant' ? 'final_answer' : undefined
                }
              })
            : []
          
          setMessages([messages[0], ...loadedMessages]) // Keep welcome message
          
          // Clear the session storage
          sessionStorage.removeItem('continueChat')
        } catch (error) {
          console.error('Failed to load continued conversation:', error)
        }
      }
    }
  }, [])

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

  const sendMessage = async () => {
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
          conversation_id: conversationId  // Pass conversation_id for linking
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
  }

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
        domain: pendingRoadmapTrigger.domain as 'programming' | 'math' | 'general',
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
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 sm:gap-3 p-3 sm:p-4 border-b bg-background shrink-0">
        <div className="flex items-center gap-2">
          <Avatar className="h-7 w-7 sm:h-8 sm:w-8">
            <AvatarFallback className="bg-primary text-primary-foreground">
              <Bot className="h-3 w-3 sm:h-4 sm:w-4" />
            </AvatarFallback>
          </Avatar>
          <div>
            <h2 className="font-semibold text-sm sm:text-base">AI Tutor</h2>
            <p className="text-xs text-muted-foreground">Programming & Math Assistant</p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push('/dashboard/chat/history')}
            className="gap-2"
          >
            <History className="h-4 w-4" />
            <span className="hidden sm:inline">History</span>
          </Button>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Sparkles className="h-3 w-3" />
            <span className="hidden sm:inline">Autonomous Learning</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 sm:p-4 pb-2">
        <div className="space-y-4 min-h-full flex flex-col">
          <div className="flex-1" />
          {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-2 sm:gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.role === 'assistant' && (
              <Avatar className="h-7 w-7 sm:h-8 sm:w-8 mt-1 shrink-0">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  <Bot className="h-3 w-3 sm:h-4 sm:w-4" />
                </AvatarFallback>
              </Avatar>
            )}
            
            <div
              className={`rounded-lg p-2 sm:p-3 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground ml-auto max-w-[85%] sm:max-w-[75%]'
                  : 'bg-muted max-w-[95%] sm:max-w-[90%] lg:max-w-[85%]'
              }`}
            >
              {message.role === 'assistant' ? (
                <div className="text-sm leading-relaxed prose prose-sm dark:prose-invert max-w-none break-words">
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
                <p className="text-sm">{message.content}</p>
              )}
              <div className="flex justify-between items-center mt-2">
                <span className="text-xs opacity-70">
                  <TimeDisplay timestamp={message.timestamp} />
                </span>
              </div>
            </div>

            {message.role === 'user' && (
              <Avatar className="h-7 w-7 sm:h-8 sm:w-8 mt-1 shrink-0">
                <AvatarFallback className="bg-muted">
                  <User className="h-3 w-3 sm:h-4 sm:w-4" />
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        ))}

        {/* Current Thinking message */}
        {currentThinkingMessage && (
          <div className="flex gap-2 sm:gap-3 justify-start">
            <Avatar className="h-7 w-7 sm:h-8 sm:w-8 mt-1 shrink-0">
              <AvatarFallback className="bg-primary text-primary-foreground">
                <Bot className="h-3 w-3 sm:h-4 sm:w-4" />
              </AvatarFallback>
            </Avatar>
            <div className="rounded-lg p-2 sm:p-3 bg-muted max-w-[95%] sm:max-w-[90%] lg:max-w-[85%]">
              <div className="flex items-center gap-2 mb-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">AI is thinking & composing...</span>
              </div>
              {currentThinkingMessage.thinking_content && (
                <div className="text-xs border-l-2 border-blue-200 dark:border-blue-700 pl-3 mt-2 bg-blue-50/50 dark:bg-blue-950/30 rounded-r-md py-2 mb-2 overflow-x-auto">
                  <div className="text-blue-600 dark:text-blue-400 font-medium mb-1">🧠 Reasoning:</div>
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
          <Card className="p-4 border-blue-200 dark:border-blue-800 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30">
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
          <Card className="p-4 border-green-200 dark:border-green-800 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30">
            <div className="flex items-start gap-3">
              <div className="rounded-full bg-green-100 dark:bg-green-900 p-2">
                <FileQuestion className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-sm mb-1">📝 Test Your Knowledge?</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Ready to practice what you've learned about <strong>{pendingQuizOffer.topic || 'this topic'}</strong>?
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

      {/* Input */}
      <div className="p-3 sm:p-4 border-t bg-background shrink-0">
        <div className="flex gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about programming or mathematics..."
            disabled={isLoading}
            className="flex-1 text-sm"
          />
          <Button 
            onClick={sendMessage} 
            disabled={!input.trim() || isLoading}
            size="icon"
            className="shrink-0"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2 text-center hidden sm:block">
          AI can make mistakes. Verify important information and use for educational purposes.
        </p>
      </div>
    </div>
  )
}
