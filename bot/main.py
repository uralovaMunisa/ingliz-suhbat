import sys
import logging
from pathlib import Path
from telegram import BotCommand, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Ensure parent directory is in python path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import config
from db.database import Database
from services.gemini_service import GeminiService
from services.rate_limiter import RateLimiter
from handlers import (
    start_handler,
    level_command,
    topic_command,
    strict_command,
    relax_command,
    reset_command,
    summary_command,
    quiz_command,
    help_command,
    callback_handler,
    text_message_handler,
    voice_message_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("emma_bot")


async def post_init(application):
    db: Database = application.bot_data["db"]
    await db.init_db()
    logger.info("Database initialized successfully.")

    bot_commands = [
        BotCommand("start", "Start or restart onboarding with Emma"),
        BotCommand("level", "Change your English level (A1-C1)"),
        BotCommand("topic", "Suggest 3 conversation topics"),
        BotCommand("quiz", "Take a 5-question quiz on your mistakes"),
        BotCommand("summary", "View your mistakes & vocabulary summary"),
        BotCommand("strict", "Strict mode (correct all mistakes & punctuation)"),
        BotCommand("relax", "Relaxed mode (correct only major mistakes)"),
        BotCommand("reset", "Clear conversation history"),
        BotCommand("help", "Help & command list with Uzbek hints"),
    ]
    try:
        await application.bot.set_my_commands(bot_commands)
        logger.info("Bot commands menu set successfully.")
    except Exception as e:
        logger.warning(f"Could not set bot commands menu: {e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update: %s", context.error, exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Oops! An unexpected glitch occurred on my end. Please try again in a moment! 😊"
            )
        except Exception:
            pass


def create_bot_app():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set! Please copy .env.example to .env and configure your bot token."
        )

    db = Database(config.DATABASE_PATH)
    gemini = GeminiService(config.GEMINI_API_KEY, config.MODEL_NAME)
    rate_limiter = RateLimiter(config.RATE_LIMIT_COUNT, config.RATE_LIMIT_WINDOW_SECONDS)

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN or "dummy_token").post_init(post_init).build()

    # Store shared services in bot_data
    app.bot_data["db"] = db
    app.bot_data["gemini"] = gemini
    app.bot_data["rate_limiter"] = rate_limiter

    # Register Command Handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("level", level_command))
    app.add_handler(CommandHandler("topic", topic_command))
    app.add_handler(CommandHandler("strict", strict_command))
    app.add_handler(CommandHandler("relax", relax_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("help", help_command))

    # Register Callback Query Handler
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Register Message Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, voice_message_handler))

    # Register Error Handler
    app.add_error_handler(error_handler)

    return app


def main():
    if not config.TELEGRAM_BOT_TOKEN:
        print("=" * 60)
        print("ERROR: TELEGRAM_BOT_TOKEN is missing!")
        print("Please create a .env file with your Telegram bot token:")
        print("  TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here")
        print("  GEMINI_API_KEY=your_gemini_api_key_here")
        print("=" * 60)
        sys.exit(1)

    logger.info("Starting Emma English Tutor Bot...")
    app = create_bot_app()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

