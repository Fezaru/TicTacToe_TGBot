import emoji
import json
import os
import sys
import random
from telegram import Bot
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.ext import *
from puzzles import Puzzle

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


def start_command(update: Update, context: CallbackContext):
    update.message.reply_text('Привет! чтобы посмотреть все команды, напиши /help')


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text('/help - все команды \n/play - начать игру')


def get_puzzle_command(update: Update, context: CallbackContext):
    print(os.getcwd())
    with open('c# form//mode.txt', 'r') as f:
        DIFFICULTY_MODE = f.read()
    if DIFFICULTY_MODE == 'easy':
        question, answer = random.choice(list(Puzzle.easy.items()))
        update.message.reply_photo(photo=open(question, 'rb'))
        context.user_data['answer'] = answer
    elif DIFFICULTY_MODE == 'hard':
        question, answer = random.choice(list(Puzzle.hard.items()))
        update.message.reply_photo(photo=open(question, 'rb'))
        context.user_data['answer'] = answer


def play_command(update: Update, context: CallbackContext):
    user_id = update.message.chat_id

    db.connect()
    games = Game.select()
    if len(games) == 0:
        initial_map(1)
        game = Game(player_x=user_id, player_o=None, current_step=user_id, map=f'..\\map{1}',
                    state='waiting for players')
        game.save()
        context.bot.send_message(chat_id=user_id, text='Ты играешь за крестики! Ищем второго игрока')
    else:
        for game in games:  # БАЗА ПУСТАЯ ЦИКЛ НЕ ЗАПУСКАЕТСЯ (запусается вроде(елс работает))
            if (str(user_id) == str(game.player_o) or str(user_id) == str(
                    game.player_x)) and game.state == 'waiting for players':
                context.bot.send_message(chat_id=user_id, text='Ожидайте 2 игрока!')
                break
            elif (str(user_id) == str(game.player_o) or str(user_id) == str(
                    game.player_x)) and game.state == 'in progress':
                message = send_updated_keyboard(context, game, user_id)
                data = {}
                data = delete_prev_keyboard(context, data, user_id)
                update_json(data, message)
                break
        else:
            # И НЕ ЗАБЫТЬ ДОБАВИТЬ ПРОВЕРКУ if state == 'in process'
            for game in games:
                if game.player_o is None:  # не уверен что будет работать с нан, проверить или заменить на ''
                    game.player_o = user_id
                    game.state = 'in progress'
                    game.save()
                    msg1, msg2 = start_game(context, game)
                    messages = {str(game.player_x): msg2.message_id, str(game.player_o): msg1.message_id}
                    data = {}
                    if os.path.getsize("messages.json") != 0:
                        with open('messages.json', 'r', encoding='utf8') as f:
                            data = json.loads(f.read())
                    update_json(data, messages)
                    break
            else:
                max_id = Game.select(fn.MAX(Game.id)).scalar() + 1
                # max_id = Game.get(fn.MAX(Game.id)) + 1
                initial_map(max_id)
                game = Game(player_x=user_id, player_o=None, current_step=user_id, map=f'..\\map{max_id}',
                            state='Waiting for players')
                game.save()
                context.bot.send_message(chat_id=user_id, text='Ты играешь за X! Ищем второго игрока')

    db.close()


def exit_command(update: Update, context: CallbackContext):
    user_id = update.message.chat_id

    db.connect()
    games = Game.select()

    if len(games) != 0:
        for game in games:  # БАЗА ПУСТАЯ ЦИКЛ НЕ ЗАПУСКАЕТСЯ (запусается вроде(елс работает))
            if (str(user_id) == str(game.player_o) or str(user_id) == str(
                    game.player_x)) and game.state in ['in progress', 'waiting for players']:
                q = Game.delete().where(Game.id == game.id)
                q.execute()
                context.bot.send_message(chat_id=game.player_x, text='Игра закончена')
                try:
                    context.bot.send_message(chat_id=game.player_o, text='Игра закончена')
                except Exception:
                    pass
                break
        else:
            context.bot.send_message(chat_id=user_id, text='Игра не может быть завершена')
    else:
        context.bot.send_message(chat_id=user_id, text='Игра не может быть завершена')
    db.close()


def start_game(context, game):
    context.bot.send_message(chat_id=game.player_o,
                             text='Ты играешь за нолики!')
    msg1 = context.bot.send_message(chat_id=game.player_o,
                                    text='Игра началась',
                                    reply_markup=initial_keyboard())
    msg2 = context.bot.send_message(chat_id=game.player_x,
                                    text='Игра началась',
                                    reply_markup=initial_keyboard())
    return msg1, msg2


def update_json(data, message):
    with open('messages.json', 'w', encoding='utf8') as f:
        data.update(message)
        json.dump(data, f)


def delete_prev_keyboard(context, data, user_id):
    if os.path.getsize("messages.json") != 0:
        with open('messages.json', 'r', encoding='utf8') as f:
            data = json.loads(f.read())
        context.bot.delete_message(chat_id=user_id, message_id=data[str(user_id)])
    return data


def send_updated_keyboard(context, game, user_id):
    reply_markup = map_to_keyboard(f'map{str(game.id)}')
    msg = context.bot.send_message(chat_id=user_id,
                                   text='Ты уже в игре!',
                                   reply_markup=reply_markup)
    message = {str(user_id): msg.message_id}
    return message


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
                reply_text = ['Ты выиграл!', 'Ты проиграл!']
                handle_step(context, keyboard, other_player, reply_text, user_id)
                q = (Game.update({Game.state: 'finished'}).where(Game.id == cur_game.id))
                q.execute()
            elif is_draw(f'map{cur_game.id}'):
                reply_text = ['Ничья!', 'Ничья!']
                handle_step(context, keyboard, other_player, reply_text, user_id)
                q = (Game.update({Game.state: 'finished'}).where(Game.id == cur_game.id))
                q.execute()
            else:
                reply_text = ['Жди хода врага!', 'Сейчас твой ход!']
                handle_step(context, keyboard, other_player, reply_text, user_id)
        else:
            # context.bot.send_message(chat_id=user_id, text='Выберите пустое поле!')
            reply_text = 'Выберите пустое поле!'
            with open("messages.json", "r", encoding='utf8') as read_file:
                messages = json.load(read_file)
            try:
                context.bot.edit_message_text(chat_id=user_id, message_id=messages[str(user_id)],
                                              text=reply_text)
                context.bot.edit_message_reply_markup(chat_id=user_id, message_id=messages[str(user_id)],
                                                      reply_markup=keyboard)
            except Exception:
                pass
            db.close()
            return
    else:
        # context.bot.send_message(chat_id=user_id, text='Сейчас не твой ход')
        reply_text = 'Сейчас не твой ход!'
        keyboard = map_to_keyboard(f'map{cur_game.id}')
        with open("messages.json", "r", encoding='utf8') as read_file:
            messages = json.load(read_file)
        try:
            context.bot.edit_message_text(chat_id=user_id, message_id=messages[str(user_id)],
                                          text=reply_text)
            context.bot.edit_message_reply_markup(chat_id=user_id, message_id=messages[str(user_id)],
                                                  reply_markup=keyboard)
        except Exception:
            pass
    db.close()


def handle_step(context, keyboard, other_player, reply_text, user_id):
    with open("messages.json", "r", encoding='utf8') as read_file:
        messages = json.load(read_file)
    try:
        context.bot.edit_message_text(chat_id=user_id, message_id=messages[str(user_id)], text=reply_text[0])
        context.bot.edit_message_text(chat_id=other_player, message_id=messages[str(other_player)],
                                      text=reply_text[1])
        context.bot.edit_message_reply_markup(chat_id=user_id, message_id=messages[str(user_id)],
                                              reply_markup=keyboard)
        context.bot.edit_message_reply_markup(chat_id=other_player, message_id=messages[str(other_player)],
                                              reply_markup=keyboard)
    except Exception:
        pass


def message_handler(update: Update, context: CallbackContext):
    if 'answer' in context.user_data.keys():
        if update.message.text.lower() == context.user_data['answer']:
            update.message.reply_text('Правильно!')
            del context.user_data['answer']
        else:
            update.message.reply_text('Неправильно!')
    else:
        update.message.reply_text(random.choice(['Да.', 'Нет']))


# def error(update: Update, context: CallbackContext):
#     print(f'Update {update} caused error {context.error}')


def main():
    bot = Bot(token=token)
    updater = Updater(token=token, use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start', filters=Filters.all, callback=start_command))
    updater.dispatcher.add_handler(CommandHandler('help', filters=Filters.all, callback=help_command))
    updater.dispatcher.add_handler(CommandHandler('play', filters=Filters.all, callback=play_command))
    updater.dispatcher.add_handler(CommandHandler('exit', filters=Filters.all, callback=exit_command))
    updater.dispatcher.add_handler(CommandHandler('get_puzzle', filters=Filters.all, callback=get_puzzle_command))
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback=buttons_callback_handler, pass_chat_data=True))
    # updater.dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


main()
