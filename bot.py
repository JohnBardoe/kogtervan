from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from pymongo import MongoClient
import os


updater = Updater(os.environ.get("TELEGRAM_TOKEN"), use_context=True)
#mongo_client = MongoClient("mongodb://localhost:1651/")

#create start callback
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет {update.effective_user.first_name}! Я бот для поиска людей для хобби работы.')

def main():
    print("Registering handlers...")
    start_handler = CommandHandler('start', start)
    updater.dispatcher.add_handler(start_handler)
    print("Started")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()











