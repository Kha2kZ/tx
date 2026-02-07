import os
import random
import asyncio
import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from db_manager import db
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("No DISCORD_TOKEN found in environment variables.")
    exit(1)

# UTC-7 Timezone
UTC7 = timezone(timedelta(hours=-7))

def get_now_utc7():
    return datetime.now(timezone.utc).astimezone(UTC7)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

class GameState:
    def __init__(self):
        self.is_running: bool = False
        self.end_time: datetime | None = None
        self.bets: list = []
        self.channel_id: int | None = None
        self.auto_restart: bool = False

game = GameState()

DAILY_REWARDS = [1000, 2000, 5000, 10000, 15000, 20000, 50000, 100000, 150000, 200000, 500000, 1000000]

def get_daily_reward(day):
    if day <= 12:
        return DAILY_REWARDS[day - 1]
    return 1000000 + (day - 12) * 500000

def create_embed(title, description, color=0x0099ff):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.timestamp = get_now_utc7()
    return embed

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

# Auto-save task
async def auto_save_task():
    while True:
        await asyncio.sleep(5)
        db.save_data()

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}!')
    bot.loop.create_task(auto_save_task())

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
            # Handle potential commas or dots in amount string if any
            bet_amount = int(amount.replace(",", "").replace(".", ""))
        except ValueError:
            await ctx.reply(embed=create_embed("❌ Lỗi", "Số tiền không hợp lệ.", 0xff0000))
            return

    if bet_amount <= 0:
        await ctx.reply(embed=create_embed("❌ Lỗi", "Số tiền phải lớn hơn 0.", 0xff0000))
        return

    # Re-fetch user to ensure balance is up to date before checking
    user = db.get_user(str(ctx.author.id))
    if user['balance'] < bet_amount:
        await ctx.reply(embed=create_embed("❌ Lỗi", f"Bạn không đủ tiền! Số dư hiện tại: **{user['balance']:,}** cash", 0xff0000))
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
