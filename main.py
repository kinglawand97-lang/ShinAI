import os
import discord
import aiohttp
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot started successfully as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            user_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
            if not user_prompt:
                user_prompt = "مرحباً!"

            # رابط Google Gemini الرسمى مع النموذج المستقر gemini-1.5-flash
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": user_prompt}]}]
            }

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            reply_text = data['candidates'][0]['content']['parts'][0]['text']
                            await message.reply(reply_text)
                        else:
                            err_body = await resp.text()
                            print(f"API Error Code: {resp.status} - Details: {err_body}")
                            await message.reply(f"حدث خطأ في المفتاح أو الخدمة (رمز: {resp.status}).")
            except Exception as e:
                print(f"Exception: {e}")
                await message.reply(f"حدث خطأ غير متوقع: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
