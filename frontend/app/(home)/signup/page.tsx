"use client"
import { useState } from 'react'
import { createSupabaseBrowserClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import Link from 'next/link'

export default function SignupPage() {
  const supabase = createSupabaseBrowserClient()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function onSignup(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    // Validation
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long')
      return
    }

    setLoading(true)

    try {
      const { error } = await supabase.auth.signUp({ 
        email, 
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/dashboard`
        }
      })
      
      if (error) {
        setError(error.message)
        setLoading(false)
      } else {
        setSuccess('Account created successfully! Redirecting to dashboard...')
        setTimeout(() => {
          router.push('/dashboard')
          router.refresh()
        }, 1000)
      }
    } catch {
      setError('An unexpected error occurred')
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto py-12 px-4">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Create Account</h1>
        <p className="text-muted-foreground">
          Start your personalized learning journey today
        </p>
      </div>

      <div className="bg-card border rounded-lg p-6 shadow-sm">
        <form onSubmit={onSignup} className="space-y-4">
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
              placeholder="Create a password (min 6 characters)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
              minLength={6}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="confirmPassword" className="text-sm font-medium">
              Confirm Password
            </label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={loading}
              minLength={6}
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
            {loading ? 'Creating account...' : 'Create Account'}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-muted-foreground">Already have an account? </span>
          <Link 
            href="/login" 
            className="text-primary hover:underline font-medium"
          >
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}
