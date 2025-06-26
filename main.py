import logging, os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ChatMemberHandler, filters, Defaults, ContextTypes
from telegram.request import HTTPXRequest
from handlers import general, admin, moderation, welcome
from handlers.utils import is_admin
from database.db import setup_db, get_all_group_ids, is_autoclean_enabled
from config import TOKEN, BOT_NAME, BOT_VERSION
from utils.group_guard import ensure_group_data
from handlers.general import left_group_handler

defaults = Defaults(parse_mode="HTML")
command_registry = {}

# Optional: Log ke file + terminal
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{LOG_DIR}/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Matikan log berisik dari pustaka internal
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

async def on_startup(app):
    app.bot_data["groups"] = get_all_group_ids()

async def autocleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        gid = update.effective_chat.id
        if is_autoclean_enabled(gid):
            try:
                await update.message.delete()
            except Exception:
                pass

def register_command(command_name: str, handler_func):
    command_registry[command_name] = handler_func

def main():
    setup_db()
    app = ApplicationBuilder()\
        .token(TOKEN)\
        .defaults(defaults)\
        .request(HTTPXRequest(connect_timeout=10.0, read_timeout=30.0))\
        .post_init(on_startup)\
        .build()

    app.add_handler(CommandHandler("start", general.start))
    register_command("start", general.start)

    app.add_handler(CommandHandler("setlog", admin.setlog))
    register_command("setlog", admin.setlog)

    app.add_handler(CommandHandler("setmute", admin.setmute))
    register_command("setmute", admin.setmute)

    app.add_handler(CommandHandler("addbadword", admin.addbad))
    register_command("addbadword", admin.addbad)

    app.add_handler(CommandHandler("delbadword", admin.deletebadword))
    register_command("delbadword", admin.deletebadword)

    app.add_handler(CommandHandler("badwords", admin.listbadwords))
    register_command("badwords", admin.listbadwords)

    app.add_handler(CommandHandler("warnreset", admin.warnreset))
    register_command("warnreset", admin.warnreset)

    app.add_handler(CommandHandler("groupinfo", admin.groupinfo))
    register_command("groupinfo", admin.groupinfo)

    app.add_handler(CommandHandler("mute", moderation.mute))
    register_command("mute", moderation.mute)

    app.add_handler(CommandHandler("unmute", moderation.unmute))
    register_command("unmute", moderation.unmute)

    app.add_handler(CommandHandler("kick", moderation.kick))
    register_command("kick", moderation.kick)

    app.add_handler(CommandHandler("setwelcome", welcome.setwelcome))
    register_command("setwelcome", welcome.setwelcome)

    app.add_handler(CommandHandler("welcome", welcome.welcome))
    register_command("welcome", welcome.welcome)

    app.add_handler(CommandHandler("setantilink", admin.setantilink))
    register_command("setantilink", admin.setantilink)

    app.add_handler(CommandHandler("setantibadword", admin.setantibadword))
    register_command("setantibadword", admin.setantibadword)

    app.add_handler(CommandHandler("setrules", welcome.setrules))
    register_command("setrules", welcome.setrules)

    app.add_handler(CommandHandler("rules", welcome.rules))
    register_command("rules", welcome.rules)

    app.add_handler(CommandHandler("clean", moderation.clean))
    register_command("clean", moderation.clean)

    app.add_handler(CommandHandler("id", general.id))
    register_command("id", general.id)

    app.add_handler(CommandHandler("me", general.me))
    register_command("me", general.me)

    app.add_handler(CommandHandler("status", admin.status))
    register_command("status", admin.status)

    app.add_handler(CommandHandler("setautoclean", admin.setautoclean))
    register_command("setautoclean", admin.setautoclean)

    app.add_handler(CommandHandler("stats", admin.stats))
    register_command("stats", admin.stats)

    app.add_handler(CommandHandler("ban", moderation.ban))
    register_command("ban", moderation.ban)

    app.add_handler(CommandHandler("unban", moderation.unban))
    register_command("unban", moderation.unban)

    app.add_handler(CommandHandler("banlist", moderation.banlist))
    register_command("banlist", moderation.banlist)

    app.add_handler(CommandHandler("autoban", moderation.autoban))
    register_command("autoban", moderation.autoban)

    app.add_handler(CommandHandler("unautoban", moderation.unautoban))
    register_command("unautoban", moderation.unautoban)

    app.add_handler(CommandHandler("pin", admin.pin))
    register_command("pin", admin.pin)

    app.add_handler(CommandHandler("unpin", admin.unpin))
    register_command("unpin", admin.unpin)

    app.add_handler(CommandHandler("unpinall", admin.unpinall))
    register_command("unpinall", admin.unpinall)

    app.add_handler(CommandHandler("kickdeactivated", admin.kick_deactivated))
    register_command("kickdeactivated", admin.kick_deactivated)

    app.add_handler(CommandHandler("purge", admin.purge))
    register_command("purge", admin.purge)

    app.add_handler(CommandHandler("settings", admin.settings))
    register_command("settings", admin.settings)

    app.add_handler(CommandHandler("setlog", admin.setlog))
    register_command("setlog", admin.setlog)

    app.add_handler(CommandHandler("muteall", admin.muteall))
    register_command("muteall", admin.muteall)
    
    app.add_handler(CommandHandler("unmuteall", admin.unmuteall))
    register_command("unmuteall", admin.unmuteall)

    app.add_handler(CallbackQueryHandler(admin.button_toggle_handler, pattern="^perm_"))
    app.add_handler(CallbackQueryHandler(admin.button_toggle_handler, pattern="^toggle_"))
    app.add_handler(CallbackQueryHandler(general.button_handler))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, moderation.handle_message))
    app.add_handler(MessageHandler(filters.ALL, general.log_message))
    app.add_handler(ChatMemberHandler(welcome.handle_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.COMMAND, autocleanup), group=99)

    app.add_handler(
        MessageHandler(filters.ALL, ensure_group_data),
        group=-1  # Middleware, dijalankan lebih dulu
    )

    app.add_handler(ChatMemberHandler(left_group_handler))

    app.job_queue.run_repeating(general.auto_mute_task, interval=3600, first=10)

    general.command_registry = command_registry

    print(f"✅ {BOT_NAME} v{BOT_VERSION} running...")
    app.run_polling()

if __name__ == "__main__":
    main()
