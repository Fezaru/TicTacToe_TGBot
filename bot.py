import emoji
from telegram import Bot
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.ext import *

from collections import defaultdict
from config import token
from db import *


def is_draw(filename):
    with open(filename, 'r', encoding='utf8') as f:
        game_map = f.read().split()
    if emoji.emojize(':white_large_square:', use_aliases=True) not in game_map:
        return True
    return False


def is_completed(cell, keyboard: InlineKeyboardMarkup):
    cell = int(cell)
    board = keyboard['inline_keyboard']
    x = cell // 3
    y = cell % 3

    # по вертикали
    if board[0][y].text == board[1][y].text == board[2][y].text:
        return True

    # по горизонтали
    if board[x][0].text == board[x][1].text == board[x][2].text:
        return True

    # по главной диагонали
    if x == y and board[0][0].text == board[1][1].text == board[2][2].text:
        return True

    # по побочной диагонали
    if x + y == 2 and board[0][2].text == board[1][1].text == board[2][0].text:
        return True

    return False


def keyboard_to_map(keyboard: InlineKeyboardMarkup):
    game_map = ''
    for row in keyboard['inline_keyboard']:  # ругается но работает
        for button in row:
            game_map += button.text + ' '
    return game_map.strip()


def map_to_keyboard(filename):  # возможно callback_data и text будут разными и придется менять структуру данных
    with open(filename, 'r', encoding='utf8') as f:  # добавил енкодинг
        game_map = f.readline().split()
    btns = [InlineKeyboardButton(text=emoji.emojize(el, use_aliases=True), callback_data=str(i))
            # проверить коллбек значения
            for
            i, el in enumerate(game_map)]
    buttons = [btns[i:i + 3] for i in range(0, 7, 3)]
    return InlineKeyboardMarkup([buttons[0], buttons[1], buttons[2]], resize_keyboard=True)


def initial_map(game_id):
    with open(f'map{game_id}', 'w', encoding='utf8') as f:  # добавил енкодинг
        a = ':white_large_square: ' * 9
        f.writelines(a.strip())


def initial_keyboard():  # возможно потом перепишу, т.к. клава будет загружаться с бд (сделать set_keyboard)
    btns = [InlineKeyboardButton(text=emoji.emojize(':white_large_square:', use_aliases=True), callback_data=str(i)) for
            i in range(9)]
    buttons = [btns[i:i + 3] for i in range(0, 7, 3)]
    return InlineKeyboardMarkup([buttons[0], buttons[1], buttons[2]], resize_keyboard=True)


# def send_initial_keyboard(context, user_id):
#     reply_markup = initial_keyboard()
#     context.bot.send_message(chat_id=user_id, text='Играй в крестики нолики через клавиатуру!',
#                              reply_markup=reply_markup)


def start_command(update: Update, context: CallbackContext):
    update.message.reply_text('Привет! чтобы посмотреть все команды, напиши /help')
    context.user_data['keyboards'] = defaultdict(list)


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text('/help - все команды \n/play - начать игру')


def play_command(update: Update, context: CallbackContext):
    user_id = update.message.chat_id

    db.connect()
    games = Game.select()
    if len(games) == 0:
        initial_map(1)
        game = Game(player_x=user_id, player_o=None, current_step=user_id, map=f'..\\map{1}',
                    state='waiting for players')
        game.save()
        # send_initial_keyboard(context, user_id)
        context.bot.send_message(chat_id=user_id, text='Ты играешь за крестики! Ищем второго игрока')
    else:
        for game in games:  # БАЗА ПУСТАЯ ЦИКЛ НЕ ЗАПУСКАЕТСЯ (запусается вроде(елс работает))
            if (str(user_id) == str(game.player_o) or str(user_id) == str(
                    game.player_x)) and game.state == 'waiting for players':
                context.bot.send_message(chat_id=user_id, text='Ожидайте 2 игрока!')
                break  # проверить здесь нуэен ли брейк и работает ли
            elif (str(user_id) == str(game.player_o) or str(user_id) == str(
                    game.player_x)) and game.state == 'in progress':
                reply_markup = map_to_keyboard(f'map{str(game.id)}')

                delete_keyboards(context, user_id)

                msg = context.bot.send_message(chat_id=user_id,
                                               text='Ты уже в игре!',
                                               reply_markup=reply_markup)  # если игрок уже в базе выслать крестику карту из бд с его игрой
                add_keyboard_to_dict(context, msg, user_id)
                break
        else:
            # И НЕ ЗАБЫТЬ ДОБАВИТЬ ПРОВЕРКУ if state == 'in process'
            for game in games:
                if game.player_o is None:  # не уверен что будет работать с нан, проверить или заменить на ''
                    game.player_o = user_id
                    game.state = 'in progress'
                    game.save()
                    delete_keyboards(context, game.player_o)
                    delete_keyboards(context, game.player_x)
                    context.bot.send_message(chat_id=game.player_o,  # проверить работает ли
                                             text='Ты играешь за нолики!')
                    msg1 = context.bot.send_message(chat_id=game.player_o,  # проверить работает ли
                                                    text='Игра началась',
                                                    reply_markup=initial_keyboard())
                    msg2 = context.bot.send_message(chat_id=game.player_x,
                                                    text='Игра началась',
                                                    reply_markup=initial_keyboard())
                    add_keyboard_to_dict(context, msg1, game.player_o)
                    add_keyboard_to_dict(context, msg2, game.player_x)
                    break
            else:
                max_id = Game.select(fn.MAX(Game.id)).scalar() + 1
                # max_id = Game.get(fn.MAX(Game.id)) + 1
                initial_map(max_id)
                game = Game(player_x=user_id, player_o=None, current_step=user_id, map=f'..\\map{max_id}',
                            state='Waiting for players')
                game.save()
                # send_initial_keyboard(context, user_id)
                context.bot.send_message(chat_id=user_id, text='Ты играешь за X! Ищем второго игрока')

    db.close()
    # update.message.reply_text(text='Играй в крестики нолики через клавиатуру!', reply_markup=reply_markup)


def delete_keyboards(context, user_id):  # добавить в json file
    print('----------------------------------------')
    for message in context.user_data['keyboards'][str(user_id)]:
        print(str(user_id), end=' ')
        print(message.text)
        try:
            context.bot.delete_message(chat_id=user_id, message_id=message.message_id)
        except Exception:
            pass
    print('----------------------------------------')
    # context.user_data['keyboards'][str(user_id)].clear()


def add_keyboard_to_dict(context, msg, user_id):
    context.user_data['keyboards'][str(user_id)].append(msg)


def buttons_callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user_id = update.effective_message.chat_id
    X = emoji.emojize(':x:', use_aliases=True)
    O = emoji.emojize(':o:', use_aliases=True)

    db.connect()

    games = Game.select()
    cur_game = None
    for game in games:  # отправлять клавиатуру игрокам только после нахождения 2 игрока
        if (str(game.player_o) == str(user_id) or str(game.player_x) == str(
                user_id)) and game.state == 'in progress':
            cur_game = game
            break
    if cur_game is None or cur_game.state == 'finished':
        context.bot.send_message(chat_id=user_id, text='Игры не существует')
        db.close()
        return
    if str(user_id) == str(cur_game.current_step):  # ДОБАВИТЬ ФУНКЦИЮ ПРОВЕРКИ, ЕСТЬ ЛИ ПОБЕДА
        keyboard = map_to_keyboard(f'map{cur_game.id}')
        row = int(data) // 3
        col = int(data) % 3
        if str(user_id) == str(cur_game.player_x):
            step = X
            other_player = cur_game.player_o
        else:
            step = O
            other_player = cur_game.player_x
        if keyboard['inline_keyboard'][row][col].text not in [X, O]:  # проверить
            keyboard['inline_keyboard'][row][col].text = emoji.emojize(step)
            cur_game.current_player = other_player
            updated_map = keyboard_to_map(keyboard)
            with open(f'map{cur_game.id}', 'w', encoding='utf8') as f:
                f.write(updated_map)
            q = (Game.update({Game.current_step: other_player}).where(Game.id == cur_game.id))
            q.execute()

            if is_completed(data, keyboard):
                delete_keyboards(context, user_id)
                delete_keyboards(context, other_player)
                msg1 = context.bot.send_message(chat_id=user_id, text='Ты выиграл!', reply_markup=keyboard)
                msg2 = context.bot.send_message(chat_id=other_player, text='Ты проиграл!', reply_markup=keyboard)
                add_keyboard_to_dict(context, msg1, user_id)
                add_keyboard_to_dict(context, msg2, other_player)
                q = (Game.update({Game.state: 'finished'}).where(Game.id == cur_game.id))
                q.execute()
            elif is_draw(f'map{cur_game.id}'):
                delete_keyboards(context, user_id)
                delete_keyboards(context, other_player)
                msg1 = context.bot.send_message(chat_id=user_id, text='Ничья!', reply_markup=keyboard)
                msg2 = context.bot.send_message(chat_id=other_player, text='Ничья!', reply_markup=keyboard)
                add_keyboard_to_dict(context, msg1, user_id)
                add_keyboard_to_dict(context, msg2, other_player)
                q = (Game.update({Game.state: 'finished'}).where(Game.id == cur_game.id))
                q.execute()
            else:
                delete_keyboards(context, cur_game.player_x)
                delete_keyboards(context, cur_game.player_o)
                msg1 = context.bot.send_message(chat_id=user_id, text='Жди хода врага', reply_markup=keyboard)
                msg2 = context.bot.send_message(chat_id=other_player, text='Твой ход', reply_markup=keyboard)
                add_keyboard_to_dict(context, msg1, user_id)
                add_keyboard_to_dict(context, msg2, other_player)
        else:
            context.bot.send_message(chat_id=user_id, text='Выберите пустое поле!')
            db.close()
            return
    else:
        context.bot.send_message(chat_id=user_id, text='Сейчас не твой ход')

    db.close()


def message_handler(update: Update, context: CallbackContext):
    update.message.reply_text('тест')


# def error(update: Update, context: CallbackContext):
#     print(f'Update {update} caused error {context.error}')


def main():
    bot = Bot(token=token)
    updater = Updater(token=token, use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', filters=Filters.all, callback=start_command))
    updater.dispatcher.add_handler(CommandHandler('help', filters=Filters.all, callback=help_command))
    updater.dispatcher.add_handler(CommandHandler('play', filters=Filters.all, callback=play_command))
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback=buttons_callback_handler, pass_chat_data=True))
    # updater.dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


main()
