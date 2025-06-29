import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

BOT_TOKEN = "7795554263:AAE7yje0MLNqiruDXWYjHx-xkgtqZGt5ByM"

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# /start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Hello! This is a working Telegram bot using PTB 13.15!")

# Main function
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
