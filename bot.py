from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
import asyncio
import logging
import os
import re
import json
import html

# --- SOZLAMALAR ---
# DIQQAT: tokenni KODGA yozma! Railway -> Variables bo'limida
# BOT_TOKEN nomli o'zgaruvchi yaratib, qiymatiga tokenni qo'y.
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@BeamModsStudio"
BOT_USERNAME = "BeamModsStudio_bot"   # @ belgisisiz
ADMIN_ID = 7022141893
MODS_FILE = "mods.json"
# -----------------

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable o'rnatilmagan!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Birinchi marta ishga tushganda mods.json bo'lmasa shu modlar yoziladi
DEFAULT_MODS = {
    "zaz_kpop": {
        "file_id": "BQACAgIAAxkBAANBag4SjOzv4tfVmDfXct--Q9yl9_gAArKiAAJgF4lLtmLe5C0yv6w7BA",
        "name": "Zaz Kpop"
    },
    "barbie_shrek": {
        "file_id": "BQACAgIAAxkBAAMragtkvVc37kBQ2rYwvDeqBxpOniAAAtifAAIIONlLsQeI1Sr59LU7BA",
        "name": "Barbie Shrek"
    },
    "nokia_hammer": {
        "file_id": "BQACAgIAAxkBAANlag40ovguaXPZlsdfMpYOExbIVdUAAnyjAAIpZkBILBVHf71r23Y7BA",
        "name": "Nokia Hammer"
    },
    "bmw_m3": {
        "file_id": "BQACAgIAAxkBAANpag45zF3k5QuErO8lIGge1tnoee8AAveUAAJ6bOBL06Qaf7slLeI7BA",
        "name": "BMW M3"
    },
    "cat_car": {
        "file_id": "BQACAgIAAxkBAANrag46p_ophZ1n8NwdUp93EN2x1pEAAumdAAJQEQFIjQABRcODde0UOwQ",
        "name": "Cat Car"
    },
}

# --- MODLARNI YUKLASH ---
def load_mods():
    if os.path.exists(MODS_FILE):
        with open(MODS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Fayl yo'q bo'lsa standart modlarni yaratamiz va saqlaymiz
    save_mods(DEFAULT_MODS)
    return dict(DEFAULT_MODS)

def save_mods(mods: dict):
    with open(MODS_FILE, "w", encoding="utf-8") as f:
        json.dump(mods, f, ensure_ascii=False, indent=2)

MODS = load_mods()

# --- YORDAMCHI ---
def make_mod_key(name: str) -> str:
    key = name.lower()
    key = re.sub(r"[^a-z0-9_]", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key

# --- ADMIN: MOD QABUL QILISH ---
# Zip yuborasan -> bot darrov yuklab olish havolasini beradi.
# Nom: caption bo'lsa o'sha ishlatiladi, bo'lmasa fayl nomidan olinadi.
@dp.message(F.document, F.from_user.id == ADMIN_ID)
async def admin_new_mod(message: types.Message):
    file_id = message.document.file_id
    file_name = message.document.file_name or "mod"

    # Nom: caption -> bo'lmasa fayl nomidan (.zip/.rar/.7z olib tashlanadi)
    name = (message.caption or "").strip()
    if not name:
        name = re.sub(r"\.(zip|rar|7z|mod)$", "", file_name, flags=re.IGNORECASE)

    mod_key = make_mod_key(name)
    if not mod_key:
        mod_key = "mod_" + str(len(MODS) + 1)

    # Saqlash (xuddi shu nom bilan qayta yuborsang, mod yangilanadi)
    MODS[mod_key] = {"file_id": file_id, "name": name}
    save_mods(MODS)

    download_url = f"https://t.me/{BOT_USERNAME}?start=download_{mod_key}"

    # Adminga tayyor havola
    await message.answer(
        f"✅ Saqlandi: <b>{html.escape(name)}</b>\n\n"
        f"🔗 Yuklab olish havolasi:\n{download_url}\n\n"
        f"📌 Kanal postidagi <b>«📥 Yuklab olish»</b> yozuviga shu havolani biriktiring.",
        parse_mode="HTML",
        disable_web_page_preview=True
    )

# --- /id : o'z Telegram ID'ingizni bilish uchun ---
@dp.message(Command("id"))
async def get_id(message: types.Message):
    await message.answer(
        f"🆔 Sizning ID: <code>{message.from_user.id}</code>\n"
        f"⚙️ Botdagi ADMIN_ID: <code>{ADMIN_ID}</code>\n\n"
        + ("✅ Mos keladi — siz adminsiz."
           if message.from_user.id == ADMIN_ID
           else "❌ Mos kelmaydi! Kodda ADMIN_ID ni yuqoridagi ID ga o'zgartiring."),
        parse_mode="HTML"
    )

# --- DEBUG: fayl admin handlerga tushmasa, ID ni ko'rsatadi ---
# (Muammo hal bo'lgach, bu handlerni o'chirib tashlasangiz bo'ladi)
@dp.message(F.document)
async def debug_document(message: types.Message):
    logging.info(f"Document from non-admin id={message.from_user.id}")
    await message.answer(
        f"⚠️ Fayl admin handlerga tushmadi.\n\n"
        f"🆔 Sizning ID: <code>{message.from_user.id}</code>\n"
        f"⚙️ ADMIN_ID: <code>{ADMIN_ID}</code>\n\n"
        f"Agar bu siz bo'lsangiz — kodda ADMIN_ID ni shu ID ga o'zgartiring va qayta deploy qiling.",
        parse_mode="HTML"
    )

# --- OBUNA TEKSHIRISH ---
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        )
    except Exception as e:
        logging.warning(f"Obuna tekshirishda xato: {e}")
        return False

# --- MOD YUBORISH (umumiy funksiya) ---
async def send_mod(chat_id: int, mod_key: str) -> bool:
    if mod_key in MODS:
        await bot.send_document(
            chat_id=chat_id,
            document=MODS[mod_key]["file_id"],
            caption=f"🚗 {MODS[mod_key]['name']} modi\n✅ BeamNG mods papkasiga tashlang!"
        )
        return True
    return False

# --- /start ---
@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    args = message.text.split(maxsplit=1)

    # Deep-link: /start download_<key>
    if len(args) > 1 and args[1].startswith("download_"):
        mod_key = args[1].removeprefix("download_")

        if not await is_subscribed(user_id):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish",
                                      url="https://t.me/BeamModsStudio")],
                [InlineKeyboardButton(text="✅ Tekshirish",
                                      callback_data=f"recheck_{mod_key}")]
            ])
            await message.answer(
                f"Salom {name}! 👋\n\n"
                "❌ Modlarni olish uchun avval kanalga obuna bo'ling 👇",
                reply_markup=keyboard
            )
            return

        if not await send_mod(user_id, mod_key):
            await message.answer("❌ Mod topilmadi!")
        return

    # Oddiy /start
    if await is_subscribed(user_id):
        await message.answer(
            f"✅ Salom {name}!\n\n"
            "Modlarni kanal postlaridagi havolalar orqali yuklab oling! 👇\n"
            "👉 https://t.me/BeamModsStudio"
        )
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish",
                                  url="https://t.me/BeamModsStudio")],
            [InlineKeyboardButton(text="✅ Tekshirish",
                                  callback_data="check_sub")]
        ])
        await message.answer(
            f"Salom {name}! 👋\n\n"
            "🚗 BeamNG.drive modlarini olish uchun\n"
            "avval kanalga obuna bo'ling 👇",
            reply_markup=keyboard
        )

@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.edit_text(
            "✅ Obuna tasdiqlandi!\n\n"
            "Modlarni kanal postlaridagi havolalar orqali yuklab oling! 👇\n"
            "👉 https://t.me/BeamModsStudio"
        )
        await callback.answer("✅ Obuna tasdiqlandi!")
    else:
        await callback.answer("❌ Hali obuna bo'lmagansiz!", show_alert=True)

@dp.callback_query(F.data.startswith("recheck_"))
async def recheck_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    mod_key = callback.data.removeprefix("recheck_")

    if not await is_subscribed(user_id):
        await callback.answer("❌ Hali obuna bo'lmagansiz!", show_alert=True)
        return

    if mod_key in MODS:
        await callback.answer("✅ Obuna tasdiqlandi!")
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await send_mod(user_id, mod_key)
    else:
        await callback.answer("❌ Mod topilmadi!", show_alert=True)

async def main():
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
