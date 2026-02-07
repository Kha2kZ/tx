import json
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, file_path="data.json"):
        self.file_path = file_path
        self.users = {}
        self.load_data()

    def load_data(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Convert list to dict for easier access by discord_id
                    self.users = {user['discord_id']: user for user in data}
            except (json.JSONDecodeError, Exception):
                self.users = {}
        else:
            self.users = {}

    def save_data(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(list(self.users.values()), f, indent=4, default=str)
        except Exception as e:
            print(f"Error saving data: {e}")

    def get_user(self, discord_id):
        user = self.users.get(str(discord_id))
        if user and isinstance(user.get('last_daily'), str):
            try:
                user['last_daily'] = datetime.fromisoformat(user['last_daily'])
            except ValueError:
                user['last_daily'] = None
        return user

    def create_user(self, discord_id, username):
        discord_id = str(discord_id)
        user = {
            "discord_id": discord_id,
            "username": username,
            "balance": 0,
            "daily_streak": 0,
            "last_daily": None,
            "is_admin": False
        }
        self.users[discord_id] = user
        self.save_data()
        return user

    def update_user(self, discord_id, **kwargs):
        discord_id = str(discord_id)
        if discord_id not in self.users:
            return None
        
        for key, value in kwargs.items():
            self.users[discord_id][key] = value
        
        # We'll rely on main.py's periodic save or manual call
        # but for small bots, manual save here is safer too
        self.save_data()
        return self.users[discord_id]

    def get_top_users(self, limit=10):
        sorted_users = sorted(self.users.values(), key=lambda x: x['balance'], reverse=True)
        return sorted_users[:limit]

db = DatabaseManager()
