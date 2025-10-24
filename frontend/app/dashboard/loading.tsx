export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center space-y-4">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  )
}
