"use client"
import { useState } from 'react'
import { createSupabaseBrowserClient } from '@/lib/supabase/client'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import Link from 'next/link'

export default function LoginPage() {
  const supabase = createSupabaseBrowserClient()
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirectTo = searchParams.get('redirectTo') || '/dashboard'
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function onLogin(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      const { error } = await supabase.auth.signInWithPassword({ 
        email, 
        password 
      })
      
      if (error) {
        setError(error.message)
        setLoading(false)
      } else {
        setSuccess('Logged in successfully! Redirecting...')
        setTimeout(() => {
          router.push(redirectTo)
          router.refresh()
        }, 500)
      }
    } catch {
      setError('An unexpected error occurred')
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto py-12 px-4">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Welcome Back</h1>
        <p className="text-muted-foreground">
          Sign in to continue your learning journey
        </p>
      </div>

      <div className="bg-card border rounded-lg p-6 shadow-sm">
        <form onSubmit={onLogin} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <Input
              id="email"
              type="email"
              placeholder="your.email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          {error && (
            <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-500/10 text-green-500 text-sm p-3 rounded-md">
              {success}
            </div>
          )}

          <Button 
            type="submit" 
            className="w-full" 
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-muted-foreground">Don&apos;t have an account? </span>
          <Link 
            href="/signup" 
            className="text-primary hover:underline font-medium"
          >
            Sign up
          </Link>
        </div>
      </div>
    </div>
  )
}
