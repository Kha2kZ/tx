import { Link } from "wouter";
import { AlertTriangle, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-background p-4 text-center">
      <div className="relative">
        <div className="absolute inset-0 bg-primary/20 blur-[100px] rounded-full" />
        <AlertTriangle className="h-24 w-24 text-destructive mb-8 relative z-10" />
      </div>
      
      <h1 className="text-6xl font-black mb-4 font-display">404</h1>
      <p className="text-xl text-muted-foreground mb-8 max-w-md">
        The page you are looking for has been lost in the void.
      </p>

      <Link href="/" className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-medium transition-all duration-200 border border-white/5">
        <Home className="w-4 h-4" />
        Return Home
      </Link>
    </div>
  );
}
