# --- ADMIN: FAQAT ZIP FAYL YUBORILGANDA BAZAGA QO'SHISH VA POST QAYTARISH ---
@dp.message(lambda m: m.from_user.id == 1529212224 and m.document and m.document.file_name.endswith(".zip"))
async def admin_direct_zip_upload(message: types.Message):
    # 1. Fayl ID va asl nomini olamiz
    file_id = message.document.file_id
    raw_filename = message.document.file_name  # Masalan: "indiancow.zip" yoki "Nexia3_Optimal.zip"

    # 2. Fayl nomidan moshina nomini chiroyli qilib ajratib olamiz (.zip qismini o'chiramiz)
    # Tagchiziqlarni bo'shliqqa almashtiramiz (Nexia3_Optimal -> Nexia3 Optimal)
    mod_name = raw_filename.rsplit('.', 1)[0].replace('_', ' ').strip()
    
    # URL va start buyrug'i uchun xavfsiz kalit (Key) generatsiya qilamiz
    mod_key = make_mod_key(mod_name)

    # 3. MODS bazasiga (faylga) yangi modni qo'shish va saqlash
    MODS[mod_key] = {
        "file_id": file_id,
        "name": mod_name
    }
    save_mods(MODS)

    # 4. Standart tavsif matni
    # (Agar har safar har xil tavsif kerak bo'lmasa, shu standart matn juda chiroyli chiqadi)
    default_desc = "BeamNG.drive uchun sifatli yangi premium modifikatsiya!"

    # Kanbop chiroyli post matni va yuklash tugmasini tayyorlash
    post_text = make_post_text(mod_name, default_desc)
    keyboard = make_download_button(mod_key)

    # Bot adminning o'ziga tayyor kanal xabarini qaytaradi
    await message.answer(
        "✨ <b>Yangi mod bazaga qo'shildi va tayyor post yaratildi!</b>\n"
        "Quyidagi xabarni sotuv kanalingizga to'g'ridan-to'g'ri Forward (Yo'naltirish) qiling:\n"
        "----------------------------------------",
        parse_mode="HTML"
    )
    
    await message.answer(
        text=post_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )