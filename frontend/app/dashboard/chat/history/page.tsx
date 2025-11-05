"use client"

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/components/auth-provider'
import { useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import { Bot, User, MessageSquare, Search, Trash2, Plus, ArrowLeft } from "lucide-react"
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import 'katex/dist/katex.min.css'

interface ChatMessage {
  id: string
  user_id: string
  conversation_id: string | null
  role: 'user' | 'assistant'
  message: string
  created_at: string
}

interface ConversationGroup {
  id: string
  title: string
  lastMessage: string
  timestamp: Date
  messageCount: number
  messages: ChatMessage[]
}

export default function ChatHistoryPage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [conversations, setConversations] = useState<ConversationGroup[]>([])
  const [filteredConversations, setFilteredConversations] = useState<ConversationGroup[]>([])
  const [selectedConversation, setSelectedConversation] = useState<ConversationGroup | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login')
    }
  }, [user, loading, router])

  const groupMessagesByConversation = React.useCallback((messages: ChatMessage[]): ConversationGroup[] => {
    const conversationMap = new Map<string, ChatMessage[]>()
    
    // Group by conversation_id or by time windows (30 min gap = new conversation)
    let currentConvId = 'conv_1'
    let lastTimestamp: Date | null = null
    const TIME_GAP_THRESHOLD = 30 * 60 * 1000 // 30 minutes in milliseconds
    
    messages.forEach((msg) => {
      const msgTime = new Date(msg.created_at)
      
      if (msg.conversation_id) {
        // Use existing conversation_id
        if (!conversationMap.has(msg.conversation_id)) {
          conversationMap.set(msg.conversation_id, [])
        }
        conversationMap.get(msg.conversation_id)!.push(msg)
      } else {
        // Auto-group by time gaps
        if (lastTimestamp && (msgTime.getTime() - lastTimestamp.getTime()) > TIME_GAP_THRESHOLD) {
          // Start a new conversation
          const nextId = parseInt(currentConvId.split('_')[1]) + 1
          currentConvId = `conv_${nextId}`
        }
        
        if (!conversationMap.has(currentConvId)) {
          conversationMap.set(currentConvId, [])
        }
        conversationMap.get(currentConvId)!.push(msg)
        lastTimestamp = msgTime
      }
    })
    
    // Convert to ConversationGroup array
    const groups: ConversationGroup[] = []
    conversationMap.forEach((msgs, convId) => {
      if (msgs.length === 0) return
      
      // Find first user message as title
      const firstUserMsg = msgs.find(m => m.role === 'user')
      const title = firstUserMsg 
        ? firstUserMsg.message.substring(0, 60) + (firstUserMsg.message.length > 60 ? '...' : '')
        : 'Conversation'
      
      // Last message
      const lastMsg = msgs[msgs.length - 1]
      
      groups.push({
        id: convId,
        title,
        lastMessage: lastMsg.message.substring(0, 100) + (lastMsg.message.length > 100 ? '...' : ''),
        timestamp: new Date(lastMsg.created_at),
        messageCount: msgs.length,
        messages: msgs
      })
    })
    
    // Sort by timestamp (newest first)
    groups.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    
    return groups
  }, [])

  const loadChatHistory = React.useCallback(async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/chat/history?limit=500', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.messages && data.messages.length > 0) {
          // Group messages into conversations
          const grouped = groupMessagesByConversation(data.messages)
          setConversations(grouped)
          setFilteredConversations(grouped)
        }
      }
    } catch (error) {
      console.error('Failed to load chat history:', error)
    } finally {
      setIsLoading(false)
    }
  }, [groupMessagesByConversation])

  useEffect(() => {
    if (user) {
      loadChatHistory()
    }
  }, [user, loadChatHistory])

  useEffect(() => {
    // Filter conversations based on search query
    if (searchQuery.trim() === '') {
      setFilteredConversations(conversations)
    } else {
      const filtered = conversations.filter(conv => 
        conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.lastMessage.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.messages.some(msg => 
          msg.message.toLowerCase().includes(searchQuery.toLowerCase())
        )
      )
      setFilteredConversations(filtered)
    }
  }, [searchQuery, conversations])

  const formatTimestamp = (date: Date): string => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    
    return date.toLocaleDateString()
  }

  const continueConversation = (conversation: ConversationGroup) => {
    // Store conversation messages in sessionStorage to load in chat page
    sessionStorage.setItem('continueChat', JSON.stringify({
      conversationId: conversation.id,
      messages: conversation.messages
    }))
    router.push('/dashboard/chat')
  }

  const deleteConversation = async (conversationId: string) => {
    if (!confirm('Are you sure you want to delete this conversation?')) return
    
    try {
      // Find the conversation to delete
      const conversation = conversations.find(c => c.id === conversationId)
      if (!conversation) return
      
      // Get all message IDs in this conversation
      const messageIds = conversation.messages.map(m => m.id).filter(Boolean)
      
      if (messageIds.length === 0) {
        // No messages to delete, just remove from UI
        setConversations(prev => prev.filter(c => c.id !== conversationId))
        if (selectedConversation?.id === conversationId) {
          setSelectedConversation(null)
        }
        return
      }
      
      console.log('Deleting messages:', messageIds)
      
      // Delete messages by their IDs
      const response = await fetch(`/api/chat/history/delete-messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messageIds }),
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        console.error('Delete error:', errorData)
        throw new Error(errorData.error || errorData.detail || 'Failed to delete conversation')
      }
      
      const result = await response.json()
      console.log('Delete result:', result)
      
      // Remove from UI on success
      setConversations(prev => prev.filter(c => c.id !== conversationId))
      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null)
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
      alert('Failed to delete conversation. Please try again.')
    }
  }

  if (loading || isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading chat history...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar - Conversation List */}
      <div className="w-80 border-r flex flex-col">
        {/* Header */}
        <div className="p-4 border-b space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => router.push('/dashboard/chat')}
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <h2 className="text-lg font-semibold">Chat History</h2>
            </div>
            <Button
              size="sm"
              onClick={() => router.push('/dashboard/chat')}
            >
              <Plus className="h-4 w-4 mr-1" />
              New
            </Button>
          </div>
          
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto">
          {filteredConversations.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">
                {searchQuery ? 'No conversations found' : 'No chat history yet'}
              </p>
              {!searchQuery && (
                <Button
                  variant="link"
                  className="mt-2"
                  onClick={() => router.push('/dashboard/chat')}
                >
                  Start a conversation
                </Button>
              )}
            </div>
          ) : (
            <div className="divide-y">
              {filteredConversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`p-4 cursor-pointer hover:bg-accent transition-colors ${
                    selectedConversation?.id === conversation.id ? 'bg-accent' : ''
                  }`}
                  onClick={() => setSelectedConversation(conversation)}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <h3 className="font-medium text-sm line-clamp-2 flex-1">
                      {conversation.title}
                    </h3>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatTimestamp(conversation.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {conversation.lastMessage}
                  </p>
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <MessageSquare className="h-3 w-3" />
                      {conversation.messageCount} messages
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Content - Conversation View */}
      <div className="flex-1 flex flex-col">
        {selectedConversation ? (
          <>
            {/* Conversation Header */}
            <div className="p-4 border-b flex items-center justify-between">
              <div>
                <h2 className="font-semibold">{selectedConversation.title}</h2>
                <p className="text-sm text-muted-foreground">
                  {selectedConversation.messageCount} messages · {formatTimestamp(selectedConversation.timestamp)}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="default"
                  onClick={() => continueConversation(selectedConversation)}
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Continue Chat
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => deleteConversation(selectedConversation.id)}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {selectedConversation.messages.map((message, idx) => (
                <div
                  key={message.id || idx}
                  className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role === 'assistant' && (
                    <Avatar className="h-8 w-8 shrink-0">
                      <AvatarFallback className="bg-primary text-primary-foreground">
                        <Bot className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}
                  
                  <div
                    className={`rounded-lg p-4 max-w-[70%] ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    {message.role === 'assistant' ? (
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkMath, remarkGfm]}
                          rehypePlugins={[rehypeKatex]}
                        >
                          {message.message}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{message.message}</p>
                    )}
                    <p className="text-xs opacity-70 mt-2">
                      {new Date(message.created_at).toLocaleTimeString()}
                    </p>
                  </div>

                  {message.role === 'user' && (
                    <Avatar className="h-8 w-8 shrink-0">
                      <AvatarFallback className="bg-secondary text-secondary-foreground">
                        <User className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <MessageSquare className="h-16 w-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">Select a conversation</p>
              <p className="text-sm">Choose a conversation from the left to view its history</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
