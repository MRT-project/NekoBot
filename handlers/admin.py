import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberOwner, ChatMemberAdministrator, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from database.db import (
    set_log_channel, enable_auto_mute, add_badword,
    reset_warning, get_log_channel, is_auto_mute_enabled,
    set_antilink, is_antilink_enabled, get_badwords,
    del_badword, set_antibadword, is_antibadword_enabled,
    set_autoclean, is_autoclean_enabled, set_auto_mute,
    get_stats
)
from .utils import is_admin, extract_user, is_admin_group


START_TIME = time.time()

def full_permissions():
    """Semua izin aktif (unmuteall)"""
    return ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    stat = get_stats(gid)

    uptime = int(time.time() - START_TIME)
    hours, minutes = divmod(uptime // 60, 60)

    members = await context.bot.get_chat_member_count(update.effective_chat.id)

    text = (
        "📊 <b>Group Statistics</b>\n\n"
        f"🔇 Mutes: <b>{stat['mute']}</b>\n"
        f"⚠️ Warnings: <b>{stat['warn']}</b>\n"
        f"🚫 Bans: <b>{stat['ban']}</b>\n"
        f"👥 Members: <b>{members}</b>\n"
        f"⏱️ Uptime: <b>{hours}h {minutes}m</b>"
    )

    await update.message.reply_text(text, parse_mode="HTML")

async def setantibadword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admin only.")
    
    if len(context.args) != 1 or context.args[0] not in ["on", "off"]:
        return await update.message.reply_text("Usage: /setantibadword on|off")

    enabled = context.args[0] == "on"
    set_antibadword(update.effective_chat.id, enabled)
    await update.message.reply_text(f"🚫 Anti-badword {'enabled' if enabled else 'disabled'}.")

async def listbadwords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    words = get_badwords(update.effective_chat.id)
    if not words:
        return await update.message.reply_text("📭 No badwords set.")
    wordlist = "\n".join(f"• {w}" for w in sorted(words))
    await update.message.reply_text(f"🚫 <b>Badwords List:</b>\n{wordlist}", parse_mode="HTML")

async def setantilink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admin only.")
    if len(context.args) != 1 or context.args[0] not in ["on", "off"]:
        return await update.message.reply_text("Usage: /setantilink on|off")
    enabled = context.args[0] == "on"
    set_antilink(update.effective_chat.id, enabled)
    await update.message.reply_text(f"🔗 Anti-link {'enabled' if enabled else 'disabled'}.")

async def setlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admin only.")
    if len(context.args) != 1:
        return await update.message.reply_text("Usage: /setlog <code>channel_id</code>", parse_mode="HTML")

    set_log_channel(update.effective_chat.id, int(context.args[0]))
    await update.message.reply_text("✅ Log channel saved.")

async def setmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admin only.")
    if len(context.args) != 1 or context.args[0] not in ["on", "off"]:
        return await update.message.reply_text("Usage: /setmute on|off")
    enable_auto_mute(update.effective_chat.id, context.args[0] == "on")
    await update.message.reply_text(f"🔒 Auto mute {'enabled' if context.args[0]=='on' else 'disabled'}.")

async def addbad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admin only.")
    if not context.args:
        return await update.message.reply_text("Usage: /addbadword <word>")
    for word in context.args:
        add_badword(update.effective_chat.id, word)
    await update.message.reply_text("✅ Badword(s) added.")

async def deletebadword(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admin only.")
    
    if not context.args:
        return await update.message.reply_text("Usage: /delbadword <word>")

    deleted = []
    not_found = []
    for word in context.args:
        if del_badword(update.effective_chat.id, word):
            deleted.append(word)
        else:
            not_found.append(word)

    reply = ""
    if deleted:
        reply += f"✅ Removed: {' | '.join(deleted)}\n"
    if not_found:
        reply += f"⚠️ Not Found: {' | '.join(not_found)}"

    await update.message.reply_text(reply.strip())

async def warnreset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admin only.")
    user = await extract_user(update, context)
    if not user:
        return await update.message.reply_text("Usage: /warnreset [reply/@username]")
    reset_warning(update.effective_chat.id, user.id)
    await update.message.reply_text(f"🔄 Warning reset for {user.full_name}.")

async def groupinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    mute = is_auto_mute_enabled(gid)
    log_channel = get_log_channel(gid)
    await update.message.reply_text(
        f"ℹ️ <b>Group Info</b>\n"
        f"ID: <code>{gid}</code>\n"
        f"Auto Mute: {'ON' if mute else 'OFF'}\n"
        f"Log Channel: {log_channel or 'Not set'}",
        parse_mode="HTML"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    chat = await context.bot.get_chat(gid)
    perms = chat.permissions or ChatPermissions()
    me = await context.bot.get_chat_member(gid, context.bot.id)

    status_text = (
        "<b>📊 Group Status</b>\n"
        "<blockquote>"
        f"• Anti-Link: {'✔️' if is_antilink_enabled(gid) else '❌'}\n"
        f"• Anti-Badword: {'✔️' if is_antibadword_enabled(gid) else '❌'}\n"
        f"• Auto-Mute Join: {'✔️' if is_auto_mute_enabled(gid) else '❌'}\n"
        f"• Auto-Clean Commands: {'✔️' if is_autoclean_enabled(gid) else '❌'}\n"
        f"• Log Channel: <code>{get_log_channel(gid) or 'Not set'}</code>"
        "</blockquote>\n\n"

        "<b>🔐 Izin Anggota Non-Admin:</b>\n"
        "<blockquote>"
        f"• Kirim Pesan: {'✔️' if getattr(perms, 'can_send_messages', False) else '❌'}\n"
        f"• Foto: {'✔️' if getattr(perms, 'can_send_photos', False) else '❌'}\n"
        f"• Video: {'✔️' if getattr(perms, 'can_send_videos', False) else '❌'}\n"
        f"• Stiker & GIF: {'✔️' if getattr(perms, 'can_send_other_messages', False) else '❌'}\n"
        f"• Musik: {'✔️' if getattr(perms, 'can_send_audios', False) else '❌'}\n"
        f"• Berkas (document): {'✔️' if getattr(perms, 'can_send_documents', False) else '❌'}\n"
        f"• Pesan Suara: {'✔️' if getattr(perms, 'can_send_voice_notes', False) else '❌'}\n"
        f"• Pesan Video: {'✔️' if getattr(perms, 'can_send_video_notes', False) else '❌'}\n"
        f"• Tautan Tertanam: {'✔️' if getattr(perms, 'can_add_web_page_previews', False) else '❌'}\n"
        f"• Poll: {'✔️' if getattr(perms, 'can_send_polls', False) else '❌'}"
        "</blockquote>\n\n"

        "<b>👮 Status Bot:</b>\n"
        "<blockquote>"
        f"• Admin: {'✔️' if me.status == 'administrator' else '❌'}\n"
        f"• Bisa batasi anggota: {'✔️' if me.can_restrict_members else '❌'}"
        "</blockquote>"
    )

    await update.message.reply_text(status_text, parse_mode="HTML")

async def setautoclean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admin only.")

    if len(context.args) != 1 or context.args[0] not in ["on", "off"]:
        return await update.message.reply_text("Usage: /setautoclean on|off")

    enabled = context.args[0] == "on"
    set_autoclean(update.effective_chat.id, enabled)
    await update.message.reply_text(f"🧹 Auto-clean {'enabled' if enabled else 'disabled'}.")

async def build_settings_keyboard(gid, context):
    chat = await context.bot.get_chat(gid)
    perms = chat.permissions or ChatPermissions()

    keyboard = [
        [InlineKeyboardButton(f"🔗 Anti-Link: {'ON ✅' if is_antilink_enabled(gid) else 'OFF ❌'}", callback_data='toggle_antilink')],
        [InlineKeyboardButton(f"🤬 Anti-Badword: {'ON ✅' if is_antibadword_enabled(gid) else 'OFF ❌'}", callback_data='toggle_antibadword')],
        [InlineKeyboardButton(f"🔇 Auto-Mute: {'ON ✅' if is_auto_mute_enabled(gid) else 'OFF ❌'}", callback_data='toggle_automute')],
        [InlineKeyboardButton(f"🧹 Auto-Clean: {'ON ✅' if is_autoclean_enabled(gid) else 'OFF ❌'}", callback_data='toggle_autoclean')],
        [
            InlineKeyboardButton(f"📝 Kirim Pesan {'✅' if getattr(perms, 'can_send_messages', False) else '❌'}", callback_data="perm_text"),
            InlineKeyboardButton(f"📸 Foto {'✅' if getattr(perms, 'can_send_photos', False) else '❌'}", callback_data="perm_photos"),
        ],
        [
            InlineKeyboardButton(f"🎞️ Video {'✅' if getattr(perms, 'can_send_videos', False) else '❌'}", callback_data="perm_videos"),
            InlineKeyboardButton(f"🎭 Stiker & GIF {'✅' if getattr(perms, 'can_send_other_messages', False) else '❌'}", callback_data="perm_sticker"),
        ],
        [
            InlineKeyboardButton(f"🎵 Musik {'✅' if getattr(perms, 'can_send_audios', False) else '❌'}", callback_data="perm_musik"),
            InlineKeyboardButton(f"📎 Berkas {'✅' if getattr(perms, 'can_send_documents', False) else '❌'}", callback_data="perm_berkas"),
        ],
        [
            InlineKeyboardButton(f"🔊 Pesan Suara {'✅' if getattr(perms, 'can_send_voice_notes', False) else '❌'}", callback_data="perm_voice"),
            InlineKeyboardButton(f"📹 Pesan Video {'✅' if getattr(perms, 'can_send_video_notes', False) else '❌'}", callback_data="perm_videonotes"),
        ],
        [
            InlineKeyboardButton(f"🌐 Tautan Tertanam {'✅' if getattr(perms, 'can_add_web_page_previews', False) else '❌'}", callback_data="perm_link"),
            InlineKeyboardButton(f"📊 Poll {'✅' if getattr(perms, 'can_send_polls', False) else '❌'}", callback_data="perm_poll"),
        ],
        [InlineKeyboardButton("🔄 Reset Semua Izin", callback_data="perm_reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_group(update):
        return await update.message.reply_text("❌ Hanya admin yang bisa membuka menu ini.")

    gid = update.effective_chat.id
    markup = await build_settings_keyboard(gid, context)

    await update.message.reply_text(
        "⚙️ <b>Pengaturan Grup</b>\n\n"
        "Gunakan tombol di bawah untuk mengaktifkan/mematikan fitur bot dan izin anggota.",
        parse_mode="HTML",
        reply_markup=markup
    )

async def button_toggle_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gid = query.message.chat.id

    # === Toggle fitur ON/OFF dari database ===
    toggles = {
        "toggle_antilink": (is_antilink_enabled, set_antilink),
        "toggle_antibadword": (is_antibadword_enabled, set_antibadword),
        "toggle_automute": (is_auto_mute_enabled, set_auto_mute),
        "toggle_autoclean": (is_autoclean_enabled, set_autoclean),
    }

    if query.data in toggles:
        check_func, toggle_func = toggles[query.data]
        toggle_func(gid, not check_func(gid))

    # === Toggle izin anggota (perm_...) ===
    elif query.data.startswith("perm_"):
        mode = query.data.replace("perm_", "")
        chat = await context.bot.get_chat(gid)
        current = chat.permissions or ChatPermissions()

        # Ambil semua izin saat ini
        perms = {
            "can_send_messages": current.can_send_messages or False,
            "can_send_other_messages": current.can_send_other_messages or False,
            "can_send_polls": current.can_send_polls or False,
            "can_add_web_page_previews": current.can_add_web_page_previews or False,
            "can_send_audios": current.can_send_audios or False,
            "can_send_documents": current.can_send_documents or False,
            "can_send_photos": current.can_send_photos or False,
            "can_send_videos": current.can_send_videos or False,
            "can_send_video_notes": current.can_send_video_notes or False,
            "can_send_voice_notes": current.can_send_voice_notes or False,
        }

        try:
            if mode == "text":
                if perms["can_send_messages"]:
                    for key in perms:
                        perms[key] = False
                else:
                    perms["can_send_messages"] = True
            elif mode == "photos":
                perms["can_send_photos"] = not perms["can_send_photos"]
            elif mode == "videos":
                perms["can_send_videos"] = not perms["can_send_videos"]
            elif mode == "sticker":
                perms["can_send_other_messages"] = not perms["can_send_other_messages"]
            elif mode == "musik":
                perms["can_send_audios"] = not perms["can_send_audios"]
            elif mode == "berkas":
                perms["can_send_documents"] = not perms["can_send_documents"]
            elif mode == "voice":
                perms["can_send_voice_notes"] = not perms["can_send_voice_notes"]
            elif mode == "videonotes":
                perms["can_send_video_notes"] = not perms["can_send_video_notes"]
            elif mode == "link":
                perms["can_add_web_page_previews"] = not perms["can_add_web_page_previews"]
            elif mode == "poll":
                perms["can_send_polls"] = not perms["can_send_polls"]
            elif mode == "reset":
                for key in perms:
                    perms[key] = True
            else:
                return await query.answer("❌ Mode tidak dikenali.")

            # Terapkan perubahan
            new_perms = ChatPermissions(**perms)
            await context.bot.set_chat_permissions(gid, new_perms)

            # Log ke channel
            log_channel = get_log_channel(gid)
            if log_channel:
                await context.bot.send_message(
                    chat_id=log_channel,
                    text=(
                        f"📣 <b>Perubahan Izin</b>\n"
                        f"👤 Oleh: {query.from_user.mention_html()}\n"
                        f"📦 Aksi: <code>{query.data}</code>"
                    ),
                    parse_mode="HTML"
                )

        except BadRequest as e:
            return await query.answer(f"❌ Gagal ubah izin: {e}", show_alert=True)

    # === Refresh tampilan tombol
    try:
        markup = await build_settings_keyboard(gid, context)
        await query.edit_message_reply_markup(reply_markup=markup)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise e

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mempin pesan yang dibalas.

    Contoh:
    Balas pesan → /pin
    Balas pesan → /pin silent (tanpa notifikasi)
    """
    if not await is_admin(update):
        return await update.message.reply_text("❌ Hanya admin yang bisa menggunakan perintah ini.")

    if not update.message.reply_to_message:
        return await update.message.reply_text("❗Perintah ini harus digunakan dengan membalas pesan.")

    silent = "silent" in context.args
    await context.bot.pin_chat_message(
        chat_id=update.effective_chat.id,
        message_id=update.message.reply_to_message.message_id,
        disable_notification=silent
    )
    await update.message.reply_text("📌 Pesan berhasil dipin." + (" (tanpa notifikasi)" if silent else ""))

async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Melepas pin dari pesan yang dibalas.

    Contoh:
    Balas pesan → /unpin
    """
    if not await is_admin(update):
        return await update.message.reply_text("❌ Hanya admin yang bisa menggunakan perintah ini.")

    if not update.message.reply_to_message:
        return await update.message.reply_text("❗Perintah ini harus digunakan dengan membalas pesan yang ingin dilepas pin-nya.")

    await context.bot.unpin_chat_message(
        chat_id=update.effective_chat.id,
        message_id=update.message.reply_to_message.message_id
    )
    await update.message.reply_text("🚫 Pesan tidak dipin lagi.")

async def unpinall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menghapus semua pesan yang dipin di grup.

    Contoh:
    /unpinall
    """
    if not await is_admin(update):
        return await update.message.reply_text("❌ Hanya admin yang bisa menggunakan perintah ini.")

    await context.bot.unpin_all_chat_messages(chat_id=update.effective_chat.id)
    await update.message.reply_text("🧹 Semua pesan yang dipin telah dihapus.")

async def kick_deactivated(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengeluarkan semua akun yang sudah dihapus (nonaktif).

    Contoh:
    /kickdeactivated
    """
    if not await is_admin(update):
        return await update.message.reply_text("❌ Hanya admin yang bisa menggunakan perintah ini.")

    await update.message.reply_text("🔍 Sedang memeriksa anggota...")

    chat = update.effective_chat
    kicked_count = 0

    try:
        async for member in context.bot.get_chat_administrators(chat.id):
            if member.user.id == context.bot.id:
                bot_can_restrict = member.can_restrict_members
                if not bot_can_restrict:
                    return await update.message.reply_text("❌ Bot tidak memiliki izin untuk mengeluarkan anggota.")
                break

        async for member in context.bot.get_chat_members(chat.id):
            if member.user.is_deleted:
                try:
                    await context.bot.ban_chat_member(chat.id, member.user.id)
                    await context.bot.unban_chat_member(chat.id, member.user.id)  # agar bisa join ulang
                    kicked_count += 1
                except Exception as e:
                    print(f"Gagal kick: {e}")

        if kicked_count:
            await update.message.reply_text(f"✅ {kicked_count} akun terhapus telah dikeluarkan.")
        else:
            await update.message.reply_text("✅ Tidak ada akun terhapus yang ditemukan.")
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi kesalahan: {e}")

async def purge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menghapus banyak pesan mulai dari pesan yang dibalas.

    Contoh:
    Balas pesan lama → /purge
    """
    if not await is_admin(update):
        return await update.message.reply_text("❌ Hanya admin yang bisa menggunakan perintah ini.")

    if not update.message.reply_to_message:
        return await update.message.reply_text("❗Balas pesan yang ingin dijadikan titik awal penghapusan.")

    chat_id = update.effective_chat.id
    start_msg_id = update.message.reply_to_message.message_id
    end_msg_id = update.message.message_id

    deleted = 0
    failed = 0

    for msg_id in range(start_msg_id, end_msg_id + 1):
        try:
            await context.bot.delete_message(chat_id, msg_id)
            deleted += 1
        except:
            failed += 1

    await update.message.reply_text(f"🧹 <b>Pembersihan selesai</b>\n✅ Berhasil: {deleted} pesan\n⚠️ Gagal: {failed}", parse_mode="HTML")

async def setlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "supergroup":
        return await update.message.reply_text("❌ Perintah ini hanya bisa digunakan di grup.")

    if not await is_admin(update):
        return await update.message.reply_text("❌ Hanya admin yang bisa mengatur log channel.")

    cid = update.effective_chat.id
    set_log_channel(cid, cid)
    await update.message.reply_text("✅ Channel log berhasil disetel ke grup ini.")

async def muteall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Membisukan semua anggota grup (mute all)."""
    if not await is_admin(update):
        return await update.message.reply_text("❌ Hanya admin yang bisa melakukan ini.")
    
    perms = ChatPermissions()  # Semua False
    await context.bot.set_chat_permissions(update.effective_chat.id, perms)
    await update.message.reply_text("🔇 Semua anggota telah dibisukan.")

async def unmuteall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Membuka mute semua anggota (unmute all)."""
    if not await is_admin(update):
        return await update.message.reply_text("❌ Hanya admin yang bisa melakukan perintah ini.")

    await context.bot.set_chat_permissions(update.effective_chat.id, full_permissions())
    await update.message.reply_text("🔊 Semua anggota telah di-unmute.")
