import os
import discord
import aiohttp
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GEMINI_API_KEY")  # نستخدم نفس اسم المتغير للتسهيل عليك

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot REM is Online as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            user_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
            if not user_prompt:
                user_prompt = "مرحباً!"

            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "أنت REM، بوت ذكي، ودود، وسريع الإجابة في سيرفر ديسكورد. أجب باختصار وذكاء باللغة العربية."},
                    {"role": "user", "content": user_prompt}
                ]
            }

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            reply_text = data['choices'][0]['message']['content']
                            await message.reply(reply_text)
                        else:
                            await message.reply(f"حدث خطأ في الاتصال (رمز: {resp.status}).")
            except Exception as e:
                await message.reply(f"حدث خطأ غير متوقع: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
