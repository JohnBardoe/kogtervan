from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

import creds

updater = Updater(creds.token, use_context=True)

#create start callback
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я бот для поиска людей для хобби работы. Хочешь создать свою анкету или искать людей? Напиши /create или /search')


def hello(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(f'Hello {update.effective_user.first_name}')


#add handlers
updater.dispatcher.add_handler(CommandHandler('hello', hello))

print('Bot started')
updater.start_polling()
updater.idle()


















