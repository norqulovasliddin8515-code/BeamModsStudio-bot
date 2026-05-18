from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import logging

# --- SOZLAMALAR ---
import os
BOT_TOKEN = os.environ.get("8665911741:AAGIG8ojQiWtzc5pJapZZUQz2aAqu9jI4yA")
CHANNEL_ID = "@BeamModsStudio"  # masalan: @mymodchannel

# -----------------

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

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

    if await is_subscribed(user_id):
        await message.answer(
            f"✅ Salom {name}! Siz obunachisiz.\n\n"
            "Qaysi modni olmoqchisiz? Mod nomini yozing yoki /mods buyrug'ini bosing."
        )
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_ID[1:]}")],
            [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
        ])
        await message.answer(
            f"Salom {name}! 👋\n\n"
            "Modlarni olish uchun avval kanalga obuna bo'ling 👇",
            reply_markup=keyboard
        )

@dp.callback_query(lambda c: c.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if await is_subscribed(user_id):
        await callback.message.edit_text(
            "✅ Rahmat! Obuna tasdiqlandi.\n\n"
            "Modlarni ko'rish uchun /mods yozing."
        )
    else:
        await callback.answer(
            "❌ Siz hali obuna bo'lmagansiz!", show_alert=True
        )

@dp.message(lambda m: m.text == "/mods")
async def send_mods_list(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer("❌ Avval kanalga obuna bo'ling!")
        return

    await message.answer(
        "🚗 Mavjud modlar:\n\n"
        "1. /mod_supra — Toyota Supra\n"
        "2. /mod_bmw — BMW M5\n\n"
        "Kerakli modni tanlang!"
    )

@dp.message(lambda m: m.text == "/mod_supra")
async def send_supra(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer("❌ Avval kanalga obuna bo'ling!")
        return

    await message.answer_document(
        document=types.FSInputFile("mods/supra.zip"),
        caption="🚗 Toyota Supra modi\n✅ O'rnatish: mods papkasiga tashlang!"
    )

async def main():
    print("Bot ishga tushdi!")
    await dp.start_polling(bot)

asyncio.run(main())