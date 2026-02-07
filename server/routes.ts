import type { Express } from "express";
import type { Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { startBot } from "./bot";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  // Start the Discord Bot
  startBot();

  // API Routes
  app.get(api.leaderboard.list.path, async (req, res) => {
    const topUsers = await storage.getTopUsers(50);
    res.json(topUsers.map(u => ({
      username: u.username,
      balance: u.balance,
      discordId: u.discordId
    })));
  });

  return httpServer;
}
