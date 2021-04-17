from telegram.ext import *
from telegram import Update
from telegram import Bot
from telegram import InlineKeyboardMarkup
from telegram import InlineKeyboardButton
from config import token
import emoji


def set_keyboard():  # возможно потом перепишу, т.к. клава будет загружаться с бд
    btns = [InlineKeyboardButton(text=emoji.emojize(":white_large_square:", use_aliases=True), callback_data=str(i)) for
            i in range(9)]
    buttons = [btns[i:i + 3] for i in range(0, 7, 3)]
    return InlineKeyboardMarkup([buttons[0], buttons[1], buttons[2]], resize_keyboard=True)


def start_command(update: Update, context: CallbackContext):
    update.message.reply_text('Привет! чтобы посмотреть все команды, напиши /help')


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text('/help - все команды \n/play - начать игру')


def play_command(update: Update, context: CallbackContext):
    reply_markup = set_keyboard()

    update.message.reply_text(text='Играй в крестики нолики через клавиатуру!', reply_markup=reply_markup)


def buttons_callback_handler(bot: Bot, update: Update):
    query = update.callback_query


def message_handler(update: Update, context: CallbackContext):
    update.message.reply_text('тест')


def error(update: Update, context: CallbackContext):
    print(f'Update {update} caused error {context.error}')


def main():
    updater = Updater(token=token, use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', filters=Filters.all, callback=start_command))
    updater.dispatcher.add_handler(CommandHandler('help', filters=Filters.all, callback=help_command))
    updater.dispatcher.add_handler(CommandHandler('play', filters=Filters.all, callback=play_command))
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


main()
