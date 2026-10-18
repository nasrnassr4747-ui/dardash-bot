import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "DardashChatBot"
CHANNEL_URL = "https://t.me/DardashChat"
GROUP_URL = "https://t.me/DardashGroup"

dp = Dispatcher()

TEXTS = {
    "ar": {
        "welcome": "🌟 أهلاً بك يا {name} في دردش!\n\nنقاطك: {points}",
        "help": "📖 الأوامر:\n/start\n/invite\n/me\n/lang\n/help",
        "btn_random": "🎲 ابحث عن شريك",
        "btn_me": "👤 حسابي",
        "btn_invite": "🎁 رابط الإحالة",
        "btn_lang": "🌐 اللغة",
        "btn_channel": "📢 القناة",
        "btn_group": "👥 المجموعة",
        "account": "👤 حسابك:\n\n🆔 {user_id}\n🏅 النقاط: {points}",
        "invite_msg": "🎁 رابط الإحالة:\n\n{link}",
        "lang_choose": "🌐 اختر لغتك:",
        "lang_changed": "✅ تم تغيير اللغة.",
        "random_found": "✅ تم إيجاد شريك!\n\nاكتب /end للإنهاء.",
        "random_end": "🛑 تم إنهاء الدردشة.",
        "random_waiting": "⏳ في قائمة الانتظار...",
        "random_already": "أنت في دردشة بالفعل. اكتب /end أولاً.",
    },
    "en": {
        "welcome": "🌟 Welcome {name} to Dardash!\n\nPoints: {points}",
        "help": "📖 Commands:\n/start\n/invite\n/me\n/lang\n/help",
        "btn_random": "🎲 Find Partner",
        "btn_me": "👤 My Account",
        "btn_invite": "🎁 Referral",
        "btn_lang": "🌐 Language",
        "btn_channel": "📢 Channel",
        "btn_group": "👥 Group",
        "account": "👤 Account:\n\n🆔 {user_id}\n🏅 Points: {points}",
        "invite_msg": "🎁 Link:\n\n{link}",
        "lang_choose": "🌐 Choose language:",
        "lang_changed": "✅ Language changed.",
        "random_found": "✅ Partner found!\n\nSend /end to finish.",
        "random_end": "🛑 Chat ended.",
        "random_waiting": "⏳ In queue...",
        "random_already": "You are in a chat. Send /end first.",
    },
}

USERS = {}
WAITING = []
CHATS = {}

def t(lang, key, **kwargs):
    if lang not in TEXTS: lang = "ar"
    text = TEXTS[lang].get(key, TEXTS["ar"].get(key, key))
    return text.format(**kwargs) if kwargs else text

def detect_lang(user):
    if not user or not user.language_code: return "ar"
    code = user.language_code[:2].lower()
    return code if code in TEXTS else "ar"

def get_user(user):
    if user.id not in USERS:
        USERS[user.id] = {"lang": detect_lang(user), "points": 0}
    return USERS[user.id]

def main_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_random"), callback_data="random")],
        [InlineKeyboardButton(text=t(lang, "btn_me"), callback_data="me"),
         InlineKeyboardButton(text=t(lang, "btn_invite"), callback_data="invite")],
        [InlineKeyboardButton(text=t(lang, "btn_lang"), callback_data="lang")],
        [InlineKeyboardButton(text=t(lang, "btn_channel"), url=CHANNEL_URL),
         InlineKeyboardButton(text=t(lang, "btn_group"), url=GROUP_URL)],
    ])

def lang_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇸🇦 العربية", callback_data="setlang:ar")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang:en")],
    ])

@dp.message(CommandStart())
async def start(message: Message):
    u = get_user(message.from_user)
    await message.answer(t(u["lang"], "welcome", name=message.from_user.first_name, points=u["points"]), reply_markup=main_menu(u["lang"]))

@dp.message(Command("me"))
async def me_cmd(message: Message):
    u = get_user(message.from_user)
    await message.answer(t(u["lang"], "account", user_id=message.from_user.id, points=u["points"]))

@dp.message(Command("invite"))
async def invite_cmd(message: Message):
    u = get_user(message.from_user)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{message.from_user.id}"
    await message.answer(t(u["lang"], "invite_msg", link=link))

@dp.message(Command("lang"))
async def lang_cmd(message: Message):
    u = get_user(message.from_user)
    await message.answer(t(u["lang"], "lang_choose"), reply_markup=lang_menu())

@dp.message(Command("random"))
async def random_cmd(message: Message):
    u = get_user(message.from_user)
    if message.from_user.id in CHATS:
        await message.answer(t(u["lang"], "random_already"))
        return
    if message.from_user.id in WAITING:
        await message.answer(t(u["lang"], "random_waiting"))
        return
    if WAITING:
        partner = WAITING.pop(0)
        CHATS[message.from_user.id] = partner
        CHATS[partner] = message.from_user.id
        pu = USERS.get(partner, {"lang": "ar"})
        await message.bot.send_message(message.from_user.id, t(u["lang"], "random_found"))
        await message.bot.send_message(partner, t(pu["lang"], "random_found"))
    else:
        WAITING.append(message.from_user.id)
        await message.answer(t(u["lang"], "random_waiting"))

@dp.message(Command("end"))
async def end_cmd(message: Message):
    u = get_user(message.from_user)
    if message.from_user.id in WAITING: WAITING.remove(message.from_user.id)
    if message.from_user.id in CHATS:
        partner = CHATS.pop(message.from_user.id)
        if partner in CHATS: del CHATS[partner]
        pu = USERS.get(partner, {"lang": "ar"})
        await message.answer(t(u["lang"], "random_end"))
        try: await message.bot.send_message(partner, t(pu["lang"], "random_end"))
        except: pass

@dp.message(F.text & ~F.text.startswith("/"))
async def relay_msg(message: Message):
    if message.from_user.id in CHATS:
        partner = CHATS[message.from_user.id]
        try: await message.bot.send_message(partner, f"💬 {message.text}")
        except: pass

@dp.callback_query(F.data == "me")
async def cb_me(call: CallbackQuery):
    u = get_user(call.from_user)
    await call.message.answer(t(u["lang"], "account", user_id=call.from_user.id, points=u["points"]))
    await call.answer()

@dp.callback_query(F.data == "invite")
async def cb_invite(call: CallbackQuery):
    u = get_user(call.from_user)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{call.from_user.id}"
    await call.message.answer(t(u["lang"], "invite_msg", link=link))
    await call.answer()

@dp.callback_query(F.data == "lang")
async def cb_lang(call: CallbackQuery):
    u = get_user(call.from_user)
    await call.message.answer(t(u["lang"], "lang_choose"), reply_markup=lang_menu())
    await call.answer()

@dp.callback_query(F.data.startswith("setlang:"))
async def cb_setlang(call: CallbackQuery):
    lang = call.data.split(":")[1]
    get_user(call.from_user)["lang"] = lang
    await call.message.answer(t(lang, "lang_changed"), reply_markup=main_menu(lang))
    await call.answer()

@dp.callback_query(F.data == "random")
async def cb_random(call: CallbackQuery):
    u = get_user(call.from_user)
    if call.from_user.id in CHATS:
        await call.message.answer(t(u["lang"], "random_already"))
    elif WAITING:
        partner = WAITING.pop(0)
        CHATS[call.from_user.id] = partner
        CHATS[partner] = call.from_user.id
        pu = USERS.get(partner, {"lang": "ar"})
        await call.message.answer(t(u["lang"], "random_found"))
        try: await call.bot.send_message(partner, t(pu["lang"], "random_found"))
        except: pass
    else:
        WAITING.append(call.from_user.id)
        await call.message.answer(t(u["lang"], "random_waiting"))
    await call.answer()

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print("✅ البوت يعمل...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
