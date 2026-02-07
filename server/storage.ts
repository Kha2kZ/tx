import { users, type User, type InsertUser } from "@shared/schema";
import { db } from "./db";
import { eq, desc, sql } from "drizzle-orm";

export interface IStorage {
  getUser(discordId: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  updateUser(discordId: string, updates: Partial<User>): Promise<User>;
  getTopUsers(limit: number): Promise<User[]>;
}

export class DatabaseStorage implements IStorage {
  async getUser(discordId: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.discordId, discordId));
    return user;
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const [user] = await db.insert(users).values(insertUser).returning();
    return user;
  }

  async updateUser(discordId: string, updates: Partial<User>): Promise<User> {
    const [user] = await db
      .update(users)
      .set(updates)
      .where(eq(users.discordId, discordId))
      .returning();
    return user;
  }

  async getTopUsers(limit: number): Promise<User[]> {
    return await db
      .select()
      .from(users)
      .orderBy(desc(users.balance))
      .limit(limit);
  }
}

export const storage = new DatabaseStorage();
