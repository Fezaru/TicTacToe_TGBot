from peewee import fn
from telegram.ext import *
from telegram import Update
from telegram import Bot
from telegram import InlineKeyboardMarkup
from telegram import InlineKeyboardButton
from config import token
import emoji
from db import *


def keyboard_to_map(keyboard: InlineKeyboardMarkup):
    game_map = ''
    for row in keyboard['inline_keyboard']:  # ругается но работает
        for button in row:
            game_map += button.text + ' '
    return game_map.strip()


def map_to_keyboard(filename):  # возможно callback_data и text будут разными и придется менять структуру данных
    with open(filename, 'r') as f:
        game_map = f.readline().split()
    btns = [InlineKeyboardButton(text=emoji.emojize(el, use_aliases=True), callback_data=el)
            for
            el in game_map]
    buttons = [btns[i:i + 3] for i in range(0, 7, 3)]
    return InlineKeyboardMarkup([buttons[0], buttons[1], buttons[2]], resize_keyboard=True)


def initial_map(game_id):
    with open(f'map{game_id}', 'w') as f:
        a = ':white_large_square: ' * 9
        f.writelines(a.strip())


def initial_keyboard():  # возможно потом перепишу, т.к. клава будет загружаться с бд (сделать set_keyboard)
    btns = [InlineKeyboardButton(text=emoji.emojize(':white_large_square:', use_aliases=True), callback_data=str(i)) for
            i in range(9)]
    buttons = [btns[i:i + 3] for i in range(0, 7, 3)]
    return InlineKeyboardMarkup([buttons[0], buttons[1], buttons[2]], resize_keyboard=True)


def start_command(update: Update, context: CallbackContext):
    update.message.reply_text('Привет! чтобы посмотреть все команды, напиши /help')


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text('/help - все команды \n/play - начать игру')


def play_command(update: Update, context: CallbackContext):
    reply_markup = initial_keyboard()
    user_id = update.message.chat_id

    db.connect()
    games = Game.select()
    if len(games) == 0:
        initial_map(1)
        game = Game(player_x=user_id, player_o=None, current_step=user_id, map=f'..\\map{1}',
                    # нан не нарботает изменить на пустуюю строку
                    state='Waiting for players')
        game.save()
    else:
        for game in games:  # БАЗА ПУСТАЯ ЦИКЛ НЕ ЗАПУСКАЕТСЯ (запусается вроде(елс работает))
            if user_id in game.player_o or user_id in game.player_x:  # проверить, добавить логику
                break  # если игрок уже в базе выслать крестику карту из бд с его игрой
        else:  # написать функцию, которая преобразует массив х, о и 0 в InlineKeyboard
            # И НЕ ЗАБЫТЬ ДОБАВИТЬ ПРОВЕРКУ if state == 'in process'
            for game in games:
                if game.player_o is None:  # не уверен что будет работать с нан, проверить или заменить на ''
                    game.player_o = user_id
                    game.state = 'in progress'
                    game.save()
                    break
            else:
                max_id = Game.select(fn.MAX(Game.id)).scalar() + 1
                # max_id = Game.get(fn.MAX(Game.id)) + 1
                initial_map(max_id)
                game = Game(player_x=user_id, player_o=None, current_step=user_id, map=f'..\\map{max_id}',
                            state='Waiting for players')
                game.save()

    db.close()

    context.bot.send_message(chat_id=user_id, text='Играй в крестики нолики через клавиатуру!',
                             reply_markup=reply_markup)
    # update.message.reply_text(text='Играй в крестики нолики через клавиатуру!', reply_markup=reply_markup)


def buttons_callback_handler(bot: Bot, update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data


def message_handler(update: Update, context: CallbackContext):
    update.message.reply_text('тест')


def error(update: Update, context: CallbackContext):
    print(f'Update {update} caused error {context.error}')


def main():
    bot = Bot(token=token)
    updater = Updater(token=token, use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', filters=Filters.all, callback=start_command))
    updater.dispatcher.add_handler(CommandHandler('help', filters=Filters.all, callback=help_command))
    updater.dispatcher.add_handler(CommandHandler('play', filters=Filters.all, callback=play_command))
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


main()
