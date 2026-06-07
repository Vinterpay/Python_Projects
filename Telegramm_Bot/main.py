import telebot
from telebot import types
import random
import time
import requests
import os
from datetime import datetime

# ====================== НАСТРОЙКИ ======================
TOKEN = '8702756707:AAEsgJIczsv6eDrs2BnOiFPhMfkfbbV9300'
WEATHER_API_KEY = 'e2baf12da292fdab2d87e1888cf046e3'

bot = telebot.TeleBot(TOKEN)

# Хранилища состояний
user_states = {}
minesweeper_games = {}
hangman_games = {}

# Данные игр
WORDS = ['питон', 'программа', 'алгоритм', 'ботаник', 'телеграм', 'клавиатура',
         'монитор', 'процессор', 'функция', 'объект', 'базаданных', 'переменная']

FACTS = [
    "Кошки могут производить более 100 различных звуков.",
    "Сердце креветки находится в её голове.",
    "Мёд никогда не портится.",
    "Крокодилы не могут высовывать язык.",
    "У улитки около 25 000 зубов.",
    "Бабочки пробуют вкус ногами.",
    "Слоны — единственные животные, которые не умеют прыгать."
]


# ====================== КЛАВИАТУРЫ ======================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('🎮 Игры', '📚 Интересный факт', '🌤️ Погода')
    return markup


def games_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('🕹️ Сапёр', '🎲 Угадай число', '💀 Виселица', '🔙 Назад')
    return markup


# ====================== КОМАНДЫ ======================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     "👋 Привет! Я улучшенный Telegram-бот 🤖\n\nВыбирай, что хочешь:",
                     reply_markup=main_menu())


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "Напиши /start", parse_mode="Markdown")


# ====================== ИГРЫ ======================
@bot.message_handler(func=lambda m: m.text in ['🎮 Игры', '/games'])
def show_games(message):
    bot.send_message(message.chat.id, "🎮 Выбери игру:", reply_markup=games_menu())


# ====================== САПЁР ======================
@bot.message_handler(func=lambda m: m.text == '🕹️ Сапёр')
def start_minesweeper(message):
    chat_id = message.chat.id
    user_states[chat_id] = 'minesweeper_difficulty'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('8x8 (10 мин)', '5x5 (3 мины)', '🔙 Назад')
    bot.send_message(chat_id, "Выбери сложность:", reply_markup=markup)


def init_minesweeper(chat_id, rows, cols, mines):
    board = [[0] * cols for _ in range(rows)]
    positions = random.sample(range(rows * cols), mines)
    for pos in positions:
        r, c = divmod(pos, cols)
        board[r][c] = -1
        for i in range(max(0, r - 1), min(rows, r + 2)):
            for j in range(max(0, c - 1), min(cols, c + 2)):
                if board[i][j] != -1:
                    board[i][j] += 1

    minesweeper_games[chat_id] = {
        'board': board,
        'visible': [[None] * cols for _ in range(rows)],
        'rows': rows, 'cols': cols, 'mines': mines,
        'game_over': False
    }


def print_board(game):
    emoji = {None: '⬜', 0: '🟦', -1: '💣', 'flag': '🚩'}
    for n in range(1, 9):
        emoji[n] = f'{n}️⃣'

    header = '   ' + ' '.join(chr(65 + i) for i in range(game['cols'])) + '\n'
    board_str = header
    for i in range(game['rows']):
        row = [emoji.get(cell, str(cell)) for cell in game['visible'][i]]
        board_str += f"{(i + 1):2d} {' '.join(row)}\n"
    return board_str


def handle_minesweeper(message):
    chat_id = message.chat.id
    text = message.text.strip().upper()

    if text in ['8X8 (10 МИН)', '8X8, 10 МИН']:
        init_minesweeper(chat_id, 8, 8, 10)
    elif text in ['5X5 (3 МИНЫ)', '5X5, 3 МИНЫ']:
        init_minesweeper(chat_id, 5, 5, 3)
    elif text == '🔙 НАЗАД':
        user_states.pop(chat_id, None)
        minesweeper_games.pop(chat_id, None)
        bot.send_message(chat_id, "Возвращаемся в меню игр", reply_markup=games_menu())
        return

    game = minesweeper_games.get(chat_id)
    if not game or game.get('game_over'):
        return

    if text.startswith('Ф '):
        try:
            col = ord(text[2]) - ord('A')
            row = int(text[3:]) - 1
            if 0 <= row < game['rows'] and 0 <= col < game['cols']:
                cell = game['visible'][row][col]
                game['visible'][row][col] = 'flag' if cell is None else None if cell == 'flag' else cell
        except:
            bot.send_message(chat_id, "Формат: `Ф A1`")
    else:
        try:
            col = ord(text[0]) - ord('A')
            row = int(text[1:]) - 1
            if 0 <= row < game['rows'] and 0 <= col < game['cols']:
                reveal_cell(chat_id, row, col)
                if check_win(chat_id):
                    bot.send_message(chat_id, "🎉 **Ты победил!** 🎉", parse_mode="Markdown")
                    end_game(chat_id)
                    return
        except:
            bot.send_message(chat_id, "Формат хода: `A1`")

    send_minesweeper_board(chat_id)


def reveal_cell(chat_id, row, col):
    game = minesweeper_games[chat_id]
    if game['visible'][row][col] is not None:
        return
    if game['board'][row][col] == -1:
        game['visible'][row][col] = -1
        game['game_over'] = True
        reveal_all_mines(chat_id)
        bot.send_message(chat_id, "💥 Ты взорвался на мине!")
        end_game(chat_id)
        return

    game['visible'][row][col] = game['board'][row][col]
    if game['board'][row][col] == 0:
        for i in range(max(0, row - 1), min(game['rows'], row + 2)):
            for j in range(max(0, col - 1), min(game['cols'], col + 2)):
                if (i, j) != (row, col):
                    reveal_cell(chat_id, i, j)


def reveal_all_mines(chat_id):
    game = minesweeper_games[chat_id]
    for i in range(game['rows']):
        for j in range(game['cols']):
            if game['board'][i][j] == -1:
                game['visible'][i][j] = -1


def check_win(chat_id):
    game = minesweeper_games[chat_id]
    for i in range(game['rows']):
        for j in range(game['cols']):
            if game['board'][i][j] != -1 and game['visible'][i][j] is None:
                return False
    return True


def send_minesweeper_board(chat_id):
    game = minesweeper_games[chat_id]
    board_str = print_board(game)
    text = f"{board_str}\n\n• A1 — открыть клетку\n• Ф A1 — поставить/убрать флаг"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔙 Назад')
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")


def end_game(chat_id):
    user_states.pop(chat_id, None)
    minesweeper_games.pop(chat_id, None)


# ====================== УГАДАЙ ЧИСЛО ======================
@bot.message_handler(func=lambda m: m.text == '🎲 Угадай число')
def start_guess_number(message):
    chat_id = message.chat.id
    user_states[chat_id] = 'guess_number'
    number = random.randint(1, 100)
    user_states[f"{chat_id}_num"] = number
    user_states[f"{chat_id}_att"] = 0
    user_states[f"{chat_id}_min"] = 1
    user_states[f"{chat_id}_max"] = 100

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔙 Назад')
    bot.send_message(chat_id, "🔢 Я загадал число от **1 до 100**!\nНапиши число:", reply_markup=markup,
                     parse_mode="Markdown")


def handle_guess_number(message):
    chat_id = message.chat.id
    if message.text == '🔙 Назад':
        cleanup_guess(chat_id)
        bot.send_message(chat_id, "Выход...", reply_markup=games_menu())
        return

    try:
        guess = int(message.text)
        number = user_states.get(f"{chat_id}_num")
        if number is None:
            return
        attempts = user_states.get(f"{chat_id}_att", 0) + 1
        user_states[f"{chat_id}_att"] = attempts

        if guess == number:
            bot.send_message(chat_id, f"🎉 **Правильно!** Это было {number}\nУгадано за {attempts} попыток!",
                             parse_mode="Markdown")
            cleanup_guess(chat_id)
        elif guess < number:
            user_states[f"{chat_id}_min"] = guess + 1
            bot.send_message(chat_id, f"🔼 Больше! ({guess + 1} — {user_states[f'{chat_id}_max']})")
        else:
            user_states[f"{chat_id}_max"] = guess - 1
            bot.send_message(chat_id, f"🔽 Меньше! ({user_states[f'{chat_id}_min']} — {guess - 1})")
    except:
        bot.send_message(chat_id, "Пожалуйста, введи число.")


def cleanup_guess(chat_id):
    for k in [chat_id, f"{chat_id}_num", f"{chat_id}_att", f"{chat_id}_min", f"{chat_id}_max"]:
        user_states.pop(k, None)


# ====================== ВИСЕЛИЦА ======================
@bot.message_handler(func=lambda m: m.text == '💀 Виселица')
def start_hangman(message):
    chat_id = message.chat.id
    user_states[chat_id] = 'hangman'
    word = random.choice(WORDS)
    hangman_games[chat_id] = {'word': word, 'hidden': ['_' for _ in word], 'attempts': 6, 'used': set()}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔙 Назад')
    bot.send_message(chat_id, f"💀 Виселица\n\nСлово: {' '.join(hangman_games[chat_id]['hidden'])}\nПопыток: 6",
                     reply_markup=markup)


def handle_hangman(message):
    chat_id = message.chat.id
    text = message.text.lower().strip()
    if text == '🔙 назад':
        user_states.pop(chat_id, None)
        hangman_games.pop(chat_id, None)
        bot.send_message(chat_id, "Выход...", reply_markup=games_menu())
        return

    game = hangman_games.get(chat_id)
    if not game:
        return

    if len(text) == 1 and text.isalpha():
        if text in game['used']:
            bot.send_message(chat_id, "Такая буква уже была.")
            return
        game['used'].add(text)
        if text in game['word']:
            for i, letter in enumerate(game['word']):
                if letter == text:
                    game['hidden'][i] = text
        else:
            game['attempts'] -= 1
    elif text == game['word']:
        game['hidden'] = list(game['word'])
    else:
        game['attempts'] -= 1

    if '_' not in game['hidden']:
        bot.send_message(chat_id, f"🎉 **Победа!** Слово: {game['word']}", parse_mode="Markdown")
        user_states.pop(chat_id, None)
        hangman_games.pop(chat_id, None)
    elif game['attempts'] <= 0:
        bot.send_message(chat_id, f"💀 Проигрыш. Слово было: {game['word']}")
        user_states.pop(chat_id, None)
        hangman_games.pop(chat_id, None)
    else:
        bot.send_message(chat_id,
                         f"Слово: {' '.join(game['hidden'])}\nПопыток: {game['attempts']}\nБуквы: {', '.join(sorted(game['used']))}")


# ====================== ПОГОДА ======================
@bot.message_handler(func=lambda m: m.text in ['🌤️ Погода', '/weather'])
def ask_city(message):
    user_states[message.chat.id] = 'waiting_city'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔙 Назад')
    bot.send_message(message.chat.id, "🌍 Введи название города:", reply_markup=markup)


def send_weather(message, city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        data = requests.get(url, timeout=10).json()
        if data.get('cod') != 200:
            bot.send_message(message.chat.id, "Город не найден. Попробуй другой.")
            return

        icon_code = data['weather'][0]['icon'][:2]
        icons = {'01': '☀️', '02': '⛅', '03': '☁️', '04': '☁️', '09': '🌧️', '10': '🌦️', '11': '⛈️', '13': '❄️',
                 '50': '🌫️'}

        text = f"{icons.get(icon_code, '🌤️')} **Погода в {data['name']}**\n" \
               f"🌡️ Температура: {round(data['main']['temp'])}°C\n" \
               f"Ощущается как: {round(data['main']['feels_like'])}°C\n" \
               f"📝 {data['weather'][0]['description'].capitalize()}"

        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())
        user_states.pop(message.chat.id, None)
    except:
        bot.send_message(message.chat.id, "Ошибка получения погоды. Попробуй позже.")


# ====================== ФАКТ ======================
@bot.message_handler(func=lambda m: m.text in ['📚 Интересный факт', '/fact'])
def send_fact(message):
    bot.send_message(message.chat.id, f"📚 **Интересный факт:**\n\n{random.choice(FACTS)}", parse_mode="Markdown")


# ====================== ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ======================
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    chat_id = message.chat.id
    text = message.text
    state = user_states.get(chat_id)

    if state == 'minesweeper_difficulty' or chat_id in minesweeper_games:
        handle_minesweeper(message)
    elif state == 'guess_number':
        handle_guess_number(message)
    elif state == 'hangman':
        handle_hangman(message)
    elif state == 'waiting_city':
        if text == '🔙 Назад':
            user_states.pop(chat_id, None)
            bot.send_message(chat_id, "Главное меню", reply_markup=main_menu())
        else:
            send_weather(message, text)
    elif text == '🔙 Назад':
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "Главное меню", reply_markup=main_menu())
    else:
        if any(g in text.lower() for g in ['привет', 'здравствуй', 'hi', 'hello']):
            bot.send_message(chat_id, "Привет! 😊 Как дела?")
        else:
            bot.send_message(chat_id, "Используй кнопки меню 👇", reply_markup=main_menu())


# ====================== ЗАПУСК ======================
if __name__ == "__main__":
    print("🤖 Бот успешно запущен! Ожидаем сообщения...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"Ошибка: {e}. Перезапуск через 5 секунд...")
            time.sleep(5)