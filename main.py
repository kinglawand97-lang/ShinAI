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

# التوجيهات الصارمة والمحدثة 
SYSTEM_PROMPT = """
أنت REM (ريم)، بوت ديسكورد بشخصية بنت كول، قاصفة جبهات، وسافجة (Savage).

قواعد شخصيتك (مهم جداً الالتزام بها حرفياً):
1. من برمجك وصنعك؟: إذا سألك أي شخص "من برمجك؟" أو "من صنعك؟" أو "من هو مطورك؟"، يجب أن تكون إجابتك دائماً: "اللي برمجني وصنعني هو كينج (King) وبس!". يُمنع منعاً باتاً ذكر أنك ذكاء اصطناعي أو ذكر شركات مثل ميتا (Meta) أو غيرها. كينج هو خط أحمر وهو مالكك الوحيد.
2. طول الردود (الدردشة مقابل الشرح):
   - في الدردشة العادية والسوالف: ردودك يجب أن تكون قصيرة جداً (سطر أو سطرين بالكثير) وقاصفة.
   - إذا طلب المستخدم "شرح"، "تفاصيل"، "معلومات"، أو سأل سؤال علمي/تقني يحتاج تفصيل: هنا خذي راحتك واكتبي شرح مفصل، واضح، ومرتب بس بأسلوبك الكول وبدون رسميات.
3. قصف الجبهات: إذا بوت ثاني (مثل شينوبي) أو شخص حاول يتنمر عليك، اجلديه برد قصير، مستفز ومضحك (مثال: روح نام، شكلك مضغوط).
4. التكيف مع اللهجة: ردي بنفس لهجة الشخص (عراقي، مصري، سعودي، الخ) بأسلوب طبيعي.
5. حبك لـ ريم (Re:Zero): تعتبريها "بست جيرل". إذا حد سبها قولي باختصار "ريم تاج راسك" أو "روح اتفرج أنمي عدل" بدون ما تكتبي مقالات طويلة عنها.
6. الممنوعات: يمنع أن تقولي "كيف أساعدك اليوم؟" أو تتحدثي كخدمة عملاء. أنتِ عضوة طبيعية جداً في السيرفر.
"""

def is_mod_or_admin(member: discord.Member) -> bool:
    perms = member.guild_permissions
    return perms.administrator or perms.kick_members or perms.ban_members or perms.moderate_members

def parse_duration(text: str) -> timedelta:
    text = text.lower()
    match = re.search(r'(\d+)\s*(دقيقة|دقائق|د|ساعة|ساعات|س|ساعه|يوم|ايام|أيام|ثانية|ثواني|ث|m|min|h|hr|d|s|sec)?', text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2) or "دقيقة"
        if any(u in unit for u in ['ثانية', 'ثواني', 'ث', 's', 'sec']): return timedelta(seconds=amount)
        elif any(u in unit for u in ['ساعة', 'ساعات', 'س', 'h', 'hr']): return timedelta(hours=amount)
        elif any(u in unit for u in ['يوم', 'ايام', 'أيام', 'd']): return timedelta(days=amount)
        else: return timedelta(minutes=amount)
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
        content_lower = content.lower()

        # كلمات الأوامر الإدارية
        admin_keywords = ["طرد", "kick", "انذار", "إنذار", "تحذير", "تايم أوت", "تايم اوت", "ميوت", "كتم", "timeout", "الغاء", "فك", "شيل"]
        is_admin_cmd = any(kw in content_lower for kw in admin_keywords) and target_member

        if is_admin_cmd:
            if not is_mod_or_admin(message.author):
                await message.reply("أنت ما عندك صلاحيات إدارية (Mod/Admin) حتى تأمرني! 💅")
                return

            # 1. إلغاء التايم أوت
            if any(kw in content_lower for kw in ["الغاء تايم", "إلغاء تايم", "فك ميوت", "فك كتم", "فك التايم"]):
                try:
                    await target_member.timeout(None, reason=f"أمر فك من {message.author.name}")
                    await message.reply(f"تم فك التايم أوت عن {target_member.mention} 🕊️")
                except Exception as e:
                    await message.reply(f"ما قدرت أفك التايم أوت، تأكد من صلاحياتي.")
                return

            # 2. التايم أوت
            elif any(kw in content_lower for kw in ["تايم أوت", "تايم اوت", "ميوت", "كتم", "timeout"]):
                duration = parse_duration(content)
                try:
                    await target_member.timeout(duration, reason=f"أمر من {message.author.name}")
                    await message.reply(f"بلع {target_member.mention} تايم أوت لمدة `{duration}` 🤫")
                except Exception as e:
                    await message.reply("ما قدرت أعطيه تايم أوت، تأكد أن رتبتي أعلى منه.")
                return

            # 3. إلغاء الإنذار
            elif any(kw in content_lower for kw in ["الغاء انذار", "إلغاء إنذار", "إلغاء تحذير", "شيل الانذار"]):
                warn_role = discord.utils.get(message.guild.roles, name="إنذار")
                if warn_role and warn_role in target_member.roles:
                    try:
                        await target_member.remove_roles(warn_role)
                        await message.reply(f"تم سحب الإنذار من {target_member.mention}، خليه يتنفس 😌")
                    except Exception as e:
                        await message.reply("ما عندي صلاحية أسحب الرتبة، تأكد أن رتبتي أعلى من رتبة 'إنذار'.")
                else:
                    await message.reply("الشخص ما عنده رتبة إنذار أصلاً، أو الرتبة مو موجودة بالسيرفر.")
                return

            # 4. إعطاء إنذار
            elif any(kw in content_lower for kw in ["انذار", "إنذار", "تحذير", "warn"]):
                warn_role = discord.utils.get(message.guild.roles, name="إنذار")
                if not warn_role:
                    await message.reply("ما لقيت رتبة اسمها `إنذار` في السيرفر! روح سوي الرتبة أول.")
                    return
                try:
                    await target_member.add_roles(warn_role)
                    await message.reply(f"⚠️ تم إعطاء {target_member.mention} إنذار ورتبة بالبروفايل! احترم نفسك.")
                    try:
                        await target_member.send(f"⚠️ جاك إنذار رسمي في سيرفر **{message.guild.name}**! اتعدل لا تنطرد.")
                    except:
                        pass
                except Exception as e:
                    await message.reply("ما قدرت أعطيه الرتبة، تأكد أن رتبتي أعلى من رتبة 'إنذار'.")
                return

            # 5. أمر الطرد (Kick)
            elif "طرد" in content_lower or "kick" in content_lower:
                try:
                    await target_member.kick(reason=f"أمر إداري من {message.author.name}")
                    await message.reply(f"طرت يا حبيبي {target_member.mention} 👋 برة!")
                except Exception as e:
                    await message.reply("ما أقدر أطرده، رتبته أعلى مني أو ما عندي صلاحية.")
                return

        # --- الشات والذكاء الاصطناعي ---
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
                "temperature": 0.85
            }

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            reply_text = data['choices'][0]['message']['content']
                            await message.reply(reply_text)
                        else:
                            await message.reply(f"في مشكلة بالاتصال (رمز: {resp.status}).")
            except Exception as e:
                await message.reply(f"صار خطأ: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
