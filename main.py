import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8749766405:AAEzb7UDuzB_Uf4b6C1XumNzONT2-jSZHTY'
ADMINS = [5305209814, 1529212224]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

conn = sqlite3.connect('/data/laboratoriya.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS metodlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metod_nomi TEXT UNIQUE,
    norma TEXT,
    javob TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS moddalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modda_nomi TEXT UNIQUE,
    metod_id INTEGER,
    FOREIGN KEY(metod_id) REFERENCES metodlar(id)
)''')
conn.commit()

boshlangich_metodlar = [
    {
        "metod": "ГФ РУз (2.2.29)",
        "norma": "Время удерживания основного пика на хроматограмме испытуемого образца должно быть идентично времени удерживания основного пика на хроматограмме стандартного образца",
        "javob": "Время удерживания основного пика на хроматограмме испытуемого раствора соответствует времени удерживания основного пика на хроматограмме стандартного образца."
    },
    {
        "metod": "ГФ РФ XIII (ОФС. 1.2.3.0017.15)",
        "norma": "Время удерживания основного пика на хроматограмме испытуемого образца должно быть идентично времени удерживания основного пика на хроматограмме стандартного образца",
        "javob": "Время удерживания основного пика на хроматограмме испытуемого раствора соответствует времени удерживания основного пика на хроматограмме стандартного образца."
    },
    {
        "metod": "ГФ РУз (2.2.28)",
        "norma": "Время выхода основного пика на хроматограмме испытуемого раствора должно соответствовать времени выхода основного пика на хроматограмме стандартного образца.",
        "javob": "Время выхода основного пика на хроматограмме испытуемого раствора соответствует времени выхода основного пика на хроматограмме стандартного образца."
    },
    {
        "metod": "ГФ РУз (2.2.25)",
        "norma": "Максимумы и минимумы спектра поглощения испытуемого образца должны совпадать с максимумами и минимумами спектра поглощения стандартного образца",
        "javob": "Максимумы и минимумы спектра поглощения испытуемого образца совпадают с максимумами и минимумами спектра поглощения стандартного образца"
    },
    {
        "metod": "ГФ РУз том I (2.3.1)",
        "norma": "Положительная реакция",
        "javob": "Положительная реакция"
    },
    {
        "metod": "USP <541>",
        "norma": "Положительная реакция",
        "javob": "Положительная реакция"
    },
    {
        "metod": "ГФ РУз (2.2.7)",
        "norma": "Удельное оптическое вращение выраженное в угловых градусах при длине волны линии D спектра натрия (при 589,3 нм) должна соответствовать указанному удельному оптическому вращению выраженному в угловых градусах",
        "javob": "Удельное оптическое вращение, выраженное в угловых градусах при длине волны линии D спектра натрия (589,3 нм), соответствует указанному удельному оптическому вращению, выраженному в угловых градусах"
    }
]

for m in boshlangich_metodlar:
    try:
        cursor.execute(
            "INSERT INTO metodlar (metod_nomi, norma, javob) VALUES (?, ?, ?)",
            (m["metod"], m["norma"], m["javob"])
        )
    except sqlite3.IntegrityError:
        pass
conn.commit()


# --- FSM ---
class NewModdaState(StatesGroup):
    waiting_for_metod_selection = State()
    waiting_for_new_metod_name = State()
    waiting_for_norma = State()
    waiting_for_javob = State()


class EditMetodState(StatesGroup):
    waiting_for_new_norma = State()
    waiting_for_new_javob = State()


# --- /start ---
@dp.message(F.text == "/start")
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.reply(
        "⚡️ Laboratoriya botiga xush kelibsiz!\n\n"
        "Modda nomini yuboring (Masalan: vitamin C):"
    )


# --- MODDA QIDIRISH ---
@dp.message(F.text & ~F.text.startswith('/'))
async def search_modda(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return

    modda_input = message.text.strip().lower()

    cursor.execute('''
        SELECT m.modda_nomi, mt.metod_nomi, mt.norma, mt.javob, mt.id
        FROM moddalar m
        JOIN metodlar mt ON m.metod_id = mt.id
        WHERE LOWER(m.modda_nomi) = ?
    ''', (modda_input,))

    result = cursor.fetchone()

    if result:
        m_nomi, metod, norma, javob, metod_id = result
        text = (
            f"📄 *Modda nomi:* {m_nomi}\n"
            f"🔢 *Method raqami:* {metod}\n\n"
            f"📊 *Norma:*\n{norma}\n\n"
            f"📝 *Javob:*\n{javob}"
        )
        if message.from_user.id in ADMINS:
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="✏️ Metodni tahrirlash",
                    callback_data=f"edit_{metod_id}"
                )
            ]])
            await message.reply(text, parse_mode="Markdown", reply_markup=kb)
        else:
            await message.reply(text, parse_mode="Markdown")
    else:
        if message.from_user.id in ADMINS:
            await state.update_data(new_modda=message.text.strip())

            cursor.execute("SELECT id, metod_nomi FROM metodlar")
            methods = cursor.fetchall()

            buttons = []
            for m_id, m_name in methods:
                buttons.append([
                    InlineKeyboardButton(text=m_name, callback_data=f"select_m_{m_id}")
                ])
            buttons.append([
                InlineKeyboardButton(text="➕ Yangi metod yaratish", callback_data="create_new_metod")
            ])
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)

            await message.reply(
                f"❓ *'{message.text}'* topilmadi\.\n\n"
                f"Ushbu modda qaysi metodga tegishli? Ro'yxatdan tanlang:",
                reply_markup=kb,
                parse_mode="MarkdownV2"
            )
            await state.set_state(NewModdaState.waiting_for_metod_selection)
        else:
            await message.reply("❌ Bu modda bazada topilmadi. Iltimos adminga murojaat qiling.")


# --- METOD TANLASH ---
@dp.callback_query(F.data.startswith('select_m_'), NewModdaState.waiting_for_metod_selection)
async def process_method_selection(callback_query: types.CallbackQuery, state: FSMContext):
    metod_id = int(callback_query.data.split('_')[2])
    data = await state.get_data()

    try:
        cursor.execute(
            "INSERT INTO moddalar (modda_nomi, metod_id) VALUES (?, ?)",
            (data['new_modda'], metod_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        await callback_query.answer()
        await bot.send_message(
            callback_query.from_user.id,
            f"⚠️ *{data['new_modda']}* moddasi bazada allaqachon mavjud!",
            parse_mode="Markdown"
        )
        await state.clear()
        return

    cursor.execute("SELECT metod_nomi FROM metodlar WHERE id = ?", (metod_id,))
    m_name = cursor.fetchone()[0]

    await callback_query.answer()
    await bot.send_message(
        callback_query.from_user.id,
        f"✅ *{data['new_modda']}* moddasi *{m_name}* metodiga bog'landi!",
        parse_mode="Markdown"
    )
    await state.clear()


# --- YANGI METOD YARATISH ---
@dp.callback_query(F.data == "create_new_metod", NewModdaState.waiting_for_metod_selection)
async def trigger_new_method_creation(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await bot.send_message(
        callback_query.from_user.id,
        "Yangi *Method raqamini* kiriting:\nMasalan: `ГФ РУз (2.2.10)`",
        parse_mode="Markdown"
    )
    await state.set_state(NewModdaState.waiting_for_new_metod_name)


@dp.message(NewModdaState.waiting_for_new_metod_name)
async def process_new_metod_name(message: types.Message, state: FSMContext):
    await state.update_data(metod_nomi=message.text.strip())
    await message.reply("Ushbu metod uchun *Norma* matnini kiriting:", parse_mode="Markdown")
    await state.set_state(NewModdaState.waiting_for_norma)


@dp.message(NewModdaState.waiting_for_norma)
async def process_norma(message: types.Message, state: FSMContext):
    await state.update_data(norma=message.text.strip())
    await message.reply("Endi *Javob* shablonini kiriting:", parse_mode="Markdown")
    await state.set_state(NewModdaState.waiting_for_javob)


@dp.message(NewModdaState.waiting_for_javob)
async def process_javob(message: types.Message, state: FSMContext):
    data = await state.get_data()
    javob = message.text.strip()

    try:
        cursor.execute(
            "INSERT INTO metodlar (metod_nomi, norma, javob) VALUES (?, ?, ?)",
            (data['metod_nomi'], data['norma'], javob)
        )
        metod_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO moddalar (modda_nomi, metod_id) VALUES (?, ?)",
            (data['new_modda'], metod_id)
        )
        conn.commit()
        await message.reply("🎉 Yangi metod yaratildi va modda muvaffaqiyatli saqlandi!")
    except sqlite3.IntegrityError:
        await message.reply("❌ Bu metod bazada allaqachon mavjud.")

    await state.clear()


# --- TAHRIRLASH ---
@dp.callback_query(F.data.startswith('edit_'))
async def edit_callback(callback_query: types.CallbackQuery, state: FSMContext):
    metod_id = callback_query.data.split('_')[1]
    await state.update_data(edit_metod_id=metod_id)
    await callback_query.answer()
    await bot.send_message(
        callback_query.from_user.id,
        "YANGI *Norma* matnini kiriting:",
        parse_mode="Markdown"
    )
    await state.set_state(EditMetodState.waiting_for_new_norma)


@dp.message(EditMetodState.waiting_for_new_norma)
async def edit_norma_proc(message: types.Message, state: FSMContext):
    await state.update_data(new_norma=message.text.strip())
    await message.reply("Endi YANGI *Javob* shablonini kiriting:", parse_mode="Markdown")
    await state.set_state(EditMetodState.waiting_for_new_javob)


@dp.message(EditMetodState.waiting_for_new_javob)
async def edit_javob_proc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_javob = message.text.strip()

    cursor.execute(
        "UPDATE metodlar SET norma = ?, javob = ? WHERE id = ?",
        (data['new_norma'], new_javob, data['edit_metod_id'])
    )
    conn.commit()

    await message.reply("🔄 Metod ma'lumotlari muvaffaqiyatli o'zgartirildi!")
    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())