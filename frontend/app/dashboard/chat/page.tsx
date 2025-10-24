"use client"

import React, { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/components/auth-provider'
import { useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Send, Bot, User, Loader2, Sparkles } from "lucide-react"
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import 'katex/dist/katex.min.css'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  type?: 'thinking' | 'final_answer' | 'complete'
  thinking_content?: string
  request_id?: string
}

export default function ChatPage() {
  const { user, loading } = useAuth()
  const router = useRouter()

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
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const toggleThinking = (messageId: string) => {
    setOpenThinking(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }))
  }
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
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
          history: messages.map(m => ({ role: m.role, content: m.content }))
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
                // Best-effort: persist memory on the backend after streaming completes.
                // We call the frontend proxy `/api/memory/add` which forwards the
                // authenticated request to the FastAPI backend. Failures are
                // non-fatal and logged to console.
                (async () => {
                  try {
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
                    console.warn('Failed to persist memory (non-fatal)', err)
                  }
                })()
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

  const CodeBlock = ({ language, children }: {
    language: string;
    children: React.ReactNode;
  }) => {
    return (
      <div className="relative my-2 sm:my-4 rounded-lg overflow-hidden border border-border bg-[#1e1e1e]">
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
        <pre className="m-0 overflow-x-auto">
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
            }}
          >
            {String(children).replace(/\n$/, '')}
          </code>
        </pre>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 sm:gap-3 p-3 sm:p-4 border-b bg-background flex-shrink-0">
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
        <div className="ml-auto flex items-center gap-1 text-xs text-muted-foreground">
          <Sparkles className="h-3 w-3" />
          <span className="hidden sm:inline">Autonomous Learning</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-4">
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
              className={`max-w-[85%] sm:max-w-[75%] lg:max-w-[65%] rounded-lg p-2 sm:p-3 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground ml-auto'
                  : 'bg-muted'
              }`}
            >
              {message.role === 'assistant' ? (
                <div className="text-sm leading-relaxed">
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
                      <CollapsibleContent className="border-l-2 border-blue-200 dark:border-blue-700 pl-3 mb-3 bg-blue-50/30 dark:bg-blue-950/20 rounded-r-md py-2">
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
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
            <div className="max-w-[85%] sm:max-w-[75%] lg:max-w-[65%] rounded-lg p-2 sm:p-3 bg-muted">
              <div className="flex items-center gap-2 mb-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">AI is thinking & composing...</span>
              </div>
              {currentThinkingMessage.thinking_content && (
                <div className="text-xs border-l-2 border-blue-200 dark:border-blue-700 pl-3 mt-2 bg-blue-50/50 dark:bg-blue-950/30 rounded-r-md py-2 mb-2">
                  <div className="text-blue-600 dark:text-blue-400 font-medium mb-1">🧠 Reasoning:</div>
                  <ReactMarkdown remarkPlugins={[remarkMath, remarkGfm]} rehypePlugins={[rehypeKatex]}>
                    {currentThinkingMessage.thinking_content}
                  </ReactMarkdown>
                </div>
              )}
              {currentThinkingMessage.content && (
                <div className="prose dark:prose-invert max-w-none text-sm">
                  <ReactMarkdown remarkPlugins={[remarkMath, remarkGfm]} rehypePlugins={[rehypeKatex]}>
                    {currentThinkingMessage.content}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 sm:p-4 border-t bg-background flex-shrink-0">
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
