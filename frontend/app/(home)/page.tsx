"use client"
import { Button } from "@/components/ui/button"
import Image from "next/image"
import { createSupabaseBrowserClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

export default function Home() {
  const supabase = createSupabaseBrowserClient()
  const router = useRouter()
  const [authed, setAuthed] = useState<boolean | null>(null)

  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const { data } = await supabase.auth.getSession()
        if (mounted) setAuthed(!!data.session)
      } catch (e) {
        console.warn('session check failed', e)
        if (mounted) setAuthed(false)
      }
    })()
    return () => { mounted = false }
  }, [supabase])
  return (
    <div className="space-y-16 lg:space-y-24">
      {/* Hero section */}
      <div className="flex flex-col lg:flex-row items-center justify-between gap-8 lg:gap-12 min-h-[80vh] lg:min-h-[70vh]">
        {/* Text content */}
        <section className="flex-1 text-center lg:text-left space-y-6 py-8 lg:py-12">
          <div 
            className="text-lg sm:text-xl lg:text-2xl font-bold text-primary mb-2 font-libre-baskerville"
          >
            Your Personal AI Teaching Assistant
          </div>
          <h1 
            className="text-3xl sm:text-4xl md:text-5xl lg:text-4xl xl:text-6xl font-bold text-foreground tracking-tight leading-tight font-exo"
          >
            <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              Porte 
              <span
                className="ml-2 px-4 py-1.5 text-white rounded-md"
                style={{
                 background: "linear-gradient(260deg, #30a695 0%, rgba(48,166,149,0.65) 50%, #8be6d5 100%)"
                }}
              >
                Hobe AI
              </span>
            </span>
          </h1>
          <p 
            className="text-lg sm:text-xl lg:text-2xl text-muted-foreground max-w-2xl mx-auto lg:mx-0 leading-relaxed font-libre-baskerville"
          >
            Experience one-to-one personalized tutoring in Programming Basics and Math Fundamentals. 
            Our autonomous AI assistant adapts to your learning pace, provides instant feedback, 
            and tracks your progress in real-time.
          </p>
          <div 
            className="text-base sm:text-lg text-foreground/80 font-andika"
          >
            Learn • Test • Track Progress • All in One Platform
          </div>
          <div className="flex flex-col sm:flex-row justify-center lg:justify-start gap-4 pt-6">
            <Button 
              size="lg" 
              className="font-medium text-base px-8 py-3 h-auto font-andika"
              onClick={() => {
                if (authed === null) return
                if (authed) router.push('/dashboard/chat')
                else router.push('/login')
              }}
            >
              Start Learning
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              className="font-medium text-base px-8 py-3 h-auto font-andika"
            >
              Take Assessment
            </Button>
          </div>
        </section>
        
        {/* Image content */}
        <div className="flex-1 flex justify-center lg:justify-end">
          <div className="relative w-full max-w-md lg:max-w-lg xl:max-w-xl">
            <Image 
              src='/gifs/welcome-bot.gif' 
              alt='Welcome Bot' 
              width={600} 
              height={300}
              className="w-full h-auto rounded-2xl shadow-2xl border border-border/20"
              priority
            />
          </div>
        </div>
      </div>

      {/* Learning Domains */}
      <section className="space-y-8 lg:space-y-12 py-12 lg:py-16 border-t border-border">
        <div className="text-center space-y-4">
          <h2 
            className="text-2xl sm:text-3xl lg:text-4xl font-bold text-foreground font-exo"
          >
            Master Two Essential Domains
          </h2>
          <p 
            className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto font-andika"
          >
            Our AI assistant specializes in two fundamental learning areas to build your foundation
          </p>
        </div>
        
        <div className="grid gap-6 sm:gap-8 md:grid-cols-2">
          <div className="p-8 lg:p-10 rounded-xl border border-border bg-card hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
            <div className="text-4xl mb-6">💻</div>
            <h3 
              className="text-xl lg:text-2xl font-semibold mb-4 text-card-foreground font-exo"
            >
              Programming Basics
            </h3>
            <p 
              className="text-sm sm:text-base text-muted-foreground leading-relaxed mb-4 font-andika"
            >
              Learn fundamental programming concepts, syntax, problem-solving techniques, and coding best practices. 
              From variables to algorithms, build a solid foundation in computer science.
            </p>
            <ul className="text-sm text-muted-foreground space-y-2 font-andika">
              <li>• Variables, Data Types & Control Structures</li>
              <li>• Functions, Arrays & Object-Oriented Programming</li>
              <li>• Algorithm Design & Problem Solving</li>
              <li>• Code Debugging & Best Practices</li>
            </ul>
          </div>
          
          <div className="p-8 lg:p-10 rounded-xl border border-border bg-card hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
            <div className="text-4xl mb-6">📐</div>
            <h3 
              className="text-xl lg:text-2xl font-semibold mb-4 text-card-foreground font-exo"
            >
              Math Fundamentals
            </h3>
            <p 
              className="text-sm sm:text-base text-muted-foreground leading-relaxed mb-4 font-andika"
            >
              Master essential mathematical concepts from basic arithmetic to advanced topics. 
              Build strong analytical and logical reasoning skills for academic and professional success.
            </p>
            <ul className="text-sm text-muted-foreground space-y-2 font-andika">
              <li>• Arithmetic, Algebra & Geometry</li>
              <li>• Statistics, Probability & Calculus</li>
              <li>• Mathematical Reasoning & Proofs</li>
              <li>• Real-world Problem Applications</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Feature cards */}
      <section className="py-12 lg:py-16">
        <div className="text-center space-y-4 mb-12 lg:mb-16">
          <h2 
            className="text-2xl sm:text-3xl lg:text-4xl font-bold text-foreground font-exo"
          >
            Why Choose Our AI Teaching Assistant?
          </h2>
          <p 
            className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto font-andika"
          >
            Experience the future of personalized education with cutting-edge AI technology
          </p>
        </div>
        
        <div className="grid gap-6 sm:gap-8 md:grid-cols-2 xl:grid-cols-3">
          <div className="group p-6 lg:p-8 rounded-xl border border-border bg-card hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
            <div className="text-3xl mb-4 group-hover:scale-110 transition-transform duration-300">🤖</div>
            <h3 
              className="text-lg sm:text-xl font-semibold mb-3 text-card-foreground font-exo"
            >
              Autonomous Learning
            </h3>
            <p 
              className="text-sm sm:text-base text-muted-foreground leading-relaxed font-andika"
            >
              Our AI adapts to your learning style and pace, providing personalized instruction without human intervention.
            </p>
          </div>

          <div className="group p-6 lg:p-8 rounded-xl border border-border bg-card hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
            <div className="text-3xl mb-4 group-hover:scale-110 transition-transform duration-300">👤</div>
            <h3 
              className="text-lg sm:text-xl font-semibold mb-3 text-card-foreground font-exo"
            >
              One-to-One Tutoring
            </h3>
            <p 
              className="text-sm sm:text-base text-muted-foreground leading-relaxed font-andika"
            >
              Get individual attention and customized learning paths tailored specifically to your needs and goals.
            </p>
          </div>

          <div className="group p-6 lg:p-8 rounded-xl border border-border bg-card hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
            <div className="text-3xl mb-4 group-hover:scale-110 transition-transform duration-300">📈</div>
            <h3 
              className="text-lg sm:text-xl font-semibold mb-3 text-card-foreground font-exo"
            >
              Performance Boost
            </h3>
            <p 
              className="text-sm sm:text-base text-muted-foreground leading-relaxed font-andika"
            >
              Track your progress in real-time and see measurable improvements in your understanding and skills.
            </p>
          </div>

          <div className="group p-6 lg:p-8 rounded-xl border border-border bg-card hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
            <div className="text-3xl mb-4 group-hover:scale-110 transition-transform duration-300">🔒</div>
            <h3 
              className="text-lg sm:text-xl font-semibold mb-3 text-card-foreground font-exo"
            >
              Private & Secure
            </h3>
            <p 
              className="text-sm sm:text-base text-muted-foreground leading-relaxed font-andika"
            >
              Your learning data and progress remain completely private and secure on our platform.
            </p>
          </div>

          <div className="group p-6 lg:p-8 rounded-xl border border-border bg-card hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
            <div className="text-3xl mb-4 group-hover:scale-110 transition-transform duration-300">🎯</div>
            <h3 
              className="text-lg sm:text-xl font-semibold mb-3 text-card-foreground font-exo"
            >
              Learn-Test-Progress
            </h3>
            <p 
              className="text-sm sm:text-base text-muted-foreground leading-relaxed font-andika"
            >
              Complete learning ecosystem with integrated lessons, assessments, and skill tracking all in one place.
            </p>
          </div>

          <div className="group p-6 lg:p-8 rounded-xl border border-border bg-card hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
            <div className="text-3xl mb-4 group-hover:scale-110 transition-transform duration-300">⚡</div>
            <h3 
              className="text-lg sm:text-xl font-semibold mb-3 text-card-foreground font-exo"
            >
              Instant Feedback
            </h3>
            <p 
              className="text-sm sm:text-base text-muted-foreground leading-relaxed font-andika"
            >
              Get immediate responses to your questions and solutions, helping you learn faster and more effectively.
            </p>
          </div>
        </div>
      </section>

      {/* Store Demo Section - Remove this in production */}
      <section className="py-12 border-t border-border">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-foreground font-exo mb-2">
            Store Demo (Development Only)
          </h2>
          <p className="text-muted-foreground font-andika">
            This section demonstrates the Zustand store functionality
          </p>
        </div>
      </section>

      {/* Call to Action */}
      <section className="py-16 lg:py-24 bg-gradient-to-r from-muted/50 to-muted/30 rounded-2xl border border-border">
        <div className="text-center space-y-6 px-6 lg:px-12">
          <h2 
            className="text-2xl sm:text-3xl lg:text-4xl font-bold text-foreground font-exo"
          >
            Ready to Accelerate Your Learning?
          </h2>
          <p 
            className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed font-libre-baskerville"
          >
            Join students worldwide who are mastering programming and mathematics with our AI-powered personalized tutoring system.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4 pt-4">
            <Button 
              size="lg" 
              className="font-medium text-base px-8 py-3 h-auto font-andika"
            >
              Begin Your Journey
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              className="font-medium text-base px-8 py-3 h-auto font-andika"
            >
              Try Demo Lesson
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
