from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ChatPermissions, InputFile, ChatMember, ChatMemberUpdated
)
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes, CallbackContext
from telegram.helpers import escape
from database.db import (
    add_group, get_log_channel, get_all_group_ids,
    is_auto_mute_enabled, delete_group
)
from config import BOT_NAME, BOT_VERSION
import datetime, os

command_registry = {}  # diisi dari main.py

# 📍 START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📖 Commands", callback_data="commands")],
        [InlineKeyboardButton(f"➕ Add {BOT_NAME}", url="https://t.me/YOURBOTUSERNAME?startgroup=true")]
    ]

    caption = (
        f"👋 <b>Welcome to {BOT_NAME} {BOT_VERSION}!</b>\n\n"
        f"🤖 {BOT_NAME} adalah asisten grup multifungsi yang dirancang untuk membantu mengelola grup kamu dengan lebih mudah dan aman.\n\n"
        "Fitur-fitur unggulan:\n"
        "🔨 Moderasi otomatis (ban, mute, warn, filter)\n"
        "🛡 Proteksi link, spam, badword\n"
        "📌 Auto welcome dan rules\n"
        "📈 Statistik grup & auto-clean\n"
        "🎉 Dan masih banyak lagi!\n\n"
        "💡 Gunakan tombol di bawah untuk menjelajahi semua perintah.\n"
        "Jika kamu adalah admin grup, tambahkan bot ini ke grup kamu sekarang!\n\n"
        "— Tim Dev Neko"
    )

    with open("assets/banner.png", "rb") as banner:
        await update.message.reply_photo(
            photo=banner,
            caption=caption,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# 📍 BUTTON HANDLER
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    message = query.message

    def is_media(msg):
        return msg.photo or msg.video or msg.document or msg.animation or msg.audio

    if query.data == "commands":
        keyboard = []
        row = []

        for i, cmd in enumerate(sorted(command_registry.keys()), 1):
            row.append(InlineKeyboardButton(f"/{cmd}", callback_data=f"help_{cmd}"))
            if i % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_start")])

        caption = "<b>📖 Daftar Perintah</b>\nKlik tombol di bawah untuk melihat penjelasan."

        if is_media(message):
            await message.edit_caption(caption=caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await message.edit_text(text=caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("help_"):
        cmd = query.data.replace("help_", "")
        handler = command_registry.get(cmd)
        doc = handler.__doc__ if handler else None
        desc = doc.strip() if doc else "❌ Tidak ada deskripsi."

        if "Contoh:" in desc:
            bagian = desc.split("Contoh:", 1)
            penjelasan = bagian[0].strip()
            contoh = bagian[1].strip()

            # Batasi panjang contoh agar tidak error
            if len(contoh) > 400:
                contoh = contoh[:400] + "..."

            caption = (
                f"📘 <b>/{cmd}</b>\n\n"
                f"{penjelasan}\n\n"
                f"📌 <b>Contoh:</b>\n"
                + "\n".join(f"• {line.strip()}" for line in contoh.splitlines())
            )
        else:
            caption = f"📘 <b>/{cmd}</b>\n\n{desc}"

        if len(caption) > 1024:
            caption = caption[:1000] + "...\n\n<i>Deskripsi dipotong.</i>"

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="commands")]])

        if is_media(message):
            await message.edit_caption(caption=caption, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await message.edit_text(text=caption, parse_mode="HTML", reply_markup=reply_markup)

    elif query.data == "back_to_start":
        keyboard = [
            [InlineKeyboardButton("📖 Commands", callback_data="commands")],
            [InlineKeyboardButton(f"➕ Add {BOT_NAME}", url="https://t.me/YOURBOTUSERNAME?startgroup=true")]
        ]

        caption = (
            f"👋 <b>Welcome to {BOT_NAME} {BOT_VERSION}!</b>\n\n"
            f"🤖 {BOT_NAME} adalah asisten grup multifungsi yang dirancang untuk membantu mengelola grup kamu dengan lebih mudah dan aman.\n\n"
            "Fitur-fitur unggulan:\n"
            "🔨 Moderasi otomatis (ban, mute, warn, filter)\n"
            "🛡 Proteksi link, spam, badword\n"
            "📌 Auto welcome dan rules\n"
            "📈 Statistik grup & auto-clean\n"
            "🎉 Dan masih banyak lagi!\n\n"
            "💡 Gunakan tombol di bawah untuk menjelajahi semua perintah.\n"
            "Jika kamu adalah admin grup, tambahkan bot ini ke grup kamu sekarang!\n\n"
            "— Tim Dev Neko"
        )

        if is_media(message):
            await message.edit_caption(caption=caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await message.edit_text(text=caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

# 📍 LOG MESSAGE
async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    log_channel = get_log_channel(gid)
    if log_channel:
        msg = f"🗨️ <b>{update.effective_user.full_name}</b>:\n<code>{update.message.text}</code>"
        await context.bot.send_message(log_channel, msg, parse_mode="HTML")

# 📍 AUTO MUTE
async def auto_mute_task(context: CallbackContext):
    now = datetime.datetime.now().time()
    for chat_id in context.bot_data.get("groups", []):
        if not is_auto_mute_enabled(chat_id):
            continue
        perms = ChatPermissions(can_send_messages=not (now >= datetime.time(23, 0) or now <= datetime.time(6, 0)))
        await context.bot.set_chat_permissions(chat_id, perms)

# 📍 ID & ME
async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan ID user & grup.

    Contoh:
    /id
    """
    chat = update.effective_chat
    user = update.effective_user
    text = (
        f"<b>Chat ID:</b> <code>{chat.id}</code>\n"
        f"<b>User ID:</b> <code>{user.id}</code>\n"
        f"<b>Username:</b> @{user.username}" if user.username else f"<b>Nama:</b> {user.full_name}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan informasi user.

    Contoh:
    /me
    """
    user = update.effective_user
    chat = update.effective_chat

    bio = None
    phone = None

    try:
        member = await chat.get_member(user.id)
        bio = member.user.bio
        phone = member.user.phone_number if hasattr(member.user, "phone_number") else None
    except:
        pass

    text = f"<b>👤 Informasi Kamu:</b>\n\n"
    text += f"<b>Nama:</b> {escape(user.full_name)}\n"
    text += f"<b>ID:</b> <code>{user.id}</code>\n"
    if user.username:
        text += f"<b>Username:</b> @{user.username}\n"
    if phone:
        text += f"<b>Nomor HP:</b> <code>{phone}</code>\n"
    if bio:
        text += f"<b>Bio:</b> {escape(bio)}\n"
    if getattr(user, "is_premium", False):
        text += "⭐️ <b>Akun Premium</b>\n"

    try:
        photos = await context.bot.get_user_profile_photos(user.id, limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1]  # resolusi tertinggi
            await update.message.reply_photo(photo.file_id, caption=text, parse_mode="HTML")
            return
    except Exception as e:
        print("❌ Gagal ambil foto profil:", e)

    # fallback: kirim teks saja
    await update.message.reply_text(text, parse_mode="HTML")

async def left_group_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.chat_member.chat
    member = update.chat_member.new_chat_member

    # Hanya jika user yang berubah status adalah bot sendiri
    if member.user.id == context.bot.id and member.status in ("left", "kicked"):
        delete_group(chat.id)
        print(f"🧹 Data grup {chat.title} ({chat.id}) dihapus karena bot keluar")
        