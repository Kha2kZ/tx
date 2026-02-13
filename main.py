import os
import random
import asyncio
import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import json
from discord import ui
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ No DISCORD_TOKEN found in environment variables.")
    exit(1)

# ===== TIMEZONE =====
UTC7 = timezone(timedelta(hours=-7))

def get_now_utc7():
    return datetime.now(timezone.utc).astimezone(UTC7)

# ===== PATHS =====
LOCAL_DATA_PATH = "data.json"

# ===== RING DATA =====
RINGS = {
    "1": {"name": "Nhẫn đá", "price": 50, "desc": "Thể hiện cái nghèo thối nát của bạn:))"},
    "2": {"name": "Nhẫn bạc", "price": 10000, "desc": "Món quà đầu tiên của bạn"},
    "3": {"name": "Nhẫn vàng", "price": 100000, "desc": "Thể hiện sự quan tâm đặc biệt của bạn"},
    "4": {"name": "Nhẫn Kim cương", "price": 1000000, "desc": "Giàu vãi cức:o"},
    "5": {"name": "Nhẫn Ruby", "price": 10000000, "desc": "OMG! Đỉnh!"},
    "6": {"name": "Nhẫn Kim cương tím", "price": 100000000, "desc": "DAMN! VỢ CỦA BẠN THỰC SỰ \"SƯỚNG\":))"},
    "7": {"name": "Nhẫn Thạch anh tím", "price": 1000000000, "desc": "Bùm! Có vẻ ví của bạn đang rất đau nhưng bạn deck quan tâm, cứ thế vì vợ, giữ phong độ nhé!"},
    "8": {"name": "Nhẫn Pha lê", "price": 10000000000, "desc": "..."},
    "9": {"name": "Nhẫn Tinh thể thứ 36", "price": 100000000000, "desc": "Vợ của bạn deck được cãi, var với bạn vì bạn đỉnh vcl rồi!"},
    "10": {"name": "Nhẫn vũ trụ", "price": 36000000000000000, "desc": "Oh, tôi ko thể bình luận về điều này vì có lẽ bạn đang hack à?"}
}

# ===== DATA MANAGER =====
class DataManager:
    def __init__(self, local_path):
        self.local_path = local_path
        self.data = {"users": {}}

    def load(self):
        if os.path.exists(self.local_path):
            try:
                with open(self.local_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)

                if not isinstance(loaded, dict) or "users" not in loaded:
                    print("⚠️ data.json sai định dạng → reset lại dữ liệu.")
                    self.data = {"users": {}}
                    self.save()
                else:
                    self.data = loaded
                    print(f"📥 Loaded data.json from {self.local_path}")
            except Exception as e:
                print(f"❌ Failed to load data.json: {e}")
                self.data = {"users": {}}
                self.save()
        else:
            print("⚠️ No data.json found. Starting fresh.")

    def save(self):
        try:
            with open(self.local_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            print(f"💾 Saved {self.local_path}")
            # Simulation of Drive Backup (In Replit, we use persistent storage)
            # backup_path = f"/drive/backups/{os.path.basename(self.local_path)}"
            # os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            # shutil.copy(self.local_path, backup_path)
        except Exception as e:
            print(f"❌ Failed to save {self.local_path}: {e}")

    def get_user(self, user_id):
        return self.data.get("users", {}).get(user_id)

    def create_user(self, user_id, username):
        user = {
            "username": username,
            "balance": 1000,
            "daily_streak": 0,
            "last_daily": None,
            "married_to": None,
            "ring": None,
            "inventory": [],
            "wins": 0,
            "losses": 0,
            "total_bet": 0
        }
        self.data.setdefault("users", {})[user_id] = user
        self.save()
        return user

    def update_user(self, user_id, **kwargs):
        user = self.get_user(user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            user[key] = value
        self.save()
        return user

    def update_stats(self, user_id, won: bool, amount: int):
        user = self.get_user(user_id)
        if not user: return
        
        if won:
            user["wins"] = user.get("wins", 0) + 1
        else:
            user["losses"] = user.get("losses", 0) + 1
        
        if isinstance(user.get("balance"), (int, float)):
            user["total_bet"] = user.get("total_bet", 0) + amount
        self.save()

    def get_top_users(self, limit=10):
        users = list(self.data.get("users", {}).values())
        def sort_key(u):
            bal = u.get("balance", 0)
            if bal == "inf": return float('inf')
            return bal
        users.sort(key=sort_key, reverse=True)
        return users[:limit]

# ===== INIT DB =====
db = DataManager(LOCAL_DATA_PATH)
db.load()

# ===== BOT SETUP =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

# ===== GAME STATE =====
class GameState:
    def __init__(self):
        self.is_running = False
        self.end_time = None
        self.bets = []
        self.channel_id = None
        self.auto_restart = False

game = GameState()

# ===== CONSTANTS =====
DAILY_REWARDS = [1000, 2000, 5000, 10000, 15000, 20000, 50000, 100000, 150000, 200000, 500000, 1000000]

def get_daily_reward(day):
    if day <= 12:
        return DAILY_REWARDS[day - 1]
    return 1000000 + (day - 12) * 500000

def create_embed(title, description, color=0x0099ff, thumbnail=None):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.timestamp = get_now_utc7()
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    return embed

def format_balance(balance):
    if balance == "inf":
        return "bằng Aura của anh ấy (∞)"
    return f"{balance:,}"

# ===== GAME LOGIC =====
async def start_game(ctx):
    if game.is_running:
        return
    
    game.is_running = True
    game.channel_id = ctx.channel.id
    game.end_time = get_now_utc7() + timedelta(seconds=30)
    game.bets = []

    await ctx.send(embed=create_embed(
        "🎲 GAME TÀI XỈU BẮT ĐẦU!", 
        "⏳ Thời gian cược: **30 giây**\n\n📢 Sử dụng lệnh `?cuoc <tai|xiu> <amount>` để tham gia.\n💰 Đừng quên nhận `?daily` mỗi ngày!", 
        0x00ff00
    ))

    await asyncio.sleep(30)
    await end_game(ctx.channel)

async def end_game(channel, forced_result=None):
    if not game.is_running:
        return

    game.is_running = False
    
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    dice3 = random.randint(1, 6)
    total = dice1 + dice2 + dice3
    
    if forced_result:
        result = forced_result
    else:
        result = "tai" if total >= 11 else "xiu"

    result_emoji = "🔴 TÀI" if result == "tai" else "⚪ XỈU"
    description = f"🎲 Kết quả: **{dice1} - {dice2} - {dice3}** (Tổng: {total})\n🏆 Chiến thắng: **{result_emoji}**\n\n"
    
    winners = []
    losers = []

    for bet in game.bets:
        user = db.get_user(bet['user_id'])
        if not user:
            continue
        
        if bet['choice'] == result:
            if user['balance'] != "inf":
                win_amount = bet['amount'] * 2
                db.update_user(bet['user_id'], balance=user['balance'] + win_amount)
            db.update_stats(bet['user_id'], True, bet['amount'])
            winners.append(f"👤 **{bet['username']}**: +{bet['amount']:,} cash")
        else:
            db.update_stats(bet['user_id'], False, bet['amount'])
            losers.append(f"👤 **{bet['username']}**: -{bet['amount']:,} cash")

    if winners:
        description += f"🎉 **Người thắng:**\n" + "\n".join(winners) + "\n\n"
    else:
        description += "😢 **Không có người thắng.**\n\n"
        
    if losers:
        description += f"💀 **Người thua:**\n" + "\n".join(losers)

    await channel.send(embed=create_embed("🏁 KẾT THÚC GAME TÀI XỈU", description, 0xff0000 if result == "tai" else 0xeeeeee))
    
    game.is_running = False
    game.bets = []

    if game.auto_restart:
        await channel.send(embed=create_embed("🔄 Auto Restart", "✨ Ván đấu mới sẽ tự động bắt đầu sau **10 giây**...", 0xffff00))
        await asyncio.sleep(10)
        await start_game(channel)

# ===== AUTO SAVE TASK =====
async def auto_save_task():
    while True:
        await asyncio.sleep(5)
        db.save()

# ===== MARRIAGE SYSTEM =====
marriage_invites = {}

@bot.group(invoke_without_command=True)
async def marry(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.reply("❌ Bạn không thể tự cưới chính mình!")
    
    user_data = db.get_user(str(ctx.author.id))
    target_data = db.get_user(str(member.id))
    
    if user_data and user_data.get("married_to"):
        return await ctx.reply("❌ Bạn đã kết hôn rồi!")
    if target_data and target_data.get("married_to"):
        return await ctx.reply("❌ Đối phương đã kết hôn rồi!")
    
    marriage_invites[str(member.id)] = str(ctx.author.id)
    await ctx.send(f"{member.mention}", embed=create_embed("💍 LỜI CẦU HÔN", f"❤️ **{ctx.author.name}** đã ngỏ lời cầu hôn với bạn!\n\nSử dụng `?marry accept @{ctx.author.name}` để đồng ý hoặc `?marry decline @{ctx.author.name}` để từ chối.", 0xff69b4, thumbnail=ctx.author.display_avatar.url))

@marry.command()
async def accept(ctx, member: discord.Member):
    if str(ctx.author.id) in marriage_invites and marriage_invites[str(ctx.author.id)] == str(member.id):
        db.update_user(str(ctx.author.id), married_to=str(member.id))
        db.update_user(str(member.id), married_to=str(ctx.author.id))
        del marriage_invites[str(ctx.author.id)]
        await ctx.send(embed=create_embed("🎉 CHÚC MỪNG ĐÁM CƯỚI!", f"🥂 **{ctx.author.name}** và **{member.name}** đã chính thức về chung một nhà!\n✨ Cả hai sẽ được **1.5x** thưởng điểm danh hàng ngày!", 0xff69b4, thumbnail=ctx.author.display_avatar.url))
    else:
        await ctx.reply("❌ Bạn không có lời mời kết hôn nào từ người này!")

@marry.command()
async def decline(ctx, member: discord.Member):
    if str(ctx.author.id) in marriage_invites and marriage_invites[str(ctx.author.id)] == str(member.id):
        del marriage_invites[str(ctx.author.id)]
        await ctx.reply(f"💔 Bạn đã từ chối lời cầu hôn của **{member.name}**.")
    else:
        await ctx.reply("❌ Bạn không có lời mời kết hôn nào từ người này!")

@marry.command()
async def shop(ctx):
    desc = "💍 **Cửa hàng Nhẫn Cưới**\n\n"
    for k, v in RINGS.items():
        desc += f"{k}. **{v['name']}**: {v['price']:,} cash\n*{v['desc']}*\n\n"
    desc += "Sử dụng `?marry buy <số>` để mua nhẫn!"
    await ctx.reply(embed=create_embed("💍 RING SHOP", desc, 0xff69b4))

@marry.command()
async def buy(ctx, ring_id: str):
    if ring_id not in RINGS:
        return await ctx.reply("❌ ID nhẫn không hợp lệ!")
    
    user = db.get_user(str(ctx.author.id))
    if not user: user = db.create_user(str(ctx.author.id), ctx.author.name)
    
    ring = RINGS[ring_id]
    if user['balance'] != "inf" and user['balance'] < ring['price']:
        return await ctx.reply("❌ Bạn không đủ tiền để mua nhẫn này!")
    
    if user['balance'] != "inf":
        db.update_user(str(ctx.author.id), balance=user['balance'] - ring['price'])
    
    inventory = user.get("inventory", [])
    inventory.append(ring_id)
    db.update_user(str(ctx.author.id), inventory=inventory)
    
    await ctx.reply(embed=create_embed("💍 MUA NHẪN THÀNH CÔNG", f"✅ Bạn đã mua **{ring['name']}**!\nDùng `?marry give ring {ring_id}` để tặng cho bạn đời.", 0x00ff00))

@marry.command(name="give")
async def give_ring(ctx, type_str: str, ring_id: str):
    if type_str.lower() != "ring": return
    
    user = db.get_user(str(ctx.author.id))
    if not user or not user.get("married_to"):
        return await ctx.reply("❌ Bạn cần phải kết hôn để tặng nhẫn!")
    
    inventory = user.get("inventory", [])
    if ring_id not in inventory:
        return await ctx.reply("❌ Bạn không sở hữu nhẫn này trong kho!")
    
    partner_id = user["married_to"]
    partner = db.get_user(partner_id)
    
    # Remove from inventory and set as current ring for partner
    inventory.remove(ring_id)
    db.update_user(str(ctx.author.id), inventory=inventory)
    db.update_user(partner_id, ring=ring_id)
    
    ring = RINGS[ring_id]
    partner_user = await bot.fetch_user(int(partner_id))
    
    await ctx.send(embed=create_embed("🎁 TẶNG QUÀ KẾT HÔN", f"❤️ **{ctx.author.name}** đã tặng **{ring['name']}** cho **{partner_user.name}**!\n✨ *{ring['desc']}*", 0xff69b4, thumbnail=partner_user.display_avatar.url))

@bot.command()
async def divorce(ctx, member: discord.Member):
    user_data = db.get_user(str(ctx.author.id))
    if user_data and user_data.get("married_to") == str(member.id):
        db.update_user(str(ctx.author.id), married_to=None, ring=None)
        db.update_user(str(member.id), married_to=None, ring=None)
        await ctx.reply(embed=create_embed("💔 LY HÔN", f"😢 **{ctx.author.name}** và **{member.name}** đã chính thức ly hôn. Tiền thưởng hàng ngày trở lại **1x**.", 0x555555))
    else:
        await ctx.reply("❌ Bạn không kết hôn với người này!")

# ===== LOTTERY SYSTEM =====
LOTT_FILE = "lott.json"

def load_lott():
    if os.path.exists(LOTT_FILE):
        try:
            with open(LOTT_FILE, "r") as f: return json.load(f)
        except: pass
    return {"tickets": [], "end_time": None}

def save_lott(data):
    with open(LOTT_FILE, "w") as f: json.dump(data, f, indent=2)

@bot.group(aliases=["lott"], invoke_without_command=True)
async def lottery(ctx):
    data = load_lott()
    if not data["end_time"]:
        data["end_time"] = (get_now_utc7() + timedelta(days=1)).isoformat()
        save_lott(data)
    
    end_time = datetime.fromisoformat(data["end_time"])
    remaining = end_time - get_now_utc7()
    
    desc = f"🎟️ Tổng số vé đã mua: **{len(data['tickets'])}**\n⏰ Thời gian còn lại: **{str(remaining).split('.')[0]}**\n💰 Giá vé: **50,000** cash\n\nSử dụng `?lott buy` để mua vé!"
    await ctx.reply(embed=create_embed("🎫 XỔ SỐ KIẾN THIẾT", desc, 0xffaa00))

@lottery.command()
async def buy(ctx):
    user = db.get_user(str(ctx.author.id))
    if not user or (user['balance'] != "inf" and user['balance'] < 50000):
        return await ctx.reply("❌ Bạn không đủ 50,000 cash để mua vé!")
    
    if user['balance'] != "inf":
        db.update_user(str(ctx.author.id), balance=user['balance'] - 50000)
    
    ticket_id = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=7))
    data = load_lott()
    if not data["end_time"]: data["end_time"] = (get_now_utc7() + timedelta(days=1)).isoformat()
    
    data["tickets"].append({"user_id": str(ctx.author.id), "id": ticket_id})
    save_lott(data)
    
    end_time = datetime.fromisoformat(data["end_time"])
    remaining = end_time - get_now_utc7()
    
    await ctx.reply(embed=create_embed("🎫 MUA VÉ THÀNH CÔNG", f"✅ Bạn đã mua vé **{ticket_id}** với giá **50,000** cash!\n⏰ Kết quả sẽ có sau **{str(remaining).split('.')[0]}**", 0x00ff00))

@lottery.command()
async def shop(ctx):
    desc = "🏪 **Cửa Hàng Vé Số**\n\n🎟️ Vé số may mắn: **50,000** cash / vé\n🍀 Cơ hội trúng giải thưởng lên đến **1,000 tỷ**!\n\nSử dụng `?lott buy` để mua ngay!"
    await ctx.reply(embed=create_embed("🎫 LOTTERY SHOP", desc, 0xffaa00))

async def lottery_check_task():
    while True:
        await asyncio.sleep(60)
        data = load_lott()
        if not data["end_time"] or not data["tickets"]: continue
        
        end_time = datetime.fromisoformat(data["end_time"])
        if get_now_utc7() >= end_time:
            random.shuffle(data["tickets"])
            winners = data["tickets"][:10]
            
            desc = "🎊 **KẾT QUẢ XỔ SỐ ĐÃ CÓ!** 🎊\n\n"
            reward = 1_000_000_000_000
            
            for i, winner in enumerate(winners):
                user = db.get_user(winner['user_id'])
                if user:
                    if user['balance'] != "inf":
                        db.update_user(winner['user_id'], balance=user['balance'] + reward)
                    desc += f"{i+1}. **{winner['id']}**: `{reward:,}` Cash (<@{winner['user_id']}>)\n"
                reward = int(reward * 0.5)
            
            # Reset
            data = {"tickets": [], "end_time": (get_now_utc7() + timedelta(days=1)).isoformat()}
            save_lott(data)
            print("🎰 Lottery resolved!")

# ===== EVENTS =====
@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}!')
    bot.loop.create_task(auto_save_task())
    bot.loop.create_task(lottery_check_task())

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"❌ Lỗi: {error}")
    raise error

# ===== ADMIN COMMANDS =====
@bot.command()
@commands.has_permissions(administrator=True)
async def win(ctx, result: str):
    print(f"✨ Admin @{ctx.author.name} forced result to: {result.upper()}")
    result = result.lower()
    if result not in ["tai", "xiu"]:
        await ctx.reply("❌ Chọn `tai` hoặc `xiu`")
        return
    await end_game(ctx.channel, forced_result=result)

@bot.command()
@commands.has_permissions(administrator=True)
async def moneyhack(ctx, amount: str):
    user = db.get_user(str(ctx.author.id))
    if not user:
        user = db.create_user(str(ctx.author.id), ctx.author.name)
    
    if amount.lower() == "inf":
        db.update_user(str(ctx.author.id), balance="inf")
        print(f"🤑 Admin @{ctx.author.name} set balance to INF")
        await ctx.reply(embed=create_embed("🤑 Money Hack Successful", f"💹 Số dư hiện tại: **{format_balance('inf')}**", 0x00ff00))
    elif amount.lower() == "-inf":
        db.update_user(str(ctx.author.id), balance=0)
        print(f"🤑 Admin @{ctx.author.name} reset balance to 0")
        await ctx.reply(embed=create_embed("🤑 Money Hack Reset", f"💹 Số dư hiện tại: **0** cash", 0x00ff00))
    else:
        try:
            val = int(amount)
            new_balance = (0 if user['balance'] == "inf" else user['balance']) + val
            db.update_user(str(ctx.author.id), balance=new_balance)
            print(f"🤑 Admin @{ctx.author.name} used moneyhack: +{val:,}")
            await ctx.reply(embed=create_embed("🤑 Money Hack Successful", f"💰 Đã thêm **{val:,}** vào tài khoản của bạn.\n💹 Số dư mới: **{format_balance(new_balance)}**", 0x00ff00))
        except ValueError:
            await ctx.reply("❌ Số tiền không hợp lệ. Sử dụng `inf`, `-inf` hoặc một con số.")

@win.error
@moneyhack.error
async def admin_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=create_embed("❌ Lỗi Quyền Hạn", "🛡️ Bạn cần quyền **Administrator** để sử dụng lệnh này!", 0xff0000))

# ===== USER COMMANDS =====
@bot.command()
async def tx(ctx):
    if game.is_running:
        await ctx.reply(embed=create_embed("❌ Lỗi", "Game đang diễn ra!", 0xff0000))
        return
    print(f"🎲 @{ctx.author.name} started a new game!")
    await start_game(ctx)

@bot.command()
async def cuoc(ctx, choice: str, amount: str):
    if not game.is_running:
        await ctx.reply(embed=create_embed("❌ Lỗi", "Không có game nào đang diễn ra!", 0xff0000))
        return

    choice = choice.lower()
    if choice not in ["tai", "xiu"]:
        await ctx.reply(embed=create_embed("❌ Lỗi", "Vui lòng chọn `tai` hoặc `xiu`.", 0xff0000))
        return

    user = db.get_user(str(ctx.author.id))
    if not user:
        user = db.create_user(str(ctx.author.id), ctx.author.name)

    if amount.lower() == "all":
        if user['balance'] == "inf":
            return await ctx.reply(embed=create_embed("❌ Lỗi", "Bạn nhiều tiền đến nổi hệ thống bị ngu, deck đếm được số tiền này. Vui lòng thử lại với số tiền hợp lý!", 0xff0000))
        bet_amount = user['balance']
    else:
        try:
            bet_amount = int(amount.replace(",", "").replace(".", ""))
        except ValueError:
            await ctx.reply(embed=create_embed("❌ Lỗi", "Số tiền không hợp lệ.", 0xff0000))
            return

    if bet_amount <= 0:
        await ctx.reply(embed=create_embed("❌ Lỗi", "Số tiền phải lớn hơn 0.", 0xff0000))
        return

    if user['balance'] != "inf" and user['balance'] < bet_amount:
        await ctx.reply(embed=create_embed("❌ Lỗi", f"Bạn không đủ tiền! Số dư hiện tại: **{user['balance']:,}** cash", 0xff0000))
        return

    if user['balance'] != "inf":
        db.update_user(str(ctx.author.id), balance=user['balance'] - bet_amount)
    
    game.bets.append({
        'user_id': str(ctx.author.id),
        'username': ctx.author.name,
        'amount': bet_amount,
        'choice': choice
    })
    print(f"💸 @{ctx.author.name} bet {bet_amount:,} on {choice.upper()}")

    await ctx.reply(embed=create_embed("✅ Đặt cược thành công", f"👤 Người chơi: **{ctx.author.name}**\n💰 Số tiền: **{bet_amount:,}** cash\n🎯 Lựa chọn: **{choice.upper()}**\n\n🍀 Chúc bạn may mắn!", 0x00ff00, thumbnail=ctx.author.display_avatar.url))

@bot.command()
async def daily(ctx):
    user = db.get_user(str(ctx.author.id))
    if not user:
        user = db.create_user(str(ctx.author.id), ctx.author.name)

    now = get_now_utc7()
    last_daily = user.get('last_daily')
    
    if last_daily:
        if isinstance(last_daily, str):
            last_daily = datetime.fromisoformat(last_daily)
        if last_daily.tzinfo is None:
            last_daily = last_daily.replace(tzinfo=UTC7)
        else:
            last_daily = last_daily.astimezone(UTC7)

    if last_daily and last_daily.date() == now.date():
        await ctx.reply(embed=create_embed("❌ Lỗi", "Bạn đã nhận thưởng hôm nay rồi!", 0xff0000))
        return

    streak = user['daily_streak'] + 1 if last_daily and last_daily.date() == (now - timedelta(days=1)).date() else 1
    reward = get_daily_reward(streak)
    
    # Marriage bonus 1.5x
    if user.get("married_to"):
        reward = int(reward * 1.5)
    
    if user['balance'] != "inf":
        db.update_user(str(ctx.author.id), balance=user['balance'] + reward, daily_streak=streak, last_daily=now.isoformat())
    else:
        db.update_user(str(ctx.author.id), daily_streak=streak, last_daily=now.isoformat())
        
    print(f"🎁 User @{ctx.author.name} claimed their daily reward successfully!")
    await ctx.reply(embed=create_embed("📅 Điểm danh hàng ngày", f"✨ Chúc mừng **{ctx.author.name}**!\n💰 Phần thưởng: **{reward:,}** cash\n🔥 Chuỗi hiện tại: **{streak} ngày**\n\n*Hãy quay lại vào ngày mai nhé!*", 0x00ff00, thumbnail=ctx.author.display_avatar.url))

@bot.command(aliases=["cash"])
async def money(ctx):
    user = db.get_user(str(ctx.author.id))
    if not user:
        user = db.create_user(str(ctx.author.id), ctx.author.name)
    print(f"💰 @{ctx.author.name} checked balance: {user['balance']}")
    await ctx.reply(embed=create_embed("💰 Tài khoản cá nhân", f"👤 Người sở hữu: **{ctx.author.name}**\n💵 Số dư: **{format_balance(user['balance'])}**\n\n🏆 Hạng hiện tại: *Sử dụng `?top` để xem*", 0xffff00, thumbnail=ctx.author.display_avatar.url))

@bot.command()
async def top(ctx):
    top_users = db.get_top_users(10)
    description = "🏆 **Bảng Xếp Hạng Đại Gia** 🏆\n\n"
    description += "\n".join([f"{i+1}. 👤 **{u['username']}**: `{format_balance(u['balance'])}`" for i, u in enumerate(top_users)])
    await ctx.send(embed=create_embed("🏆 Top 10 Bảng Xếp Hạng", description, 0xffd700))

@bot.command()
async def txstop(ctx):
    if not game.is_running:
        await ctx.reply(embed=create_embed("❌ Lỗi", "Không có game nào đang diễn ra!", 0xff0000))
        return
    print(f"🛑 @{ctx.author.name} stopped the game!")
    await end_game(ctx.channel)

@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.reply("❌ Số tiền không hợp lệ.")
        return

    sender = db.get_user(str(ctx.author.id))
    if not sender or (sender['balance'] != "inf" and sender['balance'] < amount):
        await ctx.reply("❌ Bạn không đủ tiền!")
        return

    receiver = db.get_user(str(member.id))
    if not receiver:
        receiver = db.create_user(str(member.id), member.name)

    if sender['balance'] != "inf":
        db.update_user(str(ctx.author.id), balance=sender['balance'] - amount)
    
    if receiver['balance'] != "inf":
        db.update_user(str(member.id), balance=receiver['balance'] + amount)
        
    print(f"💸 @{ctx.author.name} gave {amount:,} to @{member.name}")
    await ctx.reply(embed=create_embed("✅ Chuyển tiền thành công", f"👤 Từ: **{ctx.author.name}**\n👤 Đến: **{member.name}**\n💰 Số tiền: **{amount:,}** cash", 0x00ff00, thumbnail=ctx.author.display_avatar.url))

@bot.command()
async def txtt(ctx):
    game.auto_restart = not game.auto_restart
    status = "**BẬT**" if game.auto_restart else "**TẮT**"
    color = 0x00ff00 if game.auto_restart else 0xff0000
    print(f"🔄 @{ctx.author.name} toggled auto-restart: {status}")
    await ctx.reply(embed=create_embed("🔄 Chế độ Auto Restart", f"Chế độ tự động bắt đầu game mới đã: {status}", color))
    if game.auto_restart and not game.is_running:
        await start_game(ctx)

@bot.command(aliases=["pf", "info"])
async def profile(ctx, member: discord.Member = None):
    target = member or ctx.author
    user = db.get_user(str(target.id))
    if not user:
        user = db.create_user(str(target.id), target.name)
    
    married_id = user.get("married_to")
    married_text = "Chưa kết hôn"
    if married_id:
        try:
            married_user = await bot.fetch_user(int(married_id))
            ring_id = user.get("ring")
            ring_text = ""
            if ring_id and ring_id in RINGS:
                ring_text = f" (💍 {RINGS[ring_id]['name']})"
            married_text = f"💍 Đã kết hôn với **{married_user.name}**{ring_text}"
        except:
            married_text = "💍 Đã kết hôn"
    
    wins = user.get("wins", 0)
    losses = user.get("losses", 0)
    total_bet = user.get("total_bet", 0)
    
    desc = (
        f"💵 Số dư: **{format_balance(user['balance'])}**\n"
        f"🔥 Chuỗi điểm danh: **{user['daily_streak']}** ngày\n"
        f"{married_text}\n\n"
        f"📊 **Thống kê chơi game:**\n"
        f"✅ Thắng: **{wins}**\n"
        f"❌ Thua: **{losses}**\n"
        f"💰 Tổng cược: **{total_bet:, if isinstance(total_bet, int) else total_bet}** cash"
    )
    
    await ctx.reply(embed=create_embed(f"👤 Hồ sơ của {target.name}", desc, 0x00aaff, thumbnail=target.display_avatar.url))

@bot.command()
async def steal(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.reply("❌ Bạn không thể tự trộm chính mình!")
    
    stealer_data = db.get_user(str(ctx.author.id))
    target_data = db.get_user(str(member.id))
    
    if not stealer_data: stealer_data = db.create_user(str(ctx.author.id), ctx.author.name)
    if not target_data: target_data = db.create_user(str(member.id), member.name)
    
    if target_data['balance'] == 0:
        return await ctx.reply("❌ Đối phương không có tiền để trộm!")
    
    chance = random.random()
    if chance <= 0.01:
        stolen_amount = 999999999999 if target_data['balance'] == "inf" else target_data['balance']
        if stealer_data['balance'] != "inf":
            db.update_user(str(ctx.author.id), balance=stealer_data['balance'] + stolen_amount)
        db.update_user(str(member.id), balance=0)
        await ctx.reply(embed=create_embed("🥷 TRỘM THÀNH CÔNG!", f"😱 Bạn đã trộm thành công **{format_balance(stolen_amount)}** từ **{member.name}**!", 0x00ff00, thumbnail=ctx.author.display_avatar.url))
    else:
        penalty = 0 if stealer_data['balance'] == "inf" else int(stealer_data['balance'] * 0.5)
        if stealer_data['balance'] != "inf":
            db.update_user(str(ctx.author.id), balance=stealer_data['balance'] - penalty)
        await ctx.reply(embed=create_embed("👮 TRỘM THẤT BẠI!", f"🚔 Bạn đã bị bắt! Phạt **50%** tài sản (**{penalty:,}** cash).", 0xff0000, thumbnail=ctx.author.display_avatar.url))

@bot.command(name="help")
async def help_cmd(bot_ctx):
    help_text = (
        "🎮 **Lệnh Trò Chơi**\n"
        "`?tx`: Bắt đầu ván Tài Xỉu\n"
        "`?cuoc <tai|xiu> <amount>`: Đặt cược\n"
        "`?txstop`: Dừng ván game hiện tại\n"
        "`?txtt`: Bật/Tắt chế độ tự động bắt đầu\n\n"
        "💰 **Lệnh Kinh Tế**\n"
        "`?daily`: Nhận thưởng hàng ngày\n"
        "`?money`: Xem số dư hiện có\n"
        "`?top`: Xem bảng xếp hạng đại gia\n"
        "`?give @user <amount>`: Chuyển tiền cho bạn bè\n"
        "`?pf`: Xem hồ sơ cá nhân\n"
        "`?steal @user`: Thử vận may trộm tiền\n\n"
        "💍 **Hôn Nhân**\n"
        "`?marry @user`: Cầu hôn\n"
        "`?marry accept/decline`: Chấp nhận/Từ chối\n"
        "`?marry shop`: Cửa hàng nhẫn\n"
        "`?marry buy <id>`: Mua nhẫn\n"
        "`?marry give ring <id>`: Tặng nhẫn cho vợ/chồng\n"
        "`?divorce @user`: Ly hôn\n\n"
        "🎟️ **Xổ Số**\n"
        "`?lott`: Xem thông tin xổ số\n"
        "`?lott buy`: Mua vé (50k)\n"
        "`?lott shop`: Xem cửa hàng vé số\n\n"
        "🎰 **Trò Chơi Khác**\n"
        "`?blackjack <amount>`: Chơi Blackjack\n"
        "`?coinflip <1|2> <amount>`: Tung đồng xu\n"
        "`?slots <amount>`: Quay Slot\n"
    )
    await bot_ctx.send(embed=create_embed("📜 Danh Sách Lệnh TaixiuBot", help_text, 0x0099ff))

# ===== BLACKJACK LOGIC =====
CARD_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}
SUITS = ['♣️', '♦️', '♥️', '♠️']
CARDS = list(CARD_VALUES.keys())

def get_random_card():
    card = random.choice(CARDS)
    suit = random.choice(SUITS)
    return f"{card}{suit}"

def get_card_value(card_str):
    val_part = card_str.replace('♣️','').replace('♦️','').replace('♥️','').replace('♠️','')
    return CARD_VALUES[val_part]

def calculate_hand(hand):
    value = sum(get_card_value(card) for card in hand)
    aces = sum(1 for card in hand if card.startswith('A'))
    while value > 21 and aces > 0:
        value -= 10
        aces -= 1
    return value

def check_special_win(hand):
    if len(hand) == 2:
        aces = sum(1 for card in hand if card.startswith('A'))
        if aces == 2:
            return "Xì bàng"
        if aces == 1:
            other_card = hand[0] if not hand[0].startswith('A') else hand[1]
            if get_card_value(other_card) == 10:
                return "Xì jack"
    if len(hand) == 5 and calculate_hand(hand) <= 21:
        return "Ngũ linh"
    return None

def format_hand(hand):
    return ", ".join(hand)

class BlackjackView(ui.View):
    def __init__(self, ctx, bet, player_hand, dealer_hand):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.bet = bet
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.ended = False

    async def end_game(self, interaction, title, description, color):
        self.ended = True
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True
        
        # Dealer must hit until 17 or special win even if player busted or stood
        while calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(get_random_card())
            if check_special_win(self.dealer_hand):
                break

        embed = create_embed(title, description, color)
        embed.add_field(name="Nhà cái", value=f"{format_hand(self.dealer_hand)} (Tổng: {calculate_hand(self.dealer_hand)})", inline=True)
        embed.add_field(name=self.ctx.author.name, value=f"{format_hand(self.player_hand)} (Tổng: {calculate_hand(self.player_hand)})", inline=True)
        
        if interaction.message:
            await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Bốc (Hit)", style=discord.ButtonStyle.green, emoji="➕")
    async def hit(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Đây không phải ván bài của bạn!", ephemeral=True)
        
        if len(self.player_hand) >= 5:
            return await interaction.response.send_message("Bạn đã bốc tối đa 5 lá!", ephemeral=True)

        self.player_hand.append(get_random_card())
        player_value = calculate_hand(self.player_hand)
        special = check_special_win(self.player_hand)
        
        if special == "Ngũ linh":
            if db.get_user(str(self.ctx.author.id))['balance'] != "inf":
                win_amount = self.bet * 2
                db.update_user(str(self.ctx.author.id), balance=db.get_user(str(self.ctx.author.id))['balance'] + win_amount)
            db.update_stats(str(self.ctx.author.id), True, self.bet)
            await self.end_game(interaction, "🎉 THẮNG!", f"Bạn đã thắng vì **Ngũ linh**, sigma! Nhận được **{self.bet * 2:,}** cash!", 0x00ff00)
        elif player_value > 21:
            db.update_stats(str(self.ctx.author.id), False, self.bet)
            await self.end_game(interaction, "💥 QUÁ 21 (BUST)!", f"Bạn đã bốc quá 21 và thua **{self.bet:,}** cash!", 0xff0000)
        else:
            if interaction.message and interaction.message.embeds:
                embed = interaction.message.embeds[0]
                embed.set_field_at(1, name=self.ctx.author.name, value=f"{format_hand(self.player_hand)} (Tổng: {player_value})", inline=True)
                await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Dằn (Stand)", style=discord.ButtonStyle.red, emoji="✋")
    async def stand(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Đây không phải ván bài của bạn!", ephemeral=True)
        
        player_value = calculate_hand(self.player_hand)
        player_special = check_special_win(self.player_hand)
        
        # We don't call end_game immediately here, we resolve the dealer first
        # But end_game now handles dealer logic, so we just calculate final result
        
        # Final dealer resolve
        while calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(get_random_card())
            if check_special_win(self.dealer_hand):
                break
        
        dealer_value = calculate_hand(self.dealer_hand)
        dealer_special = check_special_win(self.dealer_hand)
        
        user_data = db.get_user(str(self.ctx.author.id))
        current_balance = user_data['balance'] if user_data else 0
        
        player_is_non = player_value < 15 and not player_special
        dealer_is_non = dealer_value < 15 and not dealer_special

        # Resolve win/loss
        win = False
        push = False
        
        if player_is_non and dealer_is_non:
            push = True
        elif player_is_non:
            win = False
        elif dealer_is_non:
            win = True
        elif dealer_special and not player_special:
            win = False
        elif player_special and not dealer_special:
            win = True
        elif dealer_value > 21:
            win = True
        elif player_value > dealer_value:
            win = True
        elif player_value == dealer_value:
            push = True
        else:
            win = False

        if push:
            if current_balance != "inf":
                db.update_user(str(self.ctx.author.id), balance=current_balance + self.bet)
            msg = "Cả hai đều chưa đủ 15 điểm (NON)!" if (player_is_non and dealer_is_non) else "Điểm bằng nhau!"
            await self.end_game(interaction, "🤝 HÒA (PUSH)!", f"{msg} Bạn được hoàn lại **{self.bet:,}** cash!", 0xffff00)
        elif win:
            win_amount = self.bet * 2
            if current_balance != "inf":
                db.update_user(str(self.ctx.author.id), balance=current_balance + win_amount)
            db.update_stats(str(self.ctx.author.id), True, self.bet)
            if dealer_is_non:
                msg = "Nhà cái chưa đủ 15 điểm (NON)!"
            else:
                msg = f"Bạn đã thắng vì **{player_special}**" if player_special else "Bạn cao điểm hơn nhà cái!"
            await self.end_game(interaction, "🎉 THẮNG!", f"{msg} Nhận được **{win_amount:,}** cash!", 0x00ff00)
        else:
            db.update_stats(str(self.ctx.author.id), False, self.bet)
            if player_is_non:
                msg = "Bạn chưa đủ 15 điểm (NON)!"
            else:
                msg = f"Nhà cái đã thắng vì **{dealer_special}**" if dealer_special else "Điểm của bạn thấp hơn nhà cái!"
            await self.end_game(interaction, "💀 THUA!", f"{msg} Mất **{self.bet:,}** cash!", 0xff0000)

@bot.command(aliases=["bj"])
async def blackjack(ctx, amount: str):
    user = db.get_user(str(ctx.author.id))
    if not user:
        user = db.create_user(str(ctx.author.id), ctx.author.name)

    if amount.lower() == "all":
        if user['balance'] == "inf":
            return await ctx.reply(embed=create_embed("❌ Lỗi", "Bạn nhiều tiền đến nổi hệ thống bị ngu, deck đếm được số tiền này. Vui lòng thử lại với số tiền hợp lý!", 0xff0000))
        bet = user['balance']
    else:
        try:
            bet = int(amount.replace(",", "").replace(".", ""))
        except ValueError:
            return await ctx.reply("❌ Số tiền không hợp lệ.")

    if (bet <= 0 or (user['balance'] != "inf" and user['balance'] < bet)):
        return await ctx.reply(f"❌ Bạn không đủ tiền! Số dư: **{format_balance(user['balance'])}** cash")

    if user['balance'] != "inf":
        db.update_user(str(ctx.author.id), balance=user['balance'] - bet)
    
    player_hand = [get_random_card(), get_random_card()]
    dealer_hand = [get_random_card(), get_random_card()]
    
    player_special = check_special_win(player_hand)
    dealer_special = check_special_win(dealer_hand)

    if player_special or dealer_special:
        user_data = db.get_user(str(ctx.author.id))
        current_balance = user_data['balance'] if user_data else 0
        
        if dealer_special and not player_special:
            msg = f"Nhà cái đã thắng vì **{dealer_special}**, "
            msg += "haha!" if dealer_special == "Xì bàng" else "gà!"
            db.update_stats(str(ctx.author.id), False, bet)
            embed = create_embed("💀 THUA!", f"Nhà cái lật bài: {format_hand(dealer_hand)}\n{msg} Mất **{bet:,}** cash!", 0xff0000, thumbnail=ctx.author.display_avatar.url)
            return await ctx.send(embed=embed)
        elif player_special:
            win_amount = bet * 2
            if current_balance != "inf":
                db.update_user(str(ctx.author.id), balance=current_balance + win_amount)
            db.update_stats(str(ctx.author.id), True, bet)
            msg = f"Bạn đã thắng vì **{player_special}**, "
            msg += "ez!" if player_special == "Xì bàng" else "gg!"
            embed = create_embed("🎉 THẮNG!", f"Bạn đã có: {format_hand(player_hand)}\n{msg} Nhận được **{win_amount:,}** cash!", 0x00ff00, thumbnail=ctx.author.display_avatar.url)
            return await ctx.send(embed=embed)

    embed = create_embed("🃏 BLACKJACK", f"@{ctx.author.name}, Bạn đã cược **{bet:,}** vào ván bài!", 0x0099ff, thumbnail=ctx.author.display_avatar.url)
    embed.add_field(name="Nhà cái", value=f"{dealer_hand[0]}, ???", inline=True)
    embed.add_field(name=ctx.author.name, value=f"{format_hand(player_hand)} (Tổng: {calculate_hand(player_hand)})", inline=True)
    
    view = BlackjackView(ctx, bet, player_hand, dealer_hand)
    await ctx.send(embed=embed, view=view)

# ===== NEW COMMANDS =====
@bot.command()
async def ok(ctx, member: discord.Member):
    await ctx.send(f"{ctx.author.mention} giơ ngón cái với {member.mention} 👍")

@bot.command()
async def cc(ctx, member: discord.Member):
    insults = [
        "địt mẹ mày con chó", "loz cek dcm", "đồ óc chó", "cút mẹ mày đi",
        "mày là cái thá gì", "ăn cức đi con"
    ]
    await ctx.send(f"{member.mention} {random.choice(insults)}")

@bot.command()
async def fuck(ctx, member: discord.Member):
    actions = [
        "đang làm gì đó mờ ám với", "đang thông đít", "đang hành hạ",
        "đang ôm ấp nồng cháy với"
    ]
    await ctx.send(f"{ctx.author.mention} {random.choice(actions)} {member.mention} 🔞")

# ===== MAIN LOOP =====
async def main():
    while True:
        try:
            await bot.start(TOKEN)
        except discord.errors.HTTPException as e:
            if e.status == 429:
                wait_time = int(e.response.headers.get("Retry-After", 60))
                print(f"⚠️ Rate limited. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                raise e
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
