"use client"
import React from 'react'
import Link from 'next/link'
import { Button } from "@/components/ui/button"
import { ModeToggle } from "@/components/mode-toggle"
import Image from 'next/image'
import { useAuth } from '@/components/auth-provider'
import { createSupabaseBrowserClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'

export default function Navbar() {
  const { session, loading } = useAuth()
  const supabase = createSupabaseBrowserClient()
  const router = useRouter()

  async function handleSignOut() {
    try {
      await supabase.auth.signOut()
      router.push('/')
      router.refresh()
    } catch (e) {
      console.warn('Sign out failed', e)
    }
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container relative flex h-16 max-w-screen-2xl items-center justify-between px-4 mx-auto">
        {/* Logo/Brand */}
        <div className="flex items-center space-x-2">
          <Link href="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
            <div className="h-8 w-8 rounded-lg flex items-center justify-center">
              <Image src="/logo/porte-hobe-ai-logo.png" alt="Logo" width={32} height={32} />
            </div>
            <h1 className="text-xl font-bold text-foreground font-exo">
              Porte Hobe AI
            </h1>
          </Link>
        </div>

        {/* Navigation Links (centered) */}
        <nav className="hidden md:flex absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 items-center space-x-8">
          <Link
            href="/"
            className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors font-andika"
          >
            Home
          </Link>
          <Link
            href="/features"
            className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors font-andika"
          >
            Features
          </Link>
          <Link
            href="/about"
            className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors font-andika"
          >
            About
          </Link>
          <Link
            href="/contact"
            className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors font-andika"
          >
            Contact
          </Link>
        </nav>

        {/* Right side actions */}
        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-2">
            {loading ? (
              <Button variant="ghost" size="sm" className="font-andika" disabled>
                Loading...
              </Button>
            ) : !session ? (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm" className="font-andika">Sign In</Button>
                </Link>
                <Link href="/signup">
                  <Button size="sm" className="font-andika">Get Started</Button>
                </Link>
              </>
            ) : (
              <>
                <Link href="/dashboard">
                  <Button variant="ghost" size="sm" className="font-andika">Dashboard</Button>
                </Link>
                <Button variant="ghost" size="sm" className="font-andika" onClick={handleSignOut}>Sign Out</Button>
              </>
            )}
          </div>
          <ModeToggle />
        </div>

        {/* Mobile menu button - you can expand this later */}
        <div className="md:hidden flex items-center space-x-2">
          <ModeToggle />
        </div>
      </div>
    </header>
  )
}
