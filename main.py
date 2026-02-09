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
            print("💾 Saved data.json")
        except Exception as e:
            print(f"❌ Failed to save data.json: {e}")

    def get_user(self, user_id):
        return self.data.get("users", {}).get(user_id)

    def create_user(self, user_id, username):
        user = {
            "username": username,
            "balance": 1000,
            "daily_streak": 0,
            "last_daily": None
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

    def get_top_users(self, limit=10):
        users = list(self.data.get("users", {}).values())
        users.sort(key=lambda u: u.get("balance", 0), reverse=True)
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

def create_embed(title, description, color=0x0099ff):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.timestamp = get_now_utc7()
    return embed

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
            win_amount = bet['amount'] * 2
            db.update_user(bet['user_id'], balance=user['balance'] + win_amount)
            winners.append(f"👤 **{bet['username']}**: +{bet['amount']:,} cash")
        else:
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

# ===== EVENTS =====
@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}!')
    bot.loop.create_task(auto_save_task())

@bot.event
async def on_command_error(ctx, error):
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
async def moneyhack(ctx, amount: int):
    user = db.get_user(str(ctx.author.id))
    if not user:
        user = db.create_user(str(ctx.author.id), ctx.author.name)
    
    new_balance = user['balance'] + amount
    db.update_user(str(ctx.author.id), balance=new_balance)
    print(f"🤑 Admin @{ctx.author.name} used moneyhack: +{amount:,}")
    await ctx.reply(embed=create_embed("🤑 Money Hack Successful", f"💰 Đã thêm **{amount:,}** vào tài khoản của bạn.\n💹 Số dư mới: **{new_balance:,}** cash", 0x00ff00))

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

    user = db.get_user(str(ctx.author.id))
    if not user or user['balance'] < bet_amount:
        current_balance = user['balance'] if user else 0
        await ctx.reply(embed=create_embed("❌ Lỗi", f"Bạn không đủ tiền! Số dư hiện tại: **{current_balance:,}** cash", 0xff0000))
        return

    new_balance = user['balance'] - bet_amount
    db.update_user(str(ctx.author.id), balance=new_balance)
    game.bets.append({
        'user_id': str(ctx.author.id),
        'username': ctx.author.name,
        'amount': bet_amount,
        'choice': choice
    })
    print(f"💸 @{ctx.author.name} bet {bet_amount:,} on {choice.upper()}")

    await ctx.reply(embed=create_embed("✅ Đặt cược thành công", f"👤 Người chơi: **{ctx.author.name}**\n💰 Số tiền: **{bet_amount:,}** cash\n🎯 Lựa chọn: **{choice.upper()}**\n\n🍀 Chúc bạn may mắn!", 0x00ff00))

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
    new_balance = user['balance'] + reward
    
    db.update_user(str(ctx.author.id), balance=new_balance, daily_streak=streak, last_daily=now.isoformat())
    print(f"🎁 User @{ctx.author.name} claimed their daily reward successfully!")
    await ctx.reply(embed=create_embed("📅 Điểm danh hàng ngày", f"✨ Chúc mừng **{ctx.author.name}**!\n💰 Phần thưởng: **{reward:,}** cash\n🔥 Chuỗi hiện tại: **{streak} ngày**\n\n*Hãy quay lại vào ngày mai nhé!*", 0x00ff00))

@bot.command(aliases=["cash"])
async def money(ctx):
    user = db.get_user(str(ctx.author.id))
    if not user:
        user = db.create_user(str(ctx.author.id), ctx.author.name)
    print(f"💰 @{ctx.author.name} checked balance: {user['balance']:,}")
    await ctx.reply(embed=create_embed("💰 Tài khoản cá nhân", f"👤 Người sở hữu: **{ctx.author.name}**\n💵 Số dư: **{user['balance']:,}** cash\n\n🏆 Hạng hiện tại: *Sử dụng `?top` để xem*", 0xffff00))

@bot.command()
async def top(ctx):
    top_users = db.get_top_users(10)
    description = "🏆 **Bảng Xếp Hạng Đại Gia** 🏆\n\n"
    description += "\n".join([f"{i+1}. 👤 **{u['username']}**: `{u['balance']:,}` cash" for i, u in enumerate(top_users)])
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
    if not sender or sender['balance'] < amount:
        await ctx.reply("❌ Bạn không đủ tiền!")
        return

    receiver = db.get_user(str(member.id))
    if not receiver:
        receiver = db.create_user(str(member.id), member.name)

    new_sender_balance = sender['balance'] - amount
    new_receiver_balance = receiver['balance'] + amount

    db.update_user(str(ctx.author.id), balance=new_sender_balance)
    db.update_user(str(member.id), balance=new_receiver_balance)
    print(f"💸 @{ctx.author.name} gave {amount:,} to @{member.name}")
    await ctx.reply(embed=create_embed("✅ Chuyển tiền thành công", f"👤 Từ: **{ctx.author.name}**\n👤 Đến: **{member.name}**\n💰 Số tiền: **{amount:,}** cash", 0x00ff00))

@bot.command()
async def txtt(ctx):
    game.auto_restart = not game.auto_restart
    status = "**BẬT**" if game.auto_restart else "**TẮT**"
    color = 0x00ff00 if game.auto_restart else 0xff0000
    print(f"🔄 @{ctx.author.name} toggled auto-restart: {status}")
    await ctx.reply(embed=create_embed("🔄 Chế độ Auto Restart", f"Chế độ tự động bắt đầu game mới đã: {status}", color))
    if game.auto_restart and not game.is_running:
        await start_game(ctx)

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
    )
    await bot_ctx.send(embed=create_embed("📜 Danh Sách Lệnh TaixiuBot", help_text, 0x0099ff))

# ===== BLACKJACK LOGIC =====
CARD_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}
CARDS = list(CARD_VALUES.keys())

def calculate_hand(hand):
    value = sum(CARD_VALUES[card] for card in hand)
    aces = hand.count('A')
    while value > 21 and aces > 0:
        value -= 10
        aces -= 1
    return value

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
        
        embed = create_embed(title, description, color)
        embed.add_field(name="Nhà cái", value=f"{self.dealer_hand} (Tổng: {calculate_hand(self.dealer_hand)})", inline=True)
        embed.add_field(name=self.ctx.author.name, value=f"{self.player_hand} (Tổng: {calculate_hand(self.player_hand)})", inline=True)
        
        if interaction.message:
            await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Bốc (Hit)", style=discord.ButtonStyle.green, emoji="➕")
    async def hit(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Đây không phải ván bài của bạn!", ephemeral=True)
        
        self.player_hand.append(random.choice(CARDS))
        player_value = calculate_hand(self.player_hand)
        
        if player_value > 21:
            await self.end_game(interaction, "💥 QUÁ 21 (BUST)!", f"Bạn đã bốc quá 21 và thua **{self.bet:,}** cash!", 0xff0000)
        else:
            if interaction.message and interaction.message.embeds:
                embed = interaction.message.embeds[0]
                embed.set_field_at(1, name=self.ctx.author.name, value=f"{self.player_hand} (Tổng: {player_value})", inline=True)
                await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Dằn (Stand)", style=discord.ButtonStyle.red, emoji="✋")
    async def stand(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Đây không phải ván bài của bạn!", ephemeral=True)
        
        while calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(random.choice(CARDS))
        
        dealer_value = calculate_hand(self.dealer_hand)
        player_value = calculate_hand(self.player_hand)
        
        user_data = db.get_user(str(self.ctx.author.id))
        current_balance = user_data['balance'] if user_data else 0
        
        if dealer_value > 21:
            win_amount = self.bet * 2
            db.update_user(str(self.ctx.author.id), balance=current_balance + win_amount)
            await self.end_game(interaction, "🎉 THẮNG!", f"Nhà cái BUST! Bạn nhận được **{win_amount:,}** cash!", 0x00ff00)
        elif player_value > dealer_value:
            win_amount = self.bet * 2
            db.update_user(str(self.ctx.author.id), balance=current_balance + win_amount)
            await self.end_game(interaction, "🎉 THẮNG!", f"Bạn cao điểm hơn nhà cái! Nhận được **{win_amount:,}** cash!", 0x00ff00)
        elif player_value == dealer_value:
            db.update_user(str(self.ctx.author.id), balance=current_balance + self.bet)
            await self.end_game(interaction, "🤝 HÒA (PUSH)!", f"Điểm bằng nhau! Bạn được hoàn lại **{self.bet:,}** cash!", 0xffff00)
        else:
            await self.end_game(interaction, "💀 THUA!", f"Điểm của bạn thấp hơn nhà cái! Mất **{self.bet:,}** cash!", 0xff0000)

@bot.command(aliases=["bj"])
async def blackjack(ctx, amount: str):
    user = db.get_user(str(ctx.author.id))
    if not user:
        user = db.create_user(str(ctx.author.id), ctx.author.name)

    if amount.lower() == "all":
        bet = user['balance']
    else:
        try:
            bet = int(amount.replace(",", "").replace(".", ""))
        except ValueError:
            return await ctx.reply("❌ Số tiền không hợp lệ.")

    if bet <= 0 or user['balance'] < bet:
        return await ctx.reply(f"❌ Bạn không đủ tiền! Số dư: **{user['balance']:,}** cash")

    db.update_user(str(ctx.author.id), balance=user['balance'] - bet)
    
    player_hand = [random.choice(CARDS), random.choice(CARDS)]
    dealer_hand = [random.choice(CARDS), random.choice(CARDS)]
    
    embed = create_embed("🃏 BLACKJACK", f"@{ctx.author.name}, Bạn đã cược **{bet:,}** vào game!", 0x0099ff)
    embed.add_field(name="Nhà cái", value=f"[{dealer_hand[0]}, ???]", inline=True)
    embed.add_field(name=ctx.author.name, value=f"{player_hand} (Tổng: {calculate_hand(player_hand)})", inline=True)
    
    view = BlackjackView(ctx, bet, player_hand, dealer_hand)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.reply(embed=create_embed("🏓 PONG!", f"Bot đang online!\n📶 Độ trễ: **{latency}ms**", 0x00ff00))

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
