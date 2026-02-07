import { motion } from "framer-motion";
import { Trophy, Medal, Award } from "lucide-react";
import { cn } from "@/lib/utils";

interface LeaderboardEntry {
  rank: number;
  username: string;
  balance: number;
  discordId: string;
}

export function LeaderboardCard({ entry, index }: { entry: LeaderboardEntry; index: number }) {
  const isTop3 = index < 3;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={cn(
        "group relative flex items-center gap-4 p-4 rounded-xl border transition-all duration-300",
        index === 0 ? "bg-gradient-to-r from-yellow-500/10 to-transparent border-yellow-500/30 shadow-[0_0_30px_-10px_rgba(234,179,8,0.3)]" :
        index === 1 ? "bg-gradient-to-r from-slate-400/10 to-transparent border-slate-400/30" :
        index === 2 ? "bg-gradient-to-r from-amber-700/10 to-transparent border-amber-700/30" :
        "bg-muted/30 border-white/5 hover:border-white/10 hover:bg-muted/50"
      )}
    >
      <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center font-display text-xl font-bold">
        {index === 0 ? <Trophy className="w-8 h-8 text-yellow-500 drop-shadow-lg" /> :
         index === 1 ? <Medal className="w-8 h-8 text-slate-400" /> :
         index === 2 ? <Award className="w-8 h-8 text-amber-700" /> :
         <span className="text-muted-foreground">#{index + 1}</span>}
      </div>

      <div className="flex-grow">
        <h3 className={cn(
          "font-bold text-lg",
          isTop3 ? "text-white" : "text-muted-foreground group-hover:text-white transition-colors"
        )}>
          {entry.username}
        </h3>
        <p className="text-xs text-muted-foreground font-mono truncate max-w-[150px]">
          ID: {entry.discordId}
        </p>
      </div>

      <div className="text-right">
        <p className="font-mono text-xl font-bold text-primary group-hover:text-primary/80 transition-colors">
          ${entry.balance.toLocaleString()}
        </p>
        <p className="text-xs text-muted-foreground uppercase tracking-wider">Balance</p>
      </div>
    </motion.div>
  );
}
