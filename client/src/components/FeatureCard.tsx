import { ReactNode } from "react";
import { motion } from "framer-motion";

interface FeatureCardProps {
  icon: ReactNode;
  title: string;
  description: string;
  command: string;
  delay?: number;
}

export function FeatureCard({ icon, title, description, command, delay = 0 }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.5 }}
      className="bg-muted/20 border border-white/5 rounded-2xl p-6 hover:bg-muted/30 hover:border-primary/20 transition-all duration-300 group"
    >
      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 group-hover:bg-primary/20 transition-all duration-300">
        {icon}
      </div>
      
      <h3 className="text-xl font-bold mb-2 text-white group-hover:text-primary transition-colors">{title}</h3>
      <p className="text-muted-foreground mb-4 leading-relaxed">{description}</p>
      
      <div className="inline-flex items-center px-3 py-1.5 rounded-md bg-black/40 border border-white/10">
        <span className="font-mono text-sm text-secondary">{command}</span>
      </div>
    </motion.div>
  );
}
