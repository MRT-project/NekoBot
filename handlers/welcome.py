from telegram import Update
from telegram.ext import ContextTypes
from database.db import set_welcome, get_welcome, set_rules, get_rules, set_welcome_enabled, is_welcome_enabled, get_banlist
from .utils import is_admin

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return await update.message.reply_text("❌ Admin only.")
    if len(context.args) != 1 or context.args[0] not in ["on", "off"]:
        return await update.message.reply_text("Usage: /welcome on|off")

    enabled = context.args[0] == "on"
    set_welcome_enabled(update.effective_chat.id, enabled)
    await update.message.reply_text(f"👋 Welcome {'enabled' if enabled else 'disabled'}.")

async def setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    text = ' '.join(context.args)
    if not text:
        return await update.message.reply_text("Usage: /setwelcome <text>. Use {name} as placeholder.")
    set_welcome(update.effective_chat.id, text)
    await update.message.reply_text("✅ Welcome saved.")

async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    text = ' '.join(context.args)
    if not text:
        return await update.message.reply_text("Usage: /setrules <text>")
    set_rules(update.effective_chat.id, text)
    await update.message.reply_text("✅ Rules saved.")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_rules(update.effective_chat.id)
    await update.message.reply_text(f"📜 Rules:\n{text}")

async def handle_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_member is None:
        return  # abaikan jika bukan event chat_member

    member = update.chat_member.new_chat_member
    user = member.user
    chat = update.chat_member.chat
    chat_id = chat.id

    # Jika bot masuk → auto ban
    if user.is_bot:
        try:
            await context.bot.ban_chat_member(chat_id, user.id)
            await context.bot.send_message(chat_id, f"🤖 {user.full_name} bot kicked.")
        except Exception as e:
            print(f"Gagal ban bot: {e}")
        return

    # Jika user baru masuk
    if member.status == "member" and await is_welcome_enabled(chat_id):
        custom = get_welcome(chat_id)
        welcome_text = custom or (
            f"👋 <b>Hallo {user.mention_html()}!</b>\n"
            f"Selamat datang di grup <b>{chat.title}</b> 🎉\n\n"
            "📌 Ketik <b>/rules</b> untuk melihat aturan grup.\n"
            "Hargai semua anggota dan semoga betah! 😸"
        )

        try:
            await context.bot.send_message(chat_id, welcome_text, parse_mode="HTML")
        except Exception as e:
            print(f"Gagal kirim welcome: {e}")

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gid = update.effective_chat.id
    for member in update.message.new_chat_members:
        if member.id in get_banlist(gid):
            await update.effective_chat.ban_member(member.id)
            await update.message.reply_text(f"🚫 Auto-ban: {member.full_name}")
