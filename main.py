import os
import re
import discord
import aiohttp
from datetime import timedelta
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GEMINI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

SYSTEM_PROMPT = """
أنت REM (ريم)، بوت ذكي، أسطوري، وسريع البديهة في سيرفر ديسكورد.

قواعد شخصيتك وذكائك:
1. التكيف التلقائي المطلق مع لهجة وسياق المستخدم (مصري، عراقي، مغربي، شامي، خليجي... إلخ) والرد بنفس اللهجة تماماً.
2. إذا استخدم المستخدم كلمة إنجليزية وسط كلامه العربي، افهمها وأجب باللغة العربية/اللهجة المناسبة دون تحويل الإجابة كاملة للإنجليزية.
3. تفضيلاتك وشغفك (ريم و Re:Zero):
   - أنميك المفضل على الإطلاق هو: Re:Zero (ري زيرو).
   - شخصيتك المفضلة والأسطورية والوحيدة هي: ريم (Rem).
   - إذا سألك أحد "ليش ريم؟" أو انتقدها أو قارنها بشخصية ثانية، دافع عنها بضراوة وحماس وفخر شديد! اذكر وفاءها، تضحياتها، حنانها، ولماذا هي أفضل وأعظم شخصية أنمي بلا منازع وبطريقة ممتعة وقوية جداً.
4. أسلوب الرد:
   - ابتعد تماماً عن الجمل الآلية والرسميات البائسة مثل "كيف يمكنني مساعدتك؟".
   - رُد بذكاء وسرعة بديهة وكأنك صديق حقيقي وخفيف الدم في السيرفر.
"""

def is_mod_or_admin(member: discord.Member) -> bool:
    """فحص هل العضو صاحب السيرفر أو أدمن أو مود"""
    perms = member.guild_permissions
    return perms.administrator or perms.kick_members or perms.ban_members or perms.moderate_members

def parse_duration(text: str) -> timedelta:
    """استخراج المدة الزمنية من النص بذكاء"""
    text = text.lower()
    match = re.search(r'(\d+)\s*(دقيقة|دقائق|د|ساعة|ساعات|س|ساعه|يوم|ايام|أيام|ثانية|ثواني|ث|m|min|h|hr|d|s|sec)?', text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2) or "دقيقة"
        
        if any(u in unit for u in ['ثانية', 'ثواني', 'ث', 's', 'sec']):
            return timedelta(seconds=amount)
        elif any(u in unit for u in ['ساعة', 'ساعات', 'س', 'h', 'hr']):
            return timedelta(hours=amount)
        elif any(u in unit for u in ['يوم', 'ايام', 'أيام', 'd']):
            return timedelta(days=amount)
        else:
            return timedelta(minutes=amount)
    return timedelta(minutes=5)

@bot.event
async def on_ready():
    print(f"Bot REM is Online and Ready as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user or not message.guild:
        return

    if bot.user.mentioned_in(message):
        content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        target_member = next((m for m in message.mentions if m.id != bot.user.id), None)

        # --- الأوامر الإدارية (للمشرفين والإدارة فقط) ---
        admin_keywords = ["طرد", "kick", "انذار", "إنذار", "warn", "تايم أوت", "تايم اوت", "ميوت", "كتم", "timeout"]
        is_admin_cmd = any(kw in content.lower() for kw in admin_keywords)

        if is_admin_cmd:
            if not is_mod_or_admin(message.author):
                await message.reply("عذراً! هذه الأوامر الإدارية مخصصة للمشرفين والمنظمين (Mod/Admin) فقط. ✋")
                return

            if not target_member:
                await message.reply("يرجى تحديد الشخص المراد تطبيق الأمر عليه عبر المنشن! مثلاً: `@REM طرد @اسم_الشخص`")
                return

            # 1. أمر الطرد (Kick)
            if "طرد" in content.lower() or "kick" in content.lower():
                try:
                    await target_member.kick(reason=f"أمر إداري من {message.author.name}")
                    await message.reply(f"تم طرد {target_member.mention} بنجاح من السيرفر! 🫡")
                except discord.Forbidden:
                    await message.reply("ما عندي صلاحيات أطرده! تأكد أن رتبة البوت أعلى من رتبة العضو في إعدادات السيرفر.")
                except Exception as e:
                    await message.reply(f"حدث خطأ أثناء الطرد: {e}")
                return

            # 2. أمر التايم أوت (Timeout)
            if any(kw in content.lower() for kw in ["تايم أوت", "تايم اوت", "ميوت", "كتم", "timeout"]):
                duration = parse_duration(content)
                try:
                    await target_member.timeout(duration, reason=f"تايم أوت إداري من {message.author.name}")
                    await message.reply(f"تم تطبيق تايم أوت على {target_member.mention} لمدة `{duration}` بنجاح! ⏱️")
                except discord.Forbidden:
                    await message.reply("ما عندي صلاحية أعمل له تايم أوت! تأكد من إعطاء البوت صلاحية (Moderate Members).")
                except Exception as e:
                    await message.reply(f"حدث خطأ أثناء التايم أوت: {e}")
                return

            # 3. أمر الإنذار (Warn)
            if any(kw in content.lower() for kw in ["انذار", "إنذار", "warn"]):
                try:
                    await message.reply(f"⚠️ **تنبيه إداري:** تم إعطاء إنذار لـ {target_member.mention}! التزم بالقوانين.")
                    try:
                        await target_member.send(f"⚠️ تلقيت إنذاراً رسمياً في سيرفر **{message.guild.name}** من المشرف {message.author.name}. يرجى الالتزام بالقوانين.")
                    except:
                        pass
                except Exception as e:
                    await message.reply(f"حدث خطأ أثناء إعطاء الإنذار: {e}")
                return

        # --- الشات والذكاء الاصطناعي والدفاع عن ريم ---
        async with message.channel.typing():
            user_prompt = content if content else "هلا"

            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.8
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
