import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

import chatbot
from config import settings

logger = logging.getLogger(__name__)


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


async def start_telegram_bot():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.info("TELEGRAM_BOT_TOKEN not set, skipping telegram bot")
        return

    logger.info("Starting Telegram bot")

    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await application.run_polling(allowed_updates=Update.TYPES)