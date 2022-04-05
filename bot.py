from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    ParseMode,
)
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
import os
import traceback
import html
import json
import difflib


########STRUCTURE########
REGISTER, SEARCH, ASK_PURPOSE, CITY_SELECT = range(4)
SEARCH_JOB, SEARCH_RENT, SEARCH_PEOPLE, DELETE = range(4)
HOBBY, SKIP_HOBBY, JOB, SKIP_JOB, PHOTO, SKIP_PHOTO = range(6)
EMPLOYEE, EMPLOYER = range(2)
ROOM, ROOMMATE = range(2)
AUTO, TAGS = range(2)
#########################


EXCEPTION_CHAT_ID = 328982832
updater = Updater(os.environ.get("TELEGRAM_TOKEN"), use_context=True)
db = MongoClient("mongodb://localhost:27017/").kv  # name of db is kv

list_of_cities = [i["name"] for i in db.cities.find()]


def error_handler(update: object, context: CallbackContext) -> None:
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"Ошибка ежжи да\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    context.bot.send_message(EXCEPTION_CHAT_ID, message, parse_mode=ParseMode.HTML)


def start_search(update: Update, context: CallbackContext) -> str:
    # get query, query data and user_id
    query = update.callback_query
    user_id = query.from_user.id
    query_data = query.data

    # if user is looking for job
    if query_data == "JOB":
        # get user data
        user_data = db.users.find_one({"user_id": user_id})
        if "resume" in user_data:
            resume = user_data["resume"]
            jobs = db.jobs.find()
            similar_jobs = [
                job
                for job in jobs
                if difflib.SequenceMatcher(None, job["description"], hobby).ratio()
                > 0.5
            ]
            # if there are no similar jobs
            if len(similar_jobs) == 0:
                query.edit_message_text("Нет таких вакансий")
                return SEARCH_JOB
            # if there are similar jobs
            else:
                # get all jobs names
                job_names = [job["name"] for job in similar_jobs]

        elif query_data == "PERSON":
            # create 2 inline buttons
            extra_tags_registered_button = (
                InlineKeyboardMarkup(
                    [
                        InlineKeyboardButton("Ищи как знаешь", callback_data="PERSON"),
                    ]
                )
                if db.uesrs.find_one({"user_id": user_id})["hobby"]
                else None
            )
            # show markup only if user is registered
            query.edit_message_text(
                "Что ты хочешь найти в человеке?",
                reply_markup=extra_tags_registered_button,
            )
            return SEARCH_PERSON
        elif query_data == "RENT":
            rent_button = InlineKeyboardMarkup(
                [
                    InlineKeyboardButton("Сдать комнату", callback_data="RENT"),
                    InlineKeyboardButton(
                        "Найти собственника", callback_data="ROOMMATE"
                    ),
                ]
            )
            query.edit_message_text("Ты хочешь", reply_markup=rent_button)
            return SEARCH_RENT
        else:
            # repeat this stage
            return SEARCH


def start(update: Update, context: CallbackContext) -> str:
    text = f"Привет {update.effective_user.first_name}! Я КогтеРван, помогу тебе с релокацией\n\nНапиши город, где ты сейчас находишься"
    # send message
    update.message.reply_text(text)
    return CITY_SELECT


def select_city(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    if query:
        query.answer()
        city = query.data
        user_id = query.from_user.id
    else:
        city = update.message.text
        user_id = update.message.from_user.id

    # find close matches to input city
    close_matches = difflib.get_close_matches(city, list_of_cities, n=3, cutoff=0.6)
    # if there is no results
    if not len(close_matches):
        update.message.reply_text("Такого города нет в базе. Попробуй еще раз")
        return CITY_SELECT

    # if there is more than one result
    elif len(close_matches) > 1 and not query:
        # create keyboard with results
        print(close_matches)
        keyboard = []
        for city in close_matches:
            keyboard.append([InlineKeyboardButton(city, callback_data=str(city))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "Найдено несколько городов. Выбери один из них", reply_markup=reply_markup
        )
        return CITY_SELECT
    # if there is only one result
    city = close_matches[0]
    db.users.insert_one({"user_id": user_id}, {"$set": {"city_name": city}})

    # save city to local context
    context.user_data["city_name"] = city

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Обновить анкету"
                    if db.users.find_one({"user_id": user_id})
                    else "Создай-ка мне анкету!",
                    callback_data="REGISTER",
                )
            ],
            [InlineKeyboardButton("Я бы нашел кого себе...", callback_data="SEARCH")],
        ]
    )
    query.edit_message_text(
        f"Ну и зачем тебе {city}?",
        reply_markup=reply_markup,
    )

    return ASK_PURPOSE


def select_purpose(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    query.answer()
    purpose = query.data
    if purpose == "REGISTER":
        update.callback_query.message.reply_text(
            "Накидай пару слов о себе. Хобби, характер и прочее."
        )
        return REGISTER
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Для хобби.", callback_data="PERSON")],
                [InlineKeyboardButton("Для работы.", callback_data="CITY")],
                [InlineKeyboardButton("Для хаты.", callback_data="RENT")],
            ]
        )
    query.edit_message_text("Для чего ищем?", reply_markup=reply_markup)
    return SEARCH


def select_hobby(update: Update, context: CallbackContext) -> str:

    # get user id and hobby
    user_id = update.message.from_user.id
    hobby = update.message.text

    # if message is longer than 300 symbols
    if len(hobby) > 300:
        update.message.reply_text("Текст не должен быть длиннее 300 символов")
        return REGISTER
    elif len(hobby) == 0:
        update.message.reply_text("Ладно, храни свои секреты")
        return SKIP_HOBBY
    db.users.update_one({"user_id": user_id}, {"$set": {"hobby": hobby}})

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Давай потом, а", callback_data="SKIP_JOB")]]
    )
    update.message.reply_text(
        "Гуд! А теперь еще немного о том, откуда на хлеб берешь деньги.",
        reply_markup=markup,
    )
    return JOB


def skip_hobby(update: Update, context: CallbackContext) -> str:
    user_id = update.message.from_user.id
    db.users.update_one({"user_id": user_id}, {"$set": {"hobby": ""}})

    update.message.reply_text(
        "Двигаемся дальше\n\n"
        "Пару слов о работе накидай хотя бы. Разрешаю и про бизнес.",
        reply_markup=markup,
    )
    return JOB


def select_job(update: Update, context: CallbackContext) -> str:
    user_id = update.message.from_user.id
    job = update.message.text
    # if message is longer than 300 symbols
    if len(update.message.text) > 300:
        update.message.reply_text("Текст не должен быть длиннее 300 символов")
        return JOB
    elif len(update.message.text) == 0:
        update.message.reply_text("Ладно, храни свои секреты")
        return SKIP_HOBBY
    db.users.update_one({"user_id": user_id}, {"$set": {"job": job}})
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Давай потом, а", callback_data="SKIP_JOB")]]
    )
    update.message.reply_text(
        "Накинь еще фоточку для полного фарша", reply_markup=markup
    )
    return PHOTO


def select_photo(update: Update, context: CallbackContext) -> str:
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]
    file_id = photo.file_id
    db.users.update_one({"user_id": user_id}, {"$set": {"photo": file_id}})
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Бери с авы и не парься", callback_data="SKIP_PHOTO")]]
    )
    update.message.reply_text(
        "Накинь еще фоточку для полного фарша", reply_markup=markup
    )
    return ConversationHandler.END


def skip_photo(update: Update, context: CallbackContext) -> str:
    user_id = update.message.from_user.id
    db.users.update_one(
        {"user_id": user_id},
        {"$set": {"photo": update.message.from_user.profile_photo_file_id}},
    )
    update.message.reply_text(
        "Двигаемся дальше\n\n"
        "Пару слов о работе накидай хотя бы. Разрешаю и про бизнес.",
        reply_markup=markup,
    )
    return JOB


def skip_job(update: Update, context: CallbackContext) -> str:
    user_id = update.message.from_user.id
    db.users.update_one({"user_id": user_id}, {"$set": {"job": ""}})
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Давай потом, а", callback_data="SKIP_PHOTO")]]
    )

    update.message.reply_text(
        "Не очень-то и хотелось. Давай фотку хотяб.", reply_markup=markup
    )
    return ConversationHandler.END


def delete_user(update: Update, context: CallbackContext) -> str:
    user_id = update.message.from_user.id
    db.users.delete_one({"user_id": user_id})
    update.message.reply_text("Пока.")


# cancel handler


def cancel(update: Update, context: CallbackContext) -> str:
    update.message.reply_text("До скорых встреч")
    return ConversationHandler.END


def ask_job(update: Update, context: CallbackContext) -> str:
    user_id = update.message.from_user.id
    # create 2 inline buttons
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Хочу искать работу", callback_data="EMPLOYEE")]][
            [InlineKeyboardButton("Хочу добавить вакансию", callback_data="EMPLOYER")]
        ]
    )

    update.message.reply_text(
        "Хочешь получать предложения о работе или добавлять вакансии?",
        reply_markup=markup,
    )
    return ConversationHandler.END


def select_employee(update: Update, context: CallbackContext) -> str:
    return ConversationHandler.END


def select_employer(update: Update, context: CallbackContext) -> str:
    return ConversationHandler.END


def ask_rent_type(update: Update, context: CallbackContext) -> str:
    return ConversationHandler.END


def select_room(update: Update, context: CallbackContext) -> str:
    return ConversationHandler.END


def select_roommate(update: Update, context: CallbackContext) -> str:
    return ConversationHandler.END


def ask_people(update: Update, context: CallbackContext) -> str:
    return ConversationHandler.END


def select_person_auto(update: Update, context: CallbackContext) -> str:
    return ConversationHandler.END


def select_person_tags(update: Update, context: CallbackContext) -> str:
    return ConversationHandler.END


def registerHandlers():
    print("Registering handlers...")
    dp = updater.dispatcher
    search_people_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_people)],
        states={
            AUTO: [MessageHandler(Filters.text, select_room)],
            TAGS: [MessageHandler(Filters.text, select_roommate)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    search_rent_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_rent_type)],
        states={
            ROOM: [MessageHandler(Filters.text, select_room)],
            ROOMMATE: [MessageHandler(Filters.text, select_roommate)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    search_job_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_job)],
        states={
            EMPLOYEE: [CallbackQueryHandler(select_employee)],
            EMPLOYER: [CallbackQueryHandler(select_employer)],
        },
        fallbacks=[MessageHandler(Filters.text, cancel)],
    )

    register_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text, select_hobby)],
        states={
            SKIP_HOBBY: [MessageHandler(Filters.text, skip_hobby)],
            JOB: [MessageHandler(Filters.text, select_job)],
            SKIP_JOB: [MessageHandler(Filters.text, skip_job)],
            PHOTO: [MessageHandler(Filters.photo, select_photo)],
            SKIP_PHOTO: [MessageHandler(Filters.text, skip_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        map_to_parent={REGISTER: REGISTER},
    )

    search_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_search)],
        # search for flats, jobs or people
        states={
            SEARCH_RENT: [search_rent_handler],
            SEARCH_JOB: [search_job_handler],
            SEARCH_PEOPLE: [search_people_handler],
            DELETE: [MessageHandler(Filters.text, delete_user)],
        },
        map_to_parent={SEARCH: SEARCH},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CITY_SELECT: [
                CallbackQueryHandler(select_city),
                MessageHandler(Filters.text, select_city),
            ],
            ASK_PURPOSE: [CallbackQueryHandler(select_purpose)],
            REGISTER: [register_handler],
            SEARCH: [search_handler],
        },
        per_user=True,
        allow_reentry=True,
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # register handler
    dp.add_handler(conv_handler)
    dp.add_error_handler(error_handler)


def main():
    registerHandlers()
    updater.start_polling()
    print("Started")
    updater.idle()


if __name__ == "__main__":
    main()
