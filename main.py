import os
import discord
from discord.ext import commands
from google import genai

# إعدادات البوت والذكاء الاصطناعي
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# تهيئة عميل جيميني الجديد
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# إعدادات صلاحيات البوت في ديسكورد
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"ShinAI Started Successfully. Listening for messages as {bot.user}")

@bot.event
async def on_message(message):
    # تجاهل رسائل البوت نفسهِ لكي لا يحدث تكرار بالردود
    if message.author == bot.user:
        return

    # إذا تم مناداة البوت أو الرد على رسالته
    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            try:
                # تنظيف النص من منشن البوت
                user_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
                
                if not user_prompt:
                    user_prompt = "مرحباً!"

                # إرسال الطلب لنموذج جيميني
                response = ai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_prompt,
                )
                
                await message.reply(response.text)
            except Exception as e:
                await message.reply(f"حدث خطأ أثناء معالجة الطلب: {e}")

    await bot.process_commands(message)

# تشغيل البوت
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
