import { Link } from "wouter";
import { ExternalLink, Gamepad2 } from "lucide-react";

export function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-background/80 backdrop-blur-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          <Link href="/" className="flex items-center gap-3 group cursor-pointer transition-opacity hover:opacity-80">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/20 group-hover:shadow-primary/40 transition-all duration-300">
              <Gamepad2 className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold tracking-widest bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
              TAIXIU<span className="text-primary">BOT</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link href="/" className="text-sm font-medium text-muted-foreground hover:text-white transition-colors">
              Home
            </Link>
            <Link href="#features" className="text-sm font-medium text-muted-foreground hover:text-white transition-colors">
              Commands
            </Link>
            <Link href="#leaderboard" className="text-sm font-medium text-muted-foreground hover:text-white transition-colors">
              Leaderboard
            </Link>
            <a 
              href="https://discord.com" 
              target="_blank" 
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white text-sm font-semibold transition-all duration-200"
            >
              Add to Discord <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
}
