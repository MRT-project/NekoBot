from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from database.db import (
    get_badwords, add_warning,
    is_antilink_enabled, is_antibadword_enabled,
    add_stat, get_banlist, add_to_banlist, remove_from_banlist
)
from utils.regexfilter import build_badword_regex
from .utils import is_admin, extract_user
import re

def parse_duration(text):
    match = re.search(r"(\d+)([mh])", text)
    if not match:
        return None
    value, unit = match.groups()
    seconds = int(value) * 60 if unit == "m" else int(value) * 3600
    return seconds

async def banlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    gid = update.effective_chat.id
    ids = get_banlist(gid)
    if not ids:
        return await update.message.reply_text("✅ Banlist kosong.")

    text = "🚫 <b>Auto-Ban List</b>\n\n"
    for uid in ids:
        try:
            user = await context.bot.get_chat_member(gid, uid)
            text += f"• {user.user.full_name} (`{uid}`)\n"
        except:
            text += f"• [Unknown User] (`{uid}`)\n"

    await update.message.reply_text(text, parse_mode="HTML")

async def autoban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    user = await extract_user(update, context)
    if not user:
        return await update.message.reply_text("Usage: /autoban [reply/@user]")
    add_to_banlist(update.effective_chat.id, user.id)
    await update.message.reply_text(f"🚫 <b>{user.full_name}</b> akan diban otomatis saat join.", parse_mode="HTML")

async def unautoban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    user = await extract_user(update, context)
    if not user:
        return await update.message.reply_text("Usage: /unautoban [reply/@user]")
    remove_from_banlist(update.effective_chat.id, user.id)
    await update.message.reply_text(f"✅ <b>{user.full_name}</b> dihapus dari daftar autoban.", parse_mode="HTML")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return

    user = await extract_user(update, context)
    if not user:
        return await update.message.reply_text("Usage: /ban [reply/@user] <durasi?> <alasan?>")

    args = context.args
    duration = parse_duration("".join(args)) if args else None
    reason = " ".join(args[1:]) if len(args) > 1 else "No reason"

    await update.effective_chat.ban_member(user.id, until_date=None if not duration else update.message.date.timestamp() + duration)

    await update.message.reply_text(
        f"🚫 <b>{user.full_name}</b> banned"
        + (f" for <b>{args[0]}</b>" if duration else "")
        + f"\n📝 Reason: {reason}",
        parse_mode="HTML"
    )

    add_stat(update.effective_chat.id, "ban")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return

    user = await extract_user(update, context)
    if not user:
        return await update.message.reply_text("Usage: /unban [reply/@user]")

    await update.effective_chat.unban_member(user.id)

    await update.message.reply_text(f"✅ <b>{user.full_name}</b> has been unbanned.", parse_mode="HTML")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return

    user = await extract_user(update, context)
    if not user:
        return await update.message.reply_text("Usage: /mute [reply/@user] <5m/1h> [reason]")

    args = context.args
    duration = parse_duration("".join(args)) if args else None
    reason = " ".join(args[1:]) if len(args) > 1 else "No reason"

    await update.effective_chat.restrict_member(
        user.id,
        ChatPermissions(can_send_messages=False)
    )

    await update.message.reply_text(
        f"🔇 <b>{user.full_name}</b> muted"
        + (f" for <b>{args[0]}</b>" if duration else "")
        + f"\n📝 Reason: {reason}",
        parse_mode="HTML"
    )

    add_stat(update.effective_chat.id, "mute")

    # auto-unmute jika durasi ada
    if duration:
        context.job_queue.run_once(
            callback=auto_unmute,
            when=duration,
            data={"chat_id": update.effective_chat.id, "user_id": user.id}
        )

async def auto_unmute(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    await context.bot.restrict_chat_member(
        data["chat_id"],
        data["user_id"],
        permissions=ChatPermissions(can_send_messages=True)
    )
    await context.bot.send_message(data["chat_id"], f"🔊 User unmuted automatically.")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    user = await extract_user(update, context)
    if not user:
        return await update.message.reply_text("Usage: /unmute [reply/@user]")
    await update.effective_chat.restrict_member(user.id, ChatPermissions(can_send_messages=True))
    await update.message.reply_text(f"🔊 {user.full_name} unmuted.")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    user = await extract_user(update, context)
    if not user:
        return await update.message.reply_text("Usage: /kick [reply/@username]")
    await update.effective_chat.ban_member(user.id)
    await update.message.reply_text(f"👢 {user.full_name} kicked.")

async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        return
    if update.message.reply_to_message:
        try:
            await update.message.reply_to_message.delete()
            await update.message.delete()
        except:
            await update.message.reply_text("❌ Failed to delete.")
    else:
        await update.message.reply_text("Reply to the message to clean.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    gid = update.effective_chat.id
    uid = update.effective_user.id

    is_user_admin = await is_admin(update)

    # === BADWORD ===
    triggered_badword = False
    if is_antibadword_enabled(gid):
        badwords = get_badwords(gid)
        pattern = build_badword_regex(badwords)
        if re.search(pattern, text):
            triggered_badword = True

    # === ANTILINK ===
    promo_keywords = ["t.me", "http://", "https://", "www"]
    triggered_link = is_antilink_enabled(gid) and any(p in text for p in promo_keywords)

    # === ACTION ===
    if (triggered_badword or triggered_link) and not is_user_admin:
        await update.message.delete()
        count = add_warning(gid, uid)
        if count >= 3:
            await update.effective_chat.ban_member(uid)
            await update.message.reply_text(f"⛔ {update.effective_user.full_name} banned (3 warnings).")
        else:
            await update.message.reply_text(f"⚠️ {update.effective_user.full_name} warned ({count}/3).")
