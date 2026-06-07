import telebot
from telebot import types
import random
import time
import requests
import json
import os
from datetime import datetime

# ====================== НАСТРОЙКИ ======================
TOKEN = '8702756707:AAEsgJIczsv6eDrs2BnOiFPhMfkfbbV9300'
WEATHER_API_KEY = 'e2baf12da292fdab2d87e1888cf046e3'

bot = telebot.TeleBot(TOKEN)

# Хранилища
user_states = {}
user_stats = {}
last_fact = {}
quiz_data = {}

STATS_FILE = 'stats.json'
LOG_FILE = 'logs.txt'

# Загрузка статистики
if os.path.exists(STATS_FILE):
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            user_stats = json.load(f)
    except:
        user_stats = {}


def save_stats():
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_stats, f, ensure_ascii=False, indent=2)


def log_to_file(message, direction="→"):
    user = message.from_user
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_text = f"[{timestamp}] {direction} ID:{user.id} @{user.username or '—'} ({user.first_name}): {message.text}\n"

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_text)

    print(log_text.strip())


# ====================== ДАННЫЕ ======================
AI_FACTS = [
    "ИИ уже может создавать картины, музыку и даже писать код лучше некоторых людей.",
    "ChatGPT-4 прошёл экзамен на адвоката в США лучше 90% людей.",
    "AlphaFold от Google решил проблему сворачивания белков, над которой наука билась 50 лет.",
    "Современные нейросети могут генерировать видео по текстовому описанию.",
    "В 2025 году ИИ начал массово использоваться для создания видеоигр.",
    "Нейросети могут переводить речь в реальном времени с сохранением интонации.",
]

QUIZ_QUESTIONS = [
    {"q": "Какой ИИ победил чемпиона мира по го?", "a": ["AlphaGo", "ChatGPT", "DALL-E", "Watson"], "correct": 0},
    {"q": "Что такое LLM?", "a": ["Большая языковая модель", "Локальная линейная машина", "Лазерный луч"],
     "correct": 0},
    {"q": "Кто создал ChatGPT?", "a": ["OpenAI", "Google", "Meta", "Apple"], "correct": 0},
    {"q": "Что делает AlphaFold?", "a": ["Предсказывает структуру белков", "Генерирует картинки", "Переводит речь"],
     "correct": 0},
]


# ====================== КЛАВИАТУРЫ ======================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('🎮 Игры', '📚 Факт об ИИ', '🧠 Квиз по ИИ', '💬 Поговори со мной', '🌤️ Погода')
    return markup


def games_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🎲 Угадай число', '🔙 Назад')
    return markup


# ====================== ОСНОВНЫЕ КОМАНДЫ ======================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    log_to_file(message)
    bot.send_message(message.chat.id, "👋 Привет! Я умный бот 🤖\nВыбирай через кнопки:", reply_markup=main_menu())


@bot.message_handler(commands=['stats'])
def show_stats(message):
    log_to_file(message)
    uid = str(message.from_user.id)
    stats = user_stats.get(uid, {"guess_wins": 0, "quiz_wins": 0})
    text = f"📊 Твоя статистика:\n\n🎲 Угадай число: {stats.get('guess_wins', 0)} побед\n🧠 Квиз по ИИ: {stats.get('quiz_wins', 0)} идеальных"
    bot.send_message(message.chat.id, text)


# ====================== ФАКТЫ ======================
@bot.message_handler(func=lambda m: m.text in ['📚 Факт об ИИ', '/aifact'])
def send_ai_fact(message):
    log_to_file(message)
    chat_id = message.chat.id
    facts = [f for f in AI_FACTS if f != last_fact.get(chat_id)]
    fact = random.choice(facts) if facts else random.choice(AI_FACTS)
    last_fact[chat_id] = fact
    bot.send_message(chat_id, f"🤖 **Факт об ИИ:**\n\n{fact}", parse_mode="Markdown")


# ====================== ИГРЫ ======================
@bot.message_handler(func=lambda m: m.text in ['🎮 Игры', '/games'])
def show_games(message):
    log_to_file(message)
    bot.send_message(message.chat.id, "🎮 Выбери игру:", reply_markup=games_menu())


# Угадай число
@bot.message_handler(func=lambda m: m.text == '🎲 Угадай число')
def start_guess_number(message):
    log_to_file(message)
    chat_id = message.chat.id
    user_states[chat_id] = 'guess_number'
    number = random.randint(1, 100)
    user_states[f"{chat_id}_num"] = number
    user_states[f"{chat_id}_att"] = 0

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔙 Назад')
    bot.send_message(chat_id, "🔢 Я загадал число от 1 до 100!\nНапиши число:", reply_markup=markup)


def handle_guess_number(message):
    chat_id = message.chat.id
    if message.text == '🔙 Назад':
        cleanup_guess(chat_id)
        bot.send_message(chat_id, "Возвращаемся...", reply_markup=games_menu())
        return

    try:
        guess = int(message.text)
        number = user_states.get(f"{chat_id}_num")
        attempts = user_states.get(f"{chat_id}_att", 0) + 1
        user_states[f"{chat_id}_att"] = attempts

        if guess == number:
            bot.send_message(chat_id, f"🎉 **Победа!** Число {number} за {attempts} попыток!", parse_mode="Markdown")
            uid = str(message.from_user.id)
            if uid not in user_stats:
                user_stats[uid] = {"guess_wins": 0, "quiz_wins": 0}
            user_stats[uid]["guess_wins"] = user_stats[uid].get("guess_wins", 0) + 1
            save_stats()
            cleanup_guess(chat_id)
        elif guess < number:
            bot.send_message(chat_id, "🔼 Моё число больше!")
        else:
            bot.send_message(chat_id, "🔽 Моё число меньше!")
    except:
        bot.send_message(chat_id, "Пожалуйста, введи число.")


def cleanup_guess(chat_id):
    for k in [chat_id, f"{chat_id}_num", f"{chat_id}_att"]:
        user_states.pop(k, None)


# ====================== КВИЗ ======================
@bot.message_handler(func=lambda m: m.text in ['🧠 Квиз по ИИ', '/quiz'])
def start_quiz(message):
    log_to_file(message)
    chat_id = message.chat.id
    user_states[chat_id] = 'quiz'
    quiz_data[chat_id] = {"score": 0, "question": 0}

    send_quiz_question(chat_id)


def send_quiz_question(chat_id):
    q_index = quiz_data[chat_id]["question"]
    q = QUIZ_QUESTIONS[q_index]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for ans in q["a"]:
        markup.add(ans)
    markup.add('🔙 Завершить квиз')
    bot.send_message(chat_id, f"Вопрос {q_index + 1}/{len(QUIZ_QUESTIONS)}:\n\n{q['q']}", reply_markup=markup)


def handle_quiz(message):
    chat_id = message.chat.id
    if message.text == '🔙 Завершить квиз':
        finish_quiz(chat_id)
        return

    q_index = quiz_data[chat_id]["question"]
    q = QUIZ_QUESTIONS[q_index]

    if message.text == q["a"][q["correct"]]:
        quiz_data[chat_id]["score"] += 1
        bot.send_message(chat_id, "✅ Правильно!")
    else:
        bot.send_message(chat_id, f"❌ Неправильно. Правильный ответ: {q['a'][q['correct']]}")

    quiz_data[chat_id]["question"] += 1
    if quiz_data[chat_id]["question"] < len(QUIZ_QUESTIONS):
        send_quiz_question(chat_id)
    else:
        finish_quiz(chat_id)


def finish_quiz(chat_id):
    score = quiz_data[chat_id]["score"]
    bot.send_message(chat_id, f"🏁 Квиз завершён! Результат: {score}/{len(QUIZ_QUESTIONS)}")

    uid = str(chat_id)
    if uid not in user_stats:
        user_stats[uid] = {"guess_wins": 0, "quiz_wins": 0}
    if score == len(QUIZ_QUESTIONS):
        user_stats[uid]["quiz_wins"] = user_stats[uid].get("quiz_wins", 0) + 1
        save_stats()

    del quiz_data[chat_id]
    user_states.pop(chat_id, None)
    bot.send_message(chat_id, "Главное меню", reply_markup=main_menu())


# ====================== РЕЖИМ РАЗГОВОРА ======================
@bot.message_handler(func=lambda m: m.text == '💬 Поговори со мной')
def start_talk_mode(message):
    log_to_file(message)
    user_states[message.chat.id] = 'talk_mode'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔙 Закончить разговор')
    bot.send_message(message.chat.id, "💬 Режим разговора включён!\nПиши что угодно.", reply_markup=markup)


def handle_talk_mode(message):
    responses = ["Интересно! Расскажи подробнее.", "А что ты думаешь об этом?", "Хорошая мысль 😊", "Забавно!",
                 "Продолжай..."]
    bot.send_message(message.chat.id, random.choice(responses))


# ====================== ПОГОДА ======================
@bot.message_handler(func=lambda m: m.text in ['🌤️ Погода', '/weather'])
def ask_city(message):
    log_to_file(message)
    user_states[message.chat.id] = 'waiting_city'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔙 Назад')
    bot.send_message(message.chat.id, "🌍 Введи название города:", reply_markup=markup)


def send_weather(message, city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        data = requests.get(url, timeout=10).json()
        if data.get('cod') != 200:
            bot.send_message(message.chat.id, "Город не найден.")
            return

        icon_code = data['weather'][0]['icon'][:2]
        icons = {'01': '☀️', '02': '⛅', '03': '☁️', '04': '☁️', '09': '🌧️', '10': '🌦️', '11': '⛈️', '13': '❄️',
                 '50': '🌫️'}

        text = f"{icons.get(icon_code, '🌤️')} **{data['name']}**\n" \
               f"🌡️ {round(data['main']['temp'])}°C (ощущается {round(data['main']['feels_like'])}°C)\n" \
               f"💧 Влажность: {data['main']['humidity']}%\n" \
               f"🌬️ Ветер: {data['wind']['speed']} м/с\n" \
               f"📝 {data['weather'][0]['description'].capitalize()}"

        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())
        user_states.pop(message.chat.id, None)
    except:
        bot.send_message(message.chat.id, "Ошибка получения погоды.")


# ====================== ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ======================
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    log_to_file(message)
    chat_id = message.chat.id
    text = message.text.strip()
    state = user_states.get(chat_id)

    if state == 'guess_number':
        handle_guess_number(message)
    elif state == 'quiz':
        handle_quiz(message)
    elif state == 'talk_mode':
        if text == '🔙 Закончить разговор':
            user_states.pop(chat_id, None)
            bot.send_message(chat_id, "Режим разговора завершён.", reply_markup=main_menu())
        else:
            handle_talk_mode(message)
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
        bot.send_message(chat_id, "Используй кнопки меню 👇", reply_markup=main_menu())


# ====================== ЗАПУСК ======================
if __name__ == "__main__":
    print("🤖 Бот запущен! Логи пишутся в logs.txt")
    # Очистка старого лога при запуске
    if os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()

    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except KeyboardInterrupt:
            print("Бот остановлен вручную.")
            break
        except Exception as e:
            print(f"Ошибка: {e}. Перезапуск через 5 сек...")
            time.sleep(5)