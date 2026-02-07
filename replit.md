# TaixiuBot (Python Version)

## Overview
A Discord bot application for running a virtual dice game called "Tai Xiu." Players bet on "Tai" (Over) or "Xiu" (Under) outcomes using in-game currency. This version is built using Python for better resource efficiency.

## Architecture
- **Bot Logic**: `bot.py` using `discord.py`.
- **Database**: `db_manager.py` using `psycopg2` for PostgreSQL.
- **Environment**: Managed via `.env` (requires `DISCORD_TOKEN` and `DATABASE_URL`).

## Running
- The bot starts automatically via the "Start application" workflow.
- Command: `python bot.py`

## Commands
- `?tx`: Start game
- `?cuoc <tai|xiu> <amount>`: Place bet
- `?daily`: Daily reward
- `?money`: Check balance
- `?top`: Leaderboard
- `?give @user <amount>`: Transfer money
- `?txstop`: Stop game
- `?txtt`: Toggle auto-restart loop
