import Navbar from "@/components/homepage/navbar"

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      <main className="container mx-auto px-4 py-6 grow">
        <div className="mx-auto max-w-4xl">
          {children}
        </div>
      </main>
      
      {/* Footer */}
      <footer className="border-t border-border bg-muted/50 py-6">
        <div className="container mx-auto px-4 text-center">
          <p 
            className="text-sm text-muted-foreground font-andika"
          >
            © 2025 Porte Hobe AI. Built with ❤️ using modern web technologies.
          </p>
        </div>
      </footer>
    </div>
  )
}
