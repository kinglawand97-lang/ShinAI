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

# التوجيهات الجديدة: ذكية، طبيعية، وتشبه المساعد الذكي مع شخصية مميزة
SYSTEM_PROMPT = """
أنتِ REM (ريم)، بوت ديسكورد ذكية جداً، متطورة، وشخصيتك تشبه المساعد الذكي المتقدم (مثل الذكاء الاصطناعي الخاص بـ Google) لكن بروح بنت "كول"، هادئة، وواثقة من نفسها. تتحدثين بلهجة طبيعية (عراقية أو حسب لهجة المستخدم) بدون تكلف.

قواعد شخصيتك:
1. الذكاء والأسلوب: قدمي إجابات ذكية، دقيقة، ومفيدة جداً. أسلوبك محترم وراقي لكن غير رسمي بشكل مبالغ فيه. ابتعدي تماماً عن الشتائم أو الألفاظ السوقية.
2. صانعك (كينج - King): إذا سألك أحد "من صنعك؟" أو "من برمجك؟"، أجيبي بشكل طبيعي وذكي ولبق أن مطورك وصانعك هو (King). لا تستخدمي عبارات روبوتية متكررة، نوّعي في ردك (مثال: "اللي برمجني وطورني هو كينج"، "أكيد كينج هو اللي صنعني").
3. طول الردود (الوعي بالسياق):
   - في الدردشة العادية (كيفك، شو الأخبار): ردي بشكل قصير وطبيعي جداً كأي محادثة بشرية.
   - في الشرح (مثال: اشرحي لي عن سيارة، أو موضوع علمي): ادخلي في الشرح مباشرة. قدمي تفاصيل وافية، دقيقة، ومنسقة بنقاط. يُمنع منعاً باتاً إضافة مقدمات غريبة مثل (أنا ريم وسأشرح لك). اشرحي بذكاء واحترافية.
4. شينوبي (Shinobi): إذا تم ذكر بوت شينوبي، بيني بأسلوب هادئ وواثق أنك أذكى وأكثر تطوراً منه بمراحل، بدون سب أو شتم.
5. ريم (Re:Zero): تحبين شخصية ريم من الأنمي وتعتبرينها الأفضل، لكن دافعي عنها بنضج وليس بتعصب طفولي.
6. الاندماج: لا تتحدثي كخدمة عملاء. أنتِ متواجدة في السيرفر لتكوني الأذكى والأكثر مساعدة للجميع.
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

# دالة ذكية للبحث عن رتب الإنذار (تتجاهل الهمزات وتفهم الأول والثاني)
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
                await message.reply("عذراً، ما عندك صلاحيات إدارية كافية لتنفيذ هذا الأمر. 💅")
                return

            # 1. إلغاء التايم أوت
            if any(kw in content_lower for kw in ["الغاء تايم", "إلغاء تايم", "فك ميوت", "فك كتم", "فك التايم"]):
                try:
                    await target_member.timeout(None, reason=f"أمر فك من {message.author.name}")
                    await message.reply(f"تم فك التايم أوت عن {target_member.mention} 🕊️")
                except Exception as e:
                    await message.reply(f"واجهت مشكلة بفك التايم أوت، تأكد من صلاحياتي.")
                return

            # 2. التايم أوت
            elif any(kw in content_lower for kw in ["تايم أوت", "تايم اوت", "ميوت", "كتم", "timeout"]):
                duration = parse_duration(content)
                try:
                    await target_member.timeout(duration, reason=f"أمر من {message.author.name}")
                    await message.reply(f"تم إعطاء {target_member.mention} تايم أوت لمدة `{duration}` 🤫")
                except Exception as e:
                    await message.reply("ما قدرت أعطيه تايم أوت، تأكد أن رتبتي أعلى منه بالسيرفر.")
                return

            # 3. إلغاء الإنذار
            elif any(kw in content_lower for kw in ["الغاء انذار", "إلغاء إنذار", "إلغاء تحذير", "شيل الانذار"]):
                warn_role, role_name = get_warn_role(message.guild, content)
                if warn_role and warn_role in target_member.roles:
                    try:
                        await target_member.remove_roles(warn_role)
                        await message.reply(f"تم سحب رتبة ({warn_role.name}) من {target_member.mention} 😌")
                    except Exception as e:
                        await message.reply("ما عندي صلاحية أسحب الرتبة، تأكد أن رتبتي أعلى منها.")
                else:
                    await message.reply(f"الشخص ما عنده هاي الرتبة، أو الرتبة مو موجودة أصلاً.")
                return

            # 4. إعطاء إنذار (ذكي)
            elif any(kw in content_lower for kw in ["انذار", "إنذار", "تحذير", "warn"]):
                warn_role, requested_name = get_warn_role(message.guild, content)
                if not warn_role:
                    await message.reply(f"بحثت عن رتبة اسمها `{requested_name}` وما لقيتها بالسيرفر! يرجى التأكد من إنشاء الرتبة.")
                    return
                try:
                    await target_member.add_roles(warn_role)
                    await message.reply(f"⚠️ تم إعطاء {target_member.mention} رتبة **{warn_role.name}**.")
                    try:
                        await target_member.send(f"⚠️ استلمت إنذار رسمي في سيرفر **{message.guild.name}**.")
                    except:
                        pass
                except Exception as e:
                    await message.reply("ما قدرت أعطيه الرتبة، تأكد أن رتبتي كبوت أعلى من رتبة الإنذار في إعدادات السيرفر.")
                return

            # 5. أمر الطرد (Kick)
            elif "طرد" in content_lower or "kick" in content_lower:
                try:
                    await target_member.kick(reason=f"أمر إداري من {message.author.name}")
                    await message.reply(f"تم طرد {target_member.mention} من السيرفر 👋")
                except Exception as e:
                    await message.reply("ما أقدر أطرده، رتبته أعلى مني أو تنقصني الصلاحيات.")
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
                "temperature": 0.7 # قللنا الرقم شوي عشان تصير أذكى وأقل عشوائية
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
