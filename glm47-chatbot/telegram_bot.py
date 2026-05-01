import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import chatbot
from config import settings

logger = logging.getLogger(__name__)

telegram_app: Application | None = None


async def start_command(update: Update, context):
    await update.message.reply_text(
        "Welcome to GLM-4.7 Chatbot!\n\n"
        "I'm powered by NVIDIA's GLM-4.7 model via NIM.\n\n"
        "Just send me a message and I'll respond. "
        "Use /clear to reset our conversation."
    )


async def clear_command(update: Update, context):
    user_id = str(update.effective_user.id)
    if user_id in chatbot._sessions:
        del chatbot._sessions[user_id]
        await update.message.reply_text("Conversation cleared!")
    else:
        await update.message.reply_text("No active conversation to clear.")


async def handle_message(update: Update, context):
    user_id = str(update.effective_user.id)
    message = update.message.text

    try:
        result = await chatbot.process_message(
            user_id=user_id,
            message=message,
            enable_thinking=False,
        )
        await update.message.reply_text(result["reply"])
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        await update.message.reply_text("Sorry, something went wrong. Please try again.")


def _build_application() -> Application:
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application


async def start_webhook_mode() -> Application:
    global telegram_app
    if not settings.TELEGRAM_BOT_TOKEN:
        return None
    telegram_app = _build_application()
    await telegram_app.initialize()
    await telegram_app.start()
    return telegram_app


async def stop_webhook_mode():
    global telegram_app
    await telegram_app.stop()
    await telegram_app.shutdown()
    telegram_app = None


async def process_update(update_data: dict):
    update = Update.de_json(update_data, telegram_app.bot)
    await telegram_app.process_update(update)


async def start_polling_mode():
    application = _build_application()
    await application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    import asyncio
    asyncio.run(start_polling_mode())