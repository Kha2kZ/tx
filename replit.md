# TaixiuBot

## Overview
A Discord bot application for running a virtual dice game called "Tai Xiu." Players bet on "Tai" (Over) or "Xiu" (Under) outcomes using in-game currency. The project includes a web frontend showcasing the bot, its features, and a live leaderboard.

## Architecture
- **Frontend:** React (Vite) with Tailwind CSS, Framer Motion, shadcn/ui components. Located in `client/src/`.
- **Backend:** Express.js server in `server/`. Handles API routes and Discord bot logic.
- **Database:** PostgreSQL via Drizzle ORM. Schema in `shared/schema.ts`.
- **Discord Integration:** `discord.js` for bot commands and game management in `server/bot.ts`.
- **Shared:** Type definitions and API route contracts in `shared/`.

## Key Files
- `client/src/pages/Home.tsx` - Main landing page with hero, features, and leaderboard
- `client/src/components/` - Navbar, FeatureCard, LeaderboardCard components
- `server/bot.ts` - Discord bot logic with game state management
- `server/routes.ts` - API endpoints (leaderboard)
- `server/storage.ts` - Database CRUD operations
- `shared/schema.ts` - Drizzle ORM schema (users table)
- `shared/routes.ts` - Shared API route definitions

## Running
- `npm run dev` starts both the Express backend and Vite frontend on port 5000
- Requires `DISCORD_TOKEN` secret for bot functionality (optional for web-only)

## Recent Changes
- 2026-02-07: Project imported to Replit environment
