"use client"
import { createSupabaseBrowserClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'

export function SignoutButton() {
  const supabase = createSupabaseBrowserClient()
  const router = useRouter()

  async function handleSignOut() {
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  return (
    <Button 
      variant="outline" 
      className="w-full" 
      onClick={handleSignOut}
    >
      Sign out
    </Button>
  )
}
