from telegram import Update
from telegram.ext import ContextTypes

async def is_admin(update: Update) -> bool:
    member = await update.effective_chat.get_member(update.effective_user.id)
    return member.status in ['administrator', 'creator']

async def extract_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    elif context.args:
        username = context.args[0].lstrip('@')
        for member in await update.effective_chat.get_administrators():
            if member.user.username == username:
                return member.user
    return None

async def is_admin_group(update: Update) -> bool:
    user_id = update.effective_user.id
    chat = update.effective_chat
    member = await chat.get_member(user_id)
    return member.status in ['administrator', 'creator']
    