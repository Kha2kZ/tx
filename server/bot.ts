import { Client, GatewayIntentBits, EmbedBuilder, TextChannel, ButtonBuilder, ActionRowBuilder, ButtonStyle, ComponentType } from "discord.js";
import { storage } from "./storage";

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

interface Bet {
  userId: string;
  username: string;
  amount: number;
  choice: "tai" | "xiu";
}

interface GameState {
  isRunning: boolean;
  endTime: number | null;
  bets: Bet[];
  channelId: string | null;
  timer: NodeJS.Timeout | null;
  autoRestart: boolean;
}

let gameState: GameState = {
  isRunning: false,
  endTime: null,
  bets: [],
  channelId: null,
  timer: null,
  autoRestart: false,
};

const DAILY_REWARDS = [1000, 2000, 5000, 10000, 15000, 20000, 50000, 100000, 150000, 200000, 500000, 1000000];

function getDailyReward(day: number): number {
  if (day <= 12) return DAILY_REWARDS[day - 1];
  return 1000000 + (day - 12) * 500000;
}

function createEmbed(title: string, description: string, color: any = 0x0099ff) {
  return new EmbedBuilder()
    .setTitle(title)
    .setDescription(description)
    .setColor(color)
    .setTimestamp();
}

async function startGame(channel: TextChannel) {
    if (gameState.isRunning) return;

    gameState.isRunning = true;
    gameState.channelId = channel.id;
    gameState.endTime = Date.now() + 30000;
    gameState.bets = [];

    await channel.send({ embeds: [createEmbed("🎲 GAME TÀI XỈU BẮT ĐẦU!", "⏳ Thời gian cược: **30 giây**\nSử dụng lệnh `?cuoc <tai|xiu> <amount>` để tham gia.", 0x00ff00)] });

    gameState.timer = setTimeout(() => {
        endGame();
    }, 30000);
}

async function endGame(forcedResult?: "tai" | "xiu") {
  if (!gameState.isRunning || !gameState.channelId) return;

  if (gameState.timer) clearTimeout(gameState.timer);
  gameState.isRunning = false;

  const channel = client.channels.cache.get(gameState.channelId) as TextChannel;
  if (!channel) return;

  const dice1 = Math.floor(Math.random() * 6) + 1;
  const dice2 = Math.floor(Math.random() * 6) + 1;
  const dice3 = Math.floor(Math.random() * 6) + 1;
  const total = dice1 + dice2 + dice3;
  
  let result: "tai" | "xiu";
  
  if (forcedResult) {
    result = forcedResult;
  } else {
    // 3-10: Xiu, 11-18: Tai
    result = total >= 11 ? "tai" : "xiu";
  }

  const resultEmoji = result === "tai" ? "🔴 TÀI" : "⚪ XỈU";
  
  let description = `🎲 Kết quả: **${dice1} - ${dice2} - ${dice3}** (Tổng: ${total})\n🏆 Chiến thắng: **${resultEmoji}**\n\n`;
  
  const winners: string[] = [];
  const losers: string[] = [];

  for (const bet of gameState.bets) {
    const user = await storage.getUser(bet.userId);
    if (!user) continue;

    if (bet.choice === result) {
      const winAmount = bet.amount * 2; 
      await storage.updateUser(bet.userId, { balance: user.balance + winAmount }); 
      winners.push(`**${bet.username}**: +${bet.amount.toLocaleString()} cash`);
    } else {
      losers.push(`**${bet.username}**: -${bet.amount.toLocaleString()} cash`);
    }
  }

  if (winners.length > 0) description += `🎉 **Người thắng:**\n${winners.join("\n")}\n\n`;
  else description += `😢 **Không có người thắng.**\n\n`;
  
  if (losers.length > 0) description += `💀 **Người thua:**\n${losers.join("\n")}`;

  await channel.send({ embeds: [createEmbed("🏁 KẾT THÚC GAME TÀI XỈU", description, result === "tai" ? 0xff0000 : 0xeeeeee)] });
  
  // Reset state variables
  gameState.isRunning = false;
  gameState.endTime = null;
  gameState.bets = [];
  gameState.timer = null;

  // Auto Restart Logic
  if (gameState.autoRestart) {
      channel.send({ embeds: [createEmbed("🔄 Auto Restart", "Game mới sẽ bắt đầu sau 10 giây...", 0xffff00)] });
      setTimeout(() => {
          startGame(channel);
      }, 10000);
  }
}

client.on("ready", () => {
  console.log(`Logged in as ${client.user?.tag}!`);
});

client.on("messageCreate", async (message) => {
  if (message.author.bot) return;
  if (!message.content.startsWith("?")) return;

  const args = message.content.slice(1).trim().split(/ +/);
  const command = args.shift()?.toLowerCase();

  let user = await storage.getUser(message.author.id);
  if (!user) {
    user = await storage.createUser({
      discordId: message.author.id,
      username: message.author.username,
      balance: 0,
      dailyStreak: 0,
      isAdmin: false
    });
  } else if (user.username !== message.author.username) {
    await storage.updateUser(message.author.id, { username: message.author.username });
  }

  if (command === "tx") {
    if (gameState.isRunning) {
      return message.reply({ embeds: [createEmbed("❌ Lỗi", "Game đang diễn ra!", 0xff0000)] });
    }
    startGame(message.channel as TextChannel);
  }

  else if (command === "cuoc") {
    if (!gameState.isRunning) {
      return message.reply({ embeds: [createEmbed("❌ Lỗi", "Không có game nào đang diễn ra!", 0xff0000)] });
    }

    const choice = args[0]?.toLowerCase();
    const amountStr = args[1];

    if (!choice || !["tai", "xiu"].includes(choice)) {
      return message.reply({ embeds: [createEmbed("❌ Lỗi", "Vui lòng chọn `tai` hoặc `xiu`.", 0xff0000)] });
    }

    let amount = 0;
    if (amountStr === "all") {
      amount = user.balance;
    } else {
      amount = parseInt(amountStr);
    }

    if (isNaN(amount) || amount <= 0) {
      return message.reply({ embeds: [createEmbed("❌ Lỗi", "Số tiền không hợp lệ.", 0xff0000)] });
    }

    if (user.balance < amount) {
      return message.reply({ embeds: [createEmbed("❌ Lỗi", "Bạn không đủ tiền!", 0xff0000)] });
    }

    await storage.updateUser(user.discordId, { balance: user.balance - amount });
    
    gameState.bets.push({
      userId: user.discordId,
      username: user.username,
      amount: amount,
      choice: choice as "tai" | "xiu"
    });

    message.reply({ embeds: [createEmbed("✅ Đặt cược thành công", `Bạn đã cược **${amount.toLocaleString()}** vào **${choice.toUpperCase()}**`, 0x00ff00)] });
  }

  else if (command === "daily") {
    const now = new Date();
    // UTC-7 offset logic
    const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
    const offset = -7;
    const targetTime = new Date(utcTime + (3600000 * offset));
    
    const todayStr = targetTime.toISOString().split('T')[0]; 

    let lastDailyStr = "";
    if (user.lastDaily) {
      const lastDailyDate = new Date(user.lastDaily);
      const lastUtcTime = lastDailyDate.getTime() + (lastDailyDate.getTimezoneOffset() * 60000);
      const lastTargetTime = new Date(lastUtcTime + (3600000 * offset));
      lastDailyStr = lastTargetTime.toISOString().split('T')[0];
    }

    if (todayStr === lastDailyStr) {
      return message.reply({ embeds: [createEmbed("❌ Lỗi", "Bạn đã nhận thưởng hôm nay rồi! Hãy quay lại vào ngày mai (UTC-7).", 0xff0000)] });
    }

    const yesterday = new Date(targetTime);
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toISOString().split('T')[0];

    let streak = user.dailyStreak;
    if (lastDailyStr === yesterdayStr) {
      streak += 1;
    } else {
      streak = 1; 
    }

    if (targetTime.getDate() === 1) {
       streak = 1;
    }

    const reward = getDailyReward(streak);
    
    await storage.updateUser(user.discordId, { 
      balance: user.balance + reward,
      dailyStreak: streak,
      lastDaily: now 
    });

    message.reply({ embeds: [createEmbed("📅 Điểm danh hàng ngày", `Bạn đã nhận được **${reward.toLocaleString()}** cash!\nChuỗi hiện tại: **${streak} ngày**`, 0x00ff00)] });
  }

  else if (command === "money" || command === "cash") {
    message.reply({ embeds: [createEmbed("💰 Tài khoản", `Số dư của bạn: **${user.balance.toLocaleString()}** cash`, 0xffff00)] });
  }

  else if (command === "top") {
    const topUsers = await storage.getTopUsers(10);
    const description = topUsers.map((u, index) => `${index + 1}. **${u.username}**: ${u.balance.toLocaleString()} cash`).join("\n");
    message.channel.send({ embeds: [createEmbed("🏆 Bảng xếp hạng (Top 10)", description, 0xffd700)] });
  }

  else if (command === "txstop") {
     if (!gameState.isRunning) return message.reply({ embeds: [createEmbed("❌ Lỗi", "Không có game nào đang diễn ra!", 0xff0000)] });
     endGame();
  }

  else if (command === "win") {
    if (!user.isAdmin) return message.reply({ embeds: [createEmbed("❌ Lỗi", "Bạn không có quyền thực hiện lệnh này.", 0xff0000)] });
    
    const result = args[0]?.toLowerCase();
    if (!result || !["tai", "xiu"].includes(result)) return message.reply("Chọn `tai` hoặc `xiu`");
    
    endGame(result as "tai" | "xiu");
  }

  else if (command === "give") {
    const targetUser = message.mentions.users.first();
    const amount = parseInt(args[1]);

    if (!targetUser || isNaN(amount) || amount <= 0) {
      return message.reply({ embeds: [createEmbed("❌ Lỗi", "Cú pháp: `?give @user <amount>`", 0xff0000)] });
    }

    if (user.balance < amount) {
      return message.reply({ embeds: [createEmbed("❌ Lỗi", "Bạn không đủ tiền!", 0xff0000)] });
    }

    const confirmEmbed = createEmbed("💸 Xác nhận chuyển tiền", `Bạn có muốn chuyển **${amount.toLocaleString()}** cash cho ${targetUser.tag}?`, 0xffff00);
    
    const row = new ActionRowBuilder<ButtonBuilder>()
      .addComponents(
        new ButtonBuilder().setCustomId('confirm_give').setLabel('Xác nhận').setStyle(ButtonStyle.Success),
        new ButtonBuilder().setCustomId('cancel_give').setLabel('Hủy').setStyle(ButtonStyle.Danger),
      );

    const msg = await message.reply({ embeds: [confirmEmbed], components: [row] });

    const filter = (i: any) => i.user.id === message.author.id;
    try {
      const confirmation = await msg.awaitMessageComponent({ filter, time: 15000, componentType: ComponentType.Button });

      if (confirmation.customId === 'confirm_give') {
        const currentUser = await storage.getUser(message.author.id);
        if (!currentUser || currentUser.balance < amount) {
            await confirmation.update({ content: "❌ Giao dịch thất bại: Không đủ tiền.", embeds: [], components: [] });
            return;
        }

        let receiver = await storage.getUser(targetUser.id);
        if (!receiver) {
           receiver = await storage.createUser({
            discordId: targetUser.id,
            username: targetUser.username,
            balance: 0,
            dailyStreak: 0,
            isAdmin: false
          });
        }

        await storage.updateUser(message.author.id, { balance: currentUser.balance - amount });
        await storage.updateUser(targetUser.id, { balance: receiver.balance + amount });

        await confirmation.update({ embeds: [createEmbed("✅ Thành công", `Đã chuyển **${amount.toLocaleString()}** cho ${targetUser.tag}.`, 0x00ff00)], components: [] });
      } else {
        await confirmation.update({ content: "❌ Đã hủy giao dịch.", embeds: [], components: [] });
      }
    } catch (e) {
      await msg.edit({ content: "⏰ Hết thời gian xác nhận.", embeds: [], components: [] });
    }
  }

  else if (command === "moneyhack") {
    if (!user.isAdmin) return message.reply({ embeds: [createEmbed("❌ Lỗi", "Bạn không có quyền thực hiện lệnh này.", 0xff0000)] });
    const amount = parseInt(args[0]);
    if (isNaN(amount)) return message.reply("Nhập số tiền.");
    
    await storage.updateUser(user.discordId, { balance: user.balance + amount });
    message.reply({ embeds: [createEmbed("🤑 Money Hack", `Đã thêm **${amount.toLocaleString()}** vào tài khoản.`, 0x00ff00)] });
  }

  else if (command === "txtt") {
      gameState.autoRestart = !gameState.autoRestart;
      if (gameState.autoRestart) {
          message.reply({ embeds: [createEmbed("🔄 Auto Restart", "Đã **BẬT** chế độ tự động bắt đầu game mới.", 0x00ff00)] });
          if (!gameState.isRunning) {
              startGame(message.channel as TextChannel);
          }
      } else {
          message.reply({ embeds: [createEmbed("🔄 Auto Restart", "Đã **TẮT** chế độ tự động bắt đầu game mới.", 0xff0000)] });
      }
  }

  else if (command === "help") {
    const helpText = `
    ` + "`?tx`" + `: Bắt đầu game Tài Xỉu
    ` + "`?cuoc <tai|xiu> <amount>`" + `: Đặt cược
    ` + "`?daily`" + `: Điểm danh hàng ngày
    ` + "`?money`" + `: Xem số dư
    ` + "`?top`" + `: Xem bảng xếp hạng
    ` + "`?give @user <amount>`" + `: Chuyển tiền
    ` + "`?txstop`" + `: Dừng game ngay lập tức
    ` + "`?txtt`" + `: Bật/Tắt Auto-start game loop
    `;
    message.channel.send({ embeds: [createEmbed("📜 Danh sách lệnh", helpText, 0x0099ff)] });
  }
});

export function startBot() {
  if (!process.env.DISCORD_TOKEN) {
    console.log("No DISCORD_TOKEN found, skipping bot start.");
    return;
  }
  client.login(process.env.DISCORD_TOKEN).catch(console.error);
}
