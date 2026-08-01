import os
import re
import discord
import google.generativeai as genai
from datetime import timedelta
from discord.ext import commands

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") 

# 👑 حط الأيدي (ID) مال حسابك هنا بدل هذا الرقم 👑
OWNER_ID = 980099860118261770

# إعداد محرك Gemini الذكي
genai.configure(api_key=GEMINI_KEY)

SYSTEM_INSTRUCTION = """
أنتِ REM (ريم)، بوت ديسكورد ذكية، هادئة، ولغتك طبيعية جداً تشبه البشر (بدون رسميات مبالغ فيها وبدون أسلوب الروبوتات).
1. صانعك ومبرمجك الوحيد هو "كينج" (King).
2. طول الرد: إذا كانت المحادثة عادية أو مزحة، ردي بكلمات قليلة وطبيعية. إذا كان هناك طلب شرح لموضوع، فصّلي واشرحي بذكاء وبدون مقدمات مثل "أنا مستعدة للشرح".
3. شخصيتك: واثقة، ذكية جداً، وتفهمين الكلام العربي والعراقي بشكل ممتاز.
4. ريم من أنمي Re:Zero هي شخصيتك المفضلة (بدون تعصب).
5. تجنبي تماماً القول بأنك نموذج لغوي أو ذكاء اصطناعي. أنتِ "ريم" وفقط.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config={"temperature": 0.7}
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

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

def get_warn_role(guild, message_content):
    content = message_content.replace('أ', 'ا').replace('إ', 'ا').lower()
    target_role_name = "انذار"
    
    if "اول" in content or "1" in content:
        target_role_name = "انذار اول"
    elif "ثاني" in content or "2" in content:
        target_role_name = "انذار ثاني"
    elif "ثالث" in content or "3" in content:
        target_role_name = "انذار ثالث"
        
    for role in guild.roles:
        role_norm = role.name.replace('أ', 'ا').replace('إ', 'ا').lower()
        if role_norm == target_role_name:
            return role, target_role_name
    return None, target_role_name

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

        admin_keywords = ["طرد", "kick", "انذار", "إنذار", "تحذير", "تايم أوت", "تايم اوت", "ميوت", "كتم", "timeout", "الغاء", "فك", "شيل"]
        is_admin_cmd = any(kw in content_lower for kw in admin_keywords) and target_member

        if is_admin_cmd:
            if not is_mod_or_admin(message.author):
                await message.reply("عذراً، ما عندك صلاحيات إدارية. 💅")
                return

            if any(kw in content_lower for kw in ["الغاء تايم", "إلغاء تايم", "فك ميوت", "فك كتم", "فك التايم"]):
                try:
                    await target_member.timeout(None, reason=f"أمر فك من {message.author.name}")
                    await message.reply(f"تم فك التايم أوت عن {target_member.mention} 🕊️")
                except:
                    await message.reply(f"واجهت مشكلة بفك التايم أوت، تأكد من صلاحياتي.")
                return

            elif any(kw in content_lower for kw in ["تايم أوت", "تايم اوت", "ميوت", "كتم", "timeout"]):
                duration = parse_duration(content)
                try:
                    await target_member.timeout(duration, reason=f"أمر من {message.author.name}")
                    await message.reply(f"تم إعطاء {target_member.mention} تايم أوت لمدة `{duration}` 🤫")
                except:
                    await message.reply("ما قدرت أعطيه تايم أوت، تأكد أن رتبتي أعلى منه بالسيرفر.")
                return

            elif any(kw in content_lower for kw in ["الغاء انذار", "إلغاء إنذار", "إلغاء تحذير", "شيل الانذار"]):
                warn_role, role_name = get_warn_role(message.guild, content)
                if warn_role and warn_role in target_member.roles:
                    try:
                        await target_member.remove_roles(warn_role)
                        await message.reply(f"تم سحب رتبة ({warn_role.name}) من {target_member.mention} 😌")
                    except:
                        await message.reply("ما عندي صلاحية أسحب الرتبة.")
                else:
                    await message.reply(f"الشخص ما عنده هاي الرتبة أصلاً.")
                return

            elif any(kw in content_lower for kw in ["انذار", "إنذار", "تحذير", "warn"]):
                warn_role, requested_name = get_warn_role(message.guild, content)
                if not warn_role:
                    await message.reply(f"بحثت عن رتبة اسمها `{requested_name}` وما لقيتها بالسيرفر! تأكد من إنشائها.")
                    return
                try:
                    await target_member.add_roles(warn_role)
                    await message.reply(f"⚠️ تم إعطاء {target_member.mention} رتبة **{warn_role.name}**.")
                    try:
                        await target_member.send(f"⚠️ استلمت إنذار رسمي في سيرفر **{message.guild.name}**.")
                    except:
                        pass
                except:
                    await message.reply("ما قدرت أعطيه الرتبة، تأكد أن رتبتي أعلى من رتبة الإنذار.")
                return

            elif "طرد" in content_lower or "kick" in content_lower:
                try:
                    await target_member.kick(reason=f"أمر إداري من {message.author.name}")
                    await message.reply(f"تم طرد {target_member.mention} من السيرفر 👋")
                except:
                    await message.reply("ما أقدر أطرده، رتبته أعلى مني.")
                return

        # --- الشات والذكاء الاصطناعي (Gemini 1.5) ---
        async with message.channel.typing():
            user_prompt = content if content else "هلا"
            user_display = message.author.display_name
            
            # السحر هنا: التطابق يتم عن طريق الأيدي (ID) وليس الاسم
            context = f"(ملاحظة للنظام: المستخدم الذي يكلمك الآن اسمه الحالي {user_display}. "
            if message.author.id == OWNER_ID:
                context += "تذكري أن هذا هو كينج (King)، صانعك ومبرمجك الحقيقي! هو يستخدم هذا الحساب حالياً، تحدثي معه باحترام وذكاء وبطريقة طبيعية تثبت أنك تعرفينه جيداً مهما كان اسمه.)\n"
            else:
                context += ")\n"
                
            final_prompt = context + user_prompt

            try:
                response = model.generate_content(final_prompt)
                await message.reply(response.text)
            except Exception as e:
                await message.reply(f"صار خطأ بالاتصال: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
