from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)
from pymongo import MongoClient
import os, traceback, html, json

EXCEPTION_CHAT_ID = 328982832
PURPOSE, CITY = range(2)
updater = Updater(os.environ.get("TELEGRAM_TOKEN"), use_context=True)
# mongo_client = MongoClient("mongodb://localhost:1651/")


def error_handler(update: object, context: CallbackContext) -> None:
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message
    context.bot.send_message(EXCEPTION_CHAT_ID, message, parse_mode=ParseMode.HTML)

def start(update: Update, context: CallbackContext) -> str:
    update.message.reply_text(
        f"Привет {update.effective_user.first_name}! Ты тут зачем?",
        reply_markup=InlineKeyboardMarkup(
            [
                InlineKeyboardButton("Зарегистрируй меня!", callback_data="1"),
                InlineKeyboardButton("Я бы нашел кого себе...", callback_data="2"),
            ]
        ),
    )
    return PURPOSE


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=f"Selected option: {query.data}")


def select_city(update: Update, context: CallbackContext) -> None:
    text = "Выбери город, где будешь искать друзей"
    if PURPOSE == 1:
        text = "Выбери город, где ты сейчас находишься"

    update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                InlineKeyboardButton("Москва", callback_data="1"),
                InlineKeyboardButton("Санкт-Петербург", callback_data="2"),
            ]
        ),
    )
    return CITY


def registerHandlers():
    print("Registering handlers...")
    # create dispatcher
    dp = updater.dispatcher
    # create 2 stage conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # select city based on purpose
            PURPOSE: [CallbackQueryHandler(select_city)]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # register handler
    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_error_handler(error_handler)

def main():
    registerHandlers()
    updater.start_polling()
    print("Started")
    updater.idle()


if __name__ == "__main__":
    main()
