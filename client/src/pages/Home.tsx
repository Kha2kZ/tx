import { useLeaderboard } from "@/hooks/use-leaderboard";
import { Navbar } from "@/components/Navbar";
import { LeaderboardCard } from "@/components/LeaderboardCard";
import { FeatureCard } from "@/components/FeatureCard";
import { motion } from "framer-motion";
import { 
  Dice5, 
  Coins, 
  Trophy, 
  Zap, 
  ShieldCheck, 
  Gift, 
  ArrowRight,
  Circle,
  Gamepad2
} from "lucide-react";

export default function Home() {
  const { data: leaderboard, isLoading } = useLeaderboard();

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
        {/* Abstract Background Shapes */}
        <div className="absolute top-1/4 -left-64 w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-0 -right-64 w-[600px] h-[600px] bg-secondary/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium mb-8"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              Bot Status: Operational
            </motion.div>

            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight mb-8"
            >
              THE ULTIMATE <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent to-secondary animate-gradient-x">
                TAI XIU EXPERIENCE
              </span>
            </motion.h1>

            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed"
            >
              Join the most exciting dice game on Discord. Bet, win, and climb the leaderboard in real-time. Automated, fair, and incredibly addictive.
            </motion.p>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-4"
            >
              <a 
                href="https://discord.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-primary hover:bg-primary/90 text-white font-bold text-lg shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:-translate-y-1 transition-all duration-200 flex items-center justify-center gap-2"
              >
                Add to Server <ArrowRight className="w-5 h-5" />
              </a>
              <a 
                href="#features"
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-muted/50 hover:bg-muted text-white font-semibold text-lg border border-white/5 transition-all duration-200"
              >
                View Commands
              </a>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 bg-black/20 relative border-t border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Powerful Commands</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">Everything you need to run the perfect game.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard 
              icon={<Dice5 className="w-6 h-6" />}
              title="Start Game"
              description="Start a new round of Tai Xiu with a 30-second betting window."
              command="?tx"
              delay={0.1}
            />
            <FeatureCard 
              icon={<Coins className="w-6 h-6" />}
              title="Place Bets"
              description="Bet your balance on TAI (Over) or XIU (Under). High risk, high reward."
              command="?cuoc <choice> <amount>"
              delay={0.2}
            />
            <FeatureCard 
              icon={<Gift className="w-6 h-6" />}
              title="Daily Rewards"
              description="Claim daily cash rewards that increase with your streak. Don't miss a day!"
              command="?daily"
              delay={0.3}
            />
            <FeatureCard 
              icon={<Trophy className="w-6 h-6" />}
              title="Global Rankings"
              description="Check the top richest players on the server. Compete for the #1 spot."
              command="?top"
              delay={0.4}
            />
            <FeatureCard 
              icon={<Zap className="w-6 h-6" />}
              title="Instant Cash"
              description="Check your current balance and net worth anytime."
              command="?cash"
              delay={0.5}
            />
            <FeatureCard 
              icon={<ShieldCheck className="w-6 h-6" />}
              title="Admin Controls"
              description="Powerful tools for admins to manage games, rewards, and users."
              command="?help"
              delay={0.6}
            />
          </div>
        </div>
      </section>

      {/* Leaderboard Section */}
      <section id="leaderboard" className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-primary/5 pointer-events-none" />
        
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="flex items-center justify-between mb-12">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold mb-2">Live Leaderboard</h2>
              <p className="text-muted-foreground">Real-time wealth rankings across all servers.</p>
            </div>
            <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/5">
              <Circle className="w-3 h-3 text-green-500 fill-green-500 animate-pulse" />
              <span className="text-sm font-medium text-white">Live Updates</span>
            </div>
          </div>

          <div className="space-y-4">
            {isLoading ? (
              // Loading Skeleton
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-20 rounded-xl bg-muted/40 animate-pulse" />
              ))
            ) : leaderboard && leaderboard.length > 0 ? (
              leaderboard.map((entry, index) => (
                <LeaderboardCard 
                  key={entry.discordId} 
                  entry={{...entry, rank: index + 1}} 
                  index={index} 
                />
              ))
            ) : (
              <div className="text-center py-20 bg-muted/20 rounded-2xl border border-white/5">
                <Trophy className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
                <h3 className="text-xl font-bold text-white mb-2">No Data Yet</h3>
                <p className="text-muted-foreground">Be the first to play and claim your spot!</p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/5 bg-black/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
             <Gamepad2 className="w-6 h-6 text-primary" />
             <span className="text-xl font-bold font-display">TAIXIU<span className="text-primary">BOT</span></span>
          </div>
          <p className="text-muted-foreground text-sm mb-8">
            The most advanced gambling bot for your Discord community.
          </p>
          <div className="flex items-center justify-center gap-6 text-sm text-muted-foreground">
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-white transition-colors">Support Server</a>
          </div>
          <p className="mt-8 text-xs text-zinc-600">
            © 2024 TaiXiu Bot. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
