import { pgTable, text, serial, integer, boolean, timestamp, bigint } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  discordId: text("discord_id").notNull().unique(),
  username: text("username").notNull(),
  balance: bigint("balance", { mode: "number" }).default(0).notNull(),
  dailyStreak: integer("daily_streak").default(0).notNull(),
  lastDaily: timestamp("last_daily"),
  isAdmin: boolean("is_admin").default(false).notNull(),
});

export const insertUserSchema = createInsertSchema(users).omit({ 
  id: true,
  balance: true,
  dailyStreak: true,
  lastDaily: true,
  isAdmin: true
});

export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;
