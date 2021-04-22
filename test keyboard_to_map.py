from telegram import InlineKeyboardMarkup
from telegram import InlineKeyboardButton
import emoji


def map_to_keyboard(filename):  # возможно callback_data и text будут разными и придется менять структуру данных
    with open(filename, 'r') as f:
        game_map = f.readline().split()
    btns = [InlineKeyboardButton(text=emoji.emojize(el, use_aliases=True), callback_data=str(i))
            # проверить коллбек значения
            for
            i, el in enumerate(game_map)]
    buttons = [btns[i:i + 3] for i in range(0, 7, 3)]
    return InlineKeyboardMarkup([buttons[0], buttons[1], buttons[2]], resize_keyboard=True)


def initial_keyboard():  # возможно потом перепишу, т.к. клава будет загружаться с бд (сделать set_keyboard)
    btns = [InlineKeyboardButton(text=emoji.emojize(':white_large_square:', use_aliases=True), callback_data=str(i)) for
            i in range(9)]
    buttons = [btns[i:i + 3] for i in range(0, 7, 3)]
    return InlineKeyboardMarkup([buttons[0], buttons[1], buttons[2]], resize_keyboard=True)


def keyboard_to_map(keyboard: InlineKeyboardMarkup):
    game_map = ''
    for row in keyboard['inline_keyboard']:
        for button in row:
            game_map += button.text + ' '
    return game_map.strip()


a = initial_keyboard()
b = keyboard_to_map(a)

print(b)

a = map_to_keyboard('map1')
b = keyboard_to_map(a)

print(b)