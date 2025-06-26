from telegram import Update
from telegram.ext import ContextTypes
from database.db import ensure_group

async def ensure_group_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    # ✅ Hanya proses grup
    if chat and chat.type in ["group", "supergroup"]:
        ensure_group(chat.id, chat.title or "Unknown")
