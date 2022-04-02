from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from pymongo import MongoClient
import os


updater = Updater(os.environ.get("TELEGRAM_TOKEN"), use_context=True)
# mongo_client = MongoClient("mongodb://localhost:1651/")

# create
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        f"Привет {update.effective_user.first_name}! Ты тут зачем?",
        reply_markup=InlineKeyboardMarkup(
            [
                InlineKeyboardButton("Зарегистрируй меня!", callback_data="1"),
                InlineKeyboardButton("Я бы нашел кого себе...", callback_data="2"),
            ]
        ),
    )


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=f"Selected option: {query.data}")

# create callback for registration
def select_city(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Выбери город:",
        reply_markup=ReplyKeyboardMarkup(["Москва", "Санкт-Петербург", "Новосибирск"]),
    )
    return select_city_2


def registerHandlers():
    print("Registering handlers...")
    # create dispatcher
    dp = updater.dispatcher
    # create 2 stage conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            select_city: [MessageHandler(Filters.text, select_city)],
            select_city_2: [MessageHandler(Filters.text, select_city_2)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # register handler
    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(button))

def main():
    registerHandlers()
    updater.start_polling()
    print("Started")
    updater.idle()


if __name__ == "__main__":
    main()
