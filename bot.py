import os
import json
import re
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.deep_linking import decode_payload

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
BOT_TOKEN: str  = os.getenv("BOT_TOKEN", "8665911741:AAFjdUnqWfFYWExSkyrR_PraETwY8JPdQJc")
ADMIN_ID:  int  = int(os.getenv("ADMIN_ID", "1529212224"))
CHANNEL_ID: str = os.getenv("CHANNEL_ID", "@BeamModsStudio")   # used for subscription check
MODS_FILE:  str = "mods.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  BOT & DISPATCHER
# ─────────────────────────────────────────────
bot = Bot(
    token=BOT_TOKEN, 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # ← Yangi standart bo'yicha shunday yoziladi
)
dp  = Dispatcher(storage=MemoryStorage())

# ─────────────────────────────────────────────
#  PERSISTENCE HELPERS
# ─────────────────────────────────────────────
def load_mods() -> dict:
    """Load the mods catalogue from disk.  Returns an empty dict on first run."""
    if not os.path.exists(MODS_FILE):
        return {}
    try:
        with open(MODS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, IOError):
        logger.warning("mods.json is corrupt or unreadable – starting fresh.")
        return {}


def save_mods(mods: dict) -> None:
    """Persist the mods catalogue to disk atomically."""
    with open(MODS_FILE, "w", encoding="utf-8") as fh:
        json.dump(mods, fh, ensure_ascii=False, indent=2)


# In-memory catalogue — loaded once at startup, kept in sync via save_mods()
MODS: dict = load_mods()

# ─────────────────────────────────────────────
#  UTILITY HELPERS
# ─────────────────────────────────────────────
def slugify(text: str) -> str:
    """
    Convert an arbitrary string into a compact URL-safe slug.
    Example: "Indian Cow"  → "indiancow"
             "Nexia3 Optimal" → "nexia3optimal"
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)   # strip non-alphanumeric (except spaces)
    text = re.sub(r"\s+", "", text)             # remove all whitespace
    return text or "mod"


def make_mod_key(mod_name: str) -> str:
    """Return a guaranteed-unique slug key for *mod_name*."""
    base = slugify(mod_name)
    if base not in MODS:
        return base
    # Append numeric suffix until unique
    counter = 2
    while f"{base}{counter}" in MODS:
        counter += 1
    return f"{base}{counter}"


def make_post_text(mod_name: str) -> str:
    """Build the structured Uzbek promotional post (HTML)."""
    return (
        f"🚗 <b>YANGI MOD: {mod_name}</b>\n"
        "\n"
        "📌 <b>Tavsif:</b>\n"
        "BeamNG.drive uchun sifatli yangi premium modifikatsiya!\n"
        "\n"
        "⚙️ <b>Xususiyatlari:</b>\n"
        "- Yuqori sifatli model\n"
        "- Realistic fizika\n"
        "- BeamNG.drive ga mos\n"
        "\n"
        "📥 <b>Yuklab olish — BEPUL!</b>\n"
        "\n"
        "✅ Yuklab olish uchun kanalga obuna bo'lish talab etiladi!\n"
        "📢 Kanal: @BeamModsStudio"
    )


def make_download_keyboard(mod_key: str) -> InlineKeyboardMarkup:
    """Inline keyboard with the deep-link download button."""
    url = f"https://t.me/BeamModsStudio_bot?start=download_{mod_key}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Yuklab olish", url=url)]
        ]
    )


async def is_subscribed(user_id: int) -> bool:
    """Check whether *user_id* is a member of CHANNEL_ID."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception as exc:
        logger.warning("Subscription check failed for %s: %s", user_id, exc)
        return False


# ─────────────────────────────────────────────
#  FSM STATE GROUPS
# ─────────────────────────────────────────────
class UploadMod(StatesGroup):
    waiting_for_zip   = State()   # Step 1 – admin sends .zip document
    waiting_for_photo = State()   # Step 2 – admin sends cover photo


# ─────────────────────────────────────────────
#  ADMIN COMMAND: /upload  (enters FSM)
# ─────────────────────────────────────────────
@dp.message(Command("upload"), F.from_user.id == ADMIN_ID)
async def cmd_upload(message: types.Message, state: FSMContext) -> None:
    """Admin triggers the upload wizard with /upload."""
    await state.set_state(UploadMod.waiting_for_zip)
    await message.answer(
        "📂 <b>Yangi mod yuklash jarayoni boshlandi.</b>\n\n"
        "Iltimos, <b>.zip</b> formatidagi mod faylini yuboring:"
    )


# ─────────────────────────────────────────────
#  STEP 1 – Admin sends .zip document
# ─────────────────────────────────────────────
@dp.message(UploadMod.waiting_for_zip, F.from_user.id == ADMIN_ID, F.document)
async def handle_zip_upload(message: types.Message, state: FSMContext) -> None:
    """Receive the .zip archive; validate format; move to photo step."""
    doc = message.document

    # ── Validate file extension ──────────────────────────────────────────────
    if not doc.file_name or not doc.file_name.lower().endswith(".zip"):
        await message.answer(
            "⚠️ Noto'g'ri fayl formati.\n"
            "Faqat <b>.zip</b> kengaytmali fayllarni yuboring."
        )
        return  # stay in waiting_for_zip

    # ── Derive mod_name and mod_key ──────────────────────────────────────────
    raw_name: str = doc.file_name
    mod_name: str = raw_name.rsplit(".", 1)[0].replace("_", " ").strip()
    mod_key:  str = make_mod_key(mod_name)

    # ── Persist interim data in FSM state ────────────────────────────────────
    await state.update_data(
        zip_file_id=doc.file_id,
        mod_name=mod_name,
        mod_key=mod_key,
    )
    await state.set_state(UploadMod.waiting_for_photo)

    await message.answer(
        f"📁 Mod fayli qabul qilindi.\n"
        f"🏷 <b>Nomi:</b> {mod_name}\n"
        f"🔑 <b>Kalit:</b> <code>{mod_key}</code>\n\n"
        "Endi ushbu mod uchun rasm (photo) yuboring:"
    )


# ── Guard: wrong file type while waiting for .zip (admin only) ──────────────
@dp.message(UploadMod.waiting_for_zip, F.from_user.id == ADMIN_ID)
async def handle_zip_wrong_type(message: types.Message) -> None:
    await message.answer(
        "⚠️ Kutilmagan xabar turi.\n"
        "Faqat <b>.zip</b> kengaytmali fayl yuboring, yoki /cancel bosing."
    )


# ─────────────────────────────────────────────
#  STEP 2 – Admin sends cover photo
# ─────────────────────────────────────────────
@dp.message(UploadMod.waiting_for_photo, F.from_user.id == ADMIN_ID, F.photo)
async def handle_photo_upload(message: types.Message, state: FSMContext) -> None:
    """Receive the cover photo; finalise mod entry; send channel-ready preview."""
    # Highest resolution = last element in the photo array
    photo_id: str = message.photo[-1].file_id

    # ── Retrieve step-1 data from FSM state ──────────────────────────────────
    data      = await state.get_data()
    zip_file_id: str = data["zip_file_id"]
    mod_name:    str = data["mod_name"]
    mod_key:     str = data["mod_key"]

    # ── Persist to global MODS dict and mods.json ─────────────────────────────
    MODS[mod_key] = {
        "file_id":  zip_file_id,
        "name":     mod_name,
        "photo_id": photo_id,   # stored for potential future use
    }
    save_mods(MODS)

    # ── Build promotional post ────────────────────────────────────────────────
    post_text = make_post_text(mod_name)
    keyboard  = make_download_keyboard(mod_key)

    # ── Clear FSM state ───────────────────────────────────────────────────────
    await state.clear()

    # ── Send success notice + channel-ready preview ───────────────────────────
    await message.answer(
        f"✅ <b>Mod muvaffaqiyatli saqlandi!</b>\n"
        f"🔑 Kalit: <code>{mod_key}</code>\n\n"
        "Quyidagi postni kanalingizga yo'naltiring (Forward):"
    )
    await message.answer_photo(
        photo=photo_id,
        caption=post_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ── Guard: wrong type while waiting for photo (admin only) ───────────────────
@dp.message(UploadMod.waiting_for_photo, F.from_user.id == ADMIN_ID)
async def handle_photo_wrong_type(message: types.Message) -> None:
    await message.answer(
        "⚠️ Rasm kutilmoqda.\n"
        "Iltimos, faqat <b>rasm (photo)</b> yuboring, yoki /cancel bosing."
    )


# ─────────────────────────────────────────────
#  /cancel – abort upload wizard at any step
# ─────────────────────────────────────────────
@dp.message(Command("cancel"), F.from_user.id == ADMIN_ID)
async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("ℹ️ Hozirda faol jarayon yo'q.")
        return
    await state.clear()
    await message.answer("❌ Yuklash jarayoni bekor qilindi.")


# ─────────────────────────────────────────────
#  GUARD: non-admin messages during any FSM step
# ─────────────────────────────────────────────
@dp.message(UploadMod.waiting_for_zip)
@dp.message(UploadMod.waiting_for_photo)
async def guard_non_admin_in_fsm(message: types.Message) -> None:
    """Silently reject non-admin messages that arrive while FSM is active."""
    # Ignore completely – do not acknowledge to avoid confusion
    pass


# ─────────────────────────────────────────────
#  /start – deep-link & subscription gate
# ─────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    args: str = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""

    # ── Deep-link download flow ───────────────────────────────────────────────
    if args.startswith("download_"):
        mod_key = args[len("download_"):]

        # Check subscription first
        subscribed = await is_subscribed(message.from_user.id)
        if not subscribed:
            join_button = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="📢 Kanalga obuna bo'lish",
                        url=f"https://t.me/{CHANNEL_ID.lstrip('@')}"
                    )
                ]]
            )
            await message.answer(
                "🔒 <b>Faylni yuklab olish uchun avval kanalga obuna bo'lishingiz kerak!</b>\n\n"
                "Obuna bo'lgach, ushbu havolaga qaytib kiring:",
                reply_markup=join_button,
            )
            return

        # Deliver the file
        mod = MODS.get(mod_key)
        if not mod:
            await message.answer("❌ Bunday mod topilmadi. Havola eskirgan bo'lishi mumkin.")
            return

        await message.answer_document(
            document=mod["file_id"],
            caption=(
                f"📦 <b>{mod['name']}</b>\n\n"
                "BeamNG.drive uchun mod muvaffaqiyatli yuklandi!\n"
                "📢 Kanal: @BeamModsStudio"
            ),
        )
        return

    # ── Default welcome ───────────────────────────────────────────────────────
    await message.answer(
        "👋 <b>BeamModsStudio botiga xush kelibsiz!</b>\n\n"
        "Bu bot orqali BeamNG.drive modlarini bepul yuklab olishingiz mumkin.\n\n"
        "📢 Kanalimizga obuna bo'ling va modlardan bahramand bo'ling: @BeamModsStudio"
    )


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
async def main() -> None:
    logger.info("BeamModsStudio bot starting…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
