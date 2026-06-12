from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import logging
import os
import re
import json

# --- SOZLAMALAR ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@BeamModsStudio"
ADMIN_ID = 7022141893
MODS_FILE = "mods.json"
# -----------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# --- MODLARNI YUKLASH ---
def load_mods():
    if os.path.exists(MODS_FILE):
        with open(MODS_FILE, "r") as f:
            return json.load(f)
    return {
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
        "BMW_M3": {
            "file_id": "BQACAgIAAxkBAANpag45zF3k5QuErO8lIGge1tnoee8AAveUAAJ6bOBL06Qaf7slLeI7BA",
            "name": "BMW M3"
        },
        "Cat_car": {
            "file_id": "BQACAgIAAxkBAANrag46p_ophZ1n8NwdUp93EN2x1pEAAumdAAJQEQFIjQABRcODde0UOwQ",
            "name": "Cat Car"
        },
    }

def save_mods(mods: dict):
    with open(MODS_FILE, "w") as f:
        json.dump(mods, f, ensure_ascii=False, indent=2)

MODS = load_mods()

# --- YORDAMCHI ---
def make_mod_key(name: str) -> str:
    key = name.lower()
    key = re.sub(r"[^a-z0-9_]", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key

# --- ADMIN: MOD QABUL QILISH ---
@dp.message(lambda m: m.from_user.id == ADMIN_ID and m.document)
async def admin_new_mod(message: types.Message):
    caption = message.caption or ""
    file_id = message.document.file_id
    file_name = message.document.file_name or "mod"

    # Caption dan nom va tavsif olish
    name_match = re.search(r"Nomi:\s*(.+)", caption)
    desc_match = re.search(r"Tavsif:\s*(.+)", caption)

    if not name_match:
        # Caption yo'q bo'lsa faqat file_id bersin
        await message.answer(
            f"📁 Fayl: {file_name}\n"
            f"🔑 File ID:\n`{file_id}`\n\n"
            "📝 Post uchun caption qo'shing:\n"
            "```\nNomi: Mod nomi\nTavsif: Mod tavsifi\n```",
            parse_mode="Markdown"
        )
        return

    name = name_match.group(1).strip()
    desc = desc_match.group(1).strip() if desc_match else "BeamNG.drive uchun sifatli yangi mod!"
    mod_key = make_mod_key(name)

    # MODS ga saqlash
    MODS[mod_key] = {
        "file_id": file_id,
        "name": name
    }
    save_mods(MODS)

    # Tayyor post matni
    download_url = f"https://t.me/BeamModsStudio_bot?start=download_{mod_key}"
    post_text = (
        f"🚗 YANGI MOD: {name}\n\n"
        f"📌 Tavsif:\n{desc}\n\n"
        f"⚙️ Xususiyatlari:\n"
        f"• Yuqori sifatli model\n"
        f"• Realistic fizika\n"
        f"• BeamNG.drive ga mos\n\n"
        f"📥 Yuklab olish — BEPUL!\n\n"
        f"✅ Yuklab olish uchun kanalga obuna bo'lish talab etiladi!\n\n"
        f"📢 Kanal: @BeamModsStudio"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📥 Yuklab olish",
            url=download_url
        )]
    ])

    # Adminga tayyor postni yuborish
    await message.answer(
        f"✅ Mod saqlandi! Mana tayyor post:\n\n"
        f"👇 Kanalga ko'chirish uchun quyidagi xabarni forward qiling:"
    )
    await message.answer(
        text=post_text,
        reply_markup=keyboard
    )

# --- OBUNA TEKSHIRISH ---
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- /start ---
@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    args = message.text.split()

    if len(args) > 1 and args[1].startswith("download_"):
        mod_key = args[1].replace("download_", "")

        if not await is_subscribed(user_id):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📢 Kanalga obuna bo'lish",
                    url="https://t.me/BeamModsStudio"
                )],
                [InlineKeyboardButton(
                    text="✅ Tekshirish",
                    callback_data=f"recheck_{mod_key}"
                )]
            ])
            await message.answer(
                f"Salom {name}! 👋\n\n"
                "❌ Modlarni olish uchun avval kanalga obuna bo'ling 👇",
                reply_markup=keyboard
            )
            return

        if mod_key in MODS:
            await message.answer_document(
                document=MODS[mod_key]["file_id"],
                caption=f"🚗 {MODS[mod_key]['name']} modi\n✅ BeamNG mods papkasiga tashlang!"
            )
        else:
            await message.answer("❌ Mod topilmadi!")
        return

    if await is_subscribed(user_id):
        await message.answer(
            f"✅ Salom {name}!\n\n"
            "Modlarni kanal postlaridagi havolalar orqali yuklab oling! 👇\n"
            "👉 https://t.me/BeamModsStudio"
        )
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📢 Kanalga obuna bo'lish",
                url="https://t.me/BeamModsStudio"
            )],
            [InlineKeyboardButton(
                text="✅ Tekshirish",
                callback_data="check_sub"
            )]
        ])
        await message.answer(
            f"Salom {name}! 👋\n\n"
            "🚗 BeamNG.drive modlarini olish uchun\n"
            "avval kanalga obuna bo'ling 👇",
            reply_markup=keyboard
        )

@dp.callback_query(lambda c: c.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.edit_text(
            "✅ Obuna tasdiqlandi!\n\n"
            "Modlarni kanal postlaridagi havolalar orqali yuklab oling! 👇\n"
            "👉 https://t.me/BeamModsStudio"
        )
    else:
        await callback.answer("❌ Hali obuna bo'lmagansiz!", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("recheck_"))
async def recheck_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    mod_key = callback.data.replace("recheck_", "")

    if await is_subscribed(user_id):
        if mod_key in MODS:
            await callback.message.delete()
            await callback.message.answer_document(
                document=MODS[mod_key]["file_id"],
                caption=f"🚗 {MODS[mod_key]['name']} modi\n✅ BeamNG mods papkasiga tashlang!"
            )
    else:
        await callback.answer("❌ Hali obuna bo'lmagansiz!", show_alert=True)

async def main():
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

asyncio.run(main())