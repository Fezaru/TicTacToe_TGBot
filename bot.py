from telegram.ext import *
from telegram import Update
from config import token


def start_command(update: Update, context: CallbackContext):
    update.message.reply_text('test reply start')


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text('test reply help')


def message_handler(update: Update, context: CallbackContext):
    update.message.reply_text('тест')


def error(update: Update, context: CallbackContext):
    print(f'Update {update} caused error {context.error}')


def main():
    updater = Updater(token=token, use_context=True)
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


main()
