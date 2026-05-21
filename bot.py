from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import logging
import os

# --- SOZLAMALAR ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = "@BeamModsStudio"
# -----------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# --- MODLAR RO'YHATI ---
MODS = {
    "zaz_kpop": {
        "file_id": "BQACAgIAAxkBAANBag4SjOzv4tfVmDfXct--Q9yl9_gAArKiAAJgF4lLtmLe5C0yv6w7BA",
        "name": "Zaz Kpop"
    },
    "nokia_hammer": {
        "file_id": "BQACAgIAAxkBAANlag40ovguaXPZlsdfMpYOExbIVdUAAnyjAAIpZkBILBVHf71r23Y7BA",
        "name": "nokia_hammer"
    },
    "BMW_M3": {
        "file_id": "BQACAgIAAxkBAANpag45zF3k5QuErO8lIGge1tnoee8AAveUAAJ6bOBL06Qaf7slLeI7BA",
        "name": "BMW_M3"
    },
    "Cat_car": {
        "file_id": "BQACAgIAAxkBAANrag46p_ophZ1n8NwdUp93EN2x1pEAAumdAAJQEQFIjQABRcODde0UOwQ",
        "name": "Cat_car"
    },
    "Barbie_shrek": {
        "file_id": "BQACAgIAAxkBAAMragtkvVc37kBQ2rYwvDeqBxpOniAAAtifAAIIONlLsQeI1Sr59LU7BA",
        "name": "Barbie_shrek"
}
# ----------------------

async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    args = message.text.split()

    # Havola orqali kelgan bo'lsa
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

    # Oddiy /start
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

@dp.message(lambda m: m.document)
async def get_file_id(message: types.Message):
    file_id = message.document.file_id
    file_name = message.document.file_name
    await message.answer(
        f"📁 Fayl nomi: {file_name}\n"
        f"🔑 File ID:\n`{file_id}`"
    )

async def main():
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

asyncio.run(main())