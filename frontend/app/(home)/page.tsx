"use client"
import { Button } from "@/components/ui/button"
import Image from "next/image"
import { createSupabaseBrowserClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Typewriter } from "@/components/homepage/typewriter"
import { AnimatedSection, AnimatedCard, StaggerContainer, StaggerItem } from "@/components/homepage/animated-section"
import { ArrowRight, Sparkles, Brain, Target, Shield, Zap, BookOpen, Code, Calculator } from 'lucide-react'

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

  const typewriterWords = [
    "Master Programming",
    "Learn Mathematics",
    "Build Your Future",
    "Unlock Your Potential",
    "Study Smarter"
  ]

  return (
    <div className="relative overflow-hidden">
      {/* Graph Paper Background - Faded style like notebook paper */}
      <div className="fixed inset-0 -z-10 bg-background">
        {/* Main grid - larger squares */}
        <div 
          className="absolute inset-0 opacity-[0.15] dark:opacity-[0.08]"
          style={{
            backgroundImage: `
              linear-gradient(to right, #888 1px, transparent 1px),
              linear-gradient(to bottom, #888 1px, transparent 1px)
            `,
            backgroundSize: '80px 80px'
          }}
        />
        {/* Secondary grid - smaller squares for detail */}
        <div 
          className="absolute inset-0 opacity-[0.08] dark:opacity-[0.04]"
          style={{
            backgroundImage: `
              linear-gradient(to right, #888 1px, transparent 1px),
              linear-gradient(to bottom, #888 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px'
          }}
        />
        {/* Radial fade overlay - fades edges */}
        <div 
          className="absolute inset-0 bg-background"
          style={{
            mask: 'radial-gradient(ellipse 80% 80% at 50% 50%, transparent 30%, black 100%)',
            WebkitMask: 'radial-gradient(ellipse 80% 80% at 50% 50%, transparent 30%, black 100%)'
          }}
        />
      </div>

      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center">
        {/* Floating decorative elements */}
        <motion.div
          className="absolute top-20 left-10 w-20 h-20 rounded-full bg-primary/10 blur-2xl"
          animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
          transition={{ duration: 4, repeat: Infinity }}
        />
        <motion.div
          className="absolute bottom-40 right-20 w-32 h-32 rounded-full bg-primary/10 blur-3xl"
          animate={{ scale: [1.2, 1, 1.2], opacity: [0.5, 0.3, 0.5] }}
          transition={{ duration: 5, repeat: Infinity }}
        />

        <div className="w-full max-w-[1400px] mx-auto px-6 lg:px-12">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-12 lg:gap-20">
            {/* Left Content - Minimal & Modern */}
            <motion.div 
              className="flex-1 space-y-8 text-center lg:text-left"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: [0.21, 0.47, 0.32, 0.98] }}
            >
              {/* Badge */}
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20"
              >
                <Sparkles className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium text-primary">AI-Powered Learning</span>
              </motion.div>

              {/* Main Heading with Typewriter */}
              <div className="space-y-4">
                <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-bold tracking-tight font-exo">
                  <span className="text-foreground">Learn to</span>
                  <br />
                  <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
                    <Typewriter 
                      words={typewriterWords}
                      typingSpeed={80}
                      deletingSpeed={40}
                      delayBetweenWords={2500}
                    />
                  </span>
                </h1>
              </div>

              {/* Subtitle */}
              <motion.p 
                className="text-lg sm:text-xl text-muted-foreground max-w-lg mx-auto lg:mx-0 leading-relaxed font-andika"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
              >
                Your personal AI tutor that adapts to your pace. 
                Master programming and mathematics with intelligent, personalized guidance.
              </motion.p>

              {/* CTA Buttons */}
              <motion.div 
                className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start pt-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
              >
                <Button 
                  size="lg" 
                  className="group font-medium text-base px-8 py-6 h-auto font-andika rounded-xl shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all duration-300"
                  onClick={() => {
                    if (authed === null) return
                    if (authed) router.push('/dashboard/chat')
                    else router.push('/login')
                  }}
                >
                  Start Learning Free
                  <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Button>
                <Button 
                  variant="outline" 
                  size="lg"
                  className="font-medium text-base px-8 py-6 h-auto font-andika rounded-xl border-2 hover:bg-primary/5 transition-all duration-300"
                >
                  Watch Demo
                </Button>
              </motion.div>

              {/* Stats */}
              <motion.div 
                className="flex flex-wrap gap-8 justify-center lg:justify-start pt-8"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
              >
                {[
                  { value: "10K+", label: "Students" },
                  { value: "500+", label: "Lessons" },
                  { value: "4.9", label: "Rating" }
                ].map((stat, i) => (
                  <div key={i} className="text-center lg:text-left">
                    <div className="text-2xl font-bold text-foreground font-exo">{stat.value}</div>
                    <div className="text-sm text-muted-foreground font-andika">{stat.label}</div>
                  </div>
                ))}
              </motion.div>
            </motion.div>

            {/* Right Content - Robot Animation */}
            <motion.div 
              className="flex-1 flex justify-center lg:justify-end"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8, delay: 0.3 }}
            >
              <motion.div 
                className="relative"
                animate={{ y: [-10, 10, -10] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              >
                {/* Glow effect behind robot */}
                <div className="absolute inset-0 bg-gradient-to-r from-primary/30 to-primary/10 rounded-full blur-3xl scale-110" />
                <Image 
                  src='/gifs/welcome-bot.gif' 
                  alt='Welcome Bot' 
                  width={550} 
                  height={300}
                  className="relative w-full max-w-md lg:max-w-lg xl:max-w-xl h-auto drop-shadow-2xl"
                  priority
                />
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Learning Domains Section */}
      <section className="py-24 lg:py-32">
        <div className="w-full max-w-[1400px] mx-auto px-6 lg:px-12">
          <AnimatedSection className="text-center space-y-4 mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium font-andika">
              Specializations
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground font-exo">
              Master Two Essential Domains
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-andika">
              Build strong foundations in the most in-demand skills
            </p>
          </AnimatedSection>

          <div className="grid gap-8 md:grid-cols-2 max-w-6xl mx-auto">
            <AnimatedCard index={0}>
              <div className="group relative h-full p-8 lg:p-10 rounded-2xl border border-border bg-card/50 backdrop-blur-sm overflow-hidden">
                {/* Gradient hover effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                
                <div className="relative space-y-6">
                  <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-blue-500/10 text-blue-500">
                    <Code className="w-7 h-7" />
                  </div>
                  <h3 className="text-2xl font-bold text-card-foreground font-exo">
                    Programming Basics
                  </h3>
                  <p className="text-muted-foreground leading-relaxed font-andika">
                    Learn fundamental programming concepts, syntax, problem-solving techniques, and coding best practices.
                  </p>
                  <ul className="space-y-3 text-sm text-muted-foreground font-andika">
                    {[
                      "Variables, Data Types & Control Structures",
                      "Functions & Object-Oriented Programming",
                      "Algorithm Design & Problem Solving",
                      "Code Debugging & Best Practices"
                    ].map((item, i) => (
                      <li key={i} className="flex items-center gap-3">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </AnimatedCard>

            <AnimatedCard index={1}>
              <div className="group relative h-full p-8 lg:p-10 rounded-2xl border border-border bg-card/50 backdrop-blur-sm overflow-hidden">
                {/* Gradient hover effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                
                <div className="relative space-y-6">
                  <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-emerald-500/10 text-emerald-500">
                    <Calculator className="w-7 h-7" />
                  </div>
                  <h3 className="text-2xl font-bold text-card-foreground font-exo">
                    Math Fundamentals
                  </h3>
                  <p className="text-muted-foreground leading-relaxed font-andika">
                    Master essential mathematical concepts from basic arithmetic to advanced analytical thinking.
                  </p>
                  <ul className="space-y-3 text-sm text-muted-foreground font-andika">
                    {[
                      "Arithmetic, Algebra & Geometry",
                      "Statistics, Probability & Calculus",
                      "Mathematical Reasoning & Proofs",
                      "Real-world Problem Applications"
                    ].map((item, i) => (
                      <li key={i} className="flex items-center gap-3">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </AnimatedCard>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 lg:py-32 bg-muted/30">
        <div className="w-full max-w-[1400px] mx-auto px-6 lg:px-12">
          <AnimatedSection className="text-center space-y-4 mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium font-andika">
              Features
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground font-exo">
              Why Choose Our Platform?
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-andika">
              Experience the future of personalized education
            </p>
          </AnimatedSection>

          <StaggerContainer className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: Brain,
                title: "Autonomous Learning",
                description: "AI adapts to your learning style and pace, providing personalized instruction automatically.",
                color: "text-violet-500",
                bg: "bg-violet-500/10"
              },
              {
                icon: Target,
                title: "One-to-One Tutoring",
                description: "Get individual attention and customized learning paths tailored to your needs.",
                color: "text-rose-500",
                bg: "bg-rose-500/10"
              },
              {
                icon: Zap,
                title: "Instant Feedback",
                description: "Get immediate responses to questions and solutions for faster learning.",
                color: "text-amber-500",
                bg: "bg-amber-500/10"
              },
              {
                icon: Shield,
                title: "Private & Secure",
                description: "Your learning data and progress remain completely private and secure.",
                color: "text-emerald-500",
                bg: "bg-emerald-500/10"
              },
              {
                icon: BookOpen,
                title: "Comprehensive Tracking",
                description: "Track your progress in real-time with detailed analytics and insights.",
                color: "text-blue-500",
                bg: "bg-blue-500/10"
              },
              {
                icon: Sparkles,
                title: "Smart Assessments",
                description: "Intelligent quizzes that adapt to your skill level and learning progress.",
                color: "text-pink-500",
                bg: "bg-pink-500/10"
              }
            ].map((feature, i) => (
              <StaggerItem key={i}>
                <div className="group h-full p-6 lg:p-8 rounded-2xl border border-border bg-card/50 backdrop-blur-sm hover:shadow-xl transition-all duration-300">
                  <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${feature.bg} ${feature.color} mb-5`}>
                    <feature.icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3 text-card-foreground font-exo">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed font-andika">
                    {feature.description}
                  </p>
                </div>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-24 lg:py-32">
        <div className="w-full max-w-[1400px] mx-auto px-6 lg:px-12">
          <AnimatedSection className="text-center space-y-4 mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium font-andika">
              Process
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground font-exo">
              How It Works
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-andika">
              Start your learning journey in three simple steps
            </p>
          </AnimatedSection>

          <div className="grid gap-8 md:grid-cols-3 max-w-6xl mx-auto">
            {[
              {
                step: "01",
                title: "Sign Up",
                description: "Create your free account and tell us about your learning goals"
              },
              {
                step: "02",
                title: "Take Assessment",
                description: "Complete a quick assessment so we can personalize your experience"
              },
              {
                step: "03",
                title: "Start Learning",
                description: "Begin your personalized learning journey with AI guidance"
              }
            ].map((item, i) => (
              <AnimatedCard key={i} index={i}>
                <div className="relative text-center p-8">
                  <div className="text-6xl font-bold text-primary/10 font-exo mb-4">{item.step}</div>
                  <h3 className="text-xl font-semibold mb-3 text-foreground font-exo">{item.title}</h3>
                  <p className="text-muted-foreground font-andika">{item.description}</p>
                  
                  {/* Connector line */}
                  {i < 2 && (
                    <div className="hidden md:block absolute top-1/2 -right-4 w-8 border-t-2 border-dashed border-primary/20" />
                  )}
                </div>
              </AnimatedCard>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 lg:py-32">
        <div className="w-full max-w-[1400px] mx-auto px-6 lg:px-12">
          <AnimatedSection>
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary/90 to-primary p-12 lg:p-20">
              {/* Decorative elements */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
              <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
              
              <div className="relative text-center space-y-6 max-w-3xl mx-auto">
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-primary-foreground font-exo">
                  Ready to Transform Your Learning?
                </h2>
                <p className="text-lg sm:text-xl text-primary-foreground/80 leading-relaxed font-andika">
                  Join thousands of students who are mastering programming and mathematics with AI-powered personalized tutoring.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
                  <Button 
                    size="lg" 
                    variant="secondary"
                    className="group font-medium text-base px-8 py-6 h-auto font-andika rounded-xl"
                    onClick={() => {
                      if (authed === null) return
                      if (authed) router.push('/dashboard/chat')
                      else router.push('/signup')
                    }}
                  >
                    Get Started Free
                    <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </Button>
                  <Button 
                    variant="outline" 
                    size="lg"
                    className="font-medium text-base px-8 py-6 h-auto font-andika rounded-xl bg-transparent border-2 border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground/10"
                  >
                    Schedule Demo
                  </Button>
                </div>
              </div>
            </div>
          </AnimatedSection>
        </div>
      </section>

      {/* Footer spacing */}
      <div className="h-16" />
    </div>
  )
}
