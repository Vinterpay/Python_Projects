import telebot
from telebot import types
import random
import time
import requests

# ====================== НАСТРОЙКИ ======================
TOKEN = '8702756707:AAEsgJIczsv6eDrs2BnOiFPhMfkfbbV9300'
WEATHER_API_KEY = 'e2baf12da292fdab2d87e1888cf046e3'

bot = telebot.TeleBot(TOKEN)

# Хранилища
user_states = {}

# Факты об ИИ + обычные
AI_FACTS = [
    "ИИ уже может создавать картины, музыку и даже писать код лучше некоторых людей.",
    "ChatGPT-4 прошёл экзамен на адвоката в США лучше 90% людей.",
    "Сейчас нейросети могут генерировать видео по текстовому описанию.",
    "AlphaFold от Google решил проблему сворачивания белков, над которой наука билась 50 лет.",
    "ИИ уже помогает врачам диагностировать рак на ранних стадиях.",
    "Современные модели ИИ могут поддерживать разговор почти неотличимо от человека.",
    "В 2025 году ИИ начал массово использоваться для создания видеоигр.",
    "Нейросети могут переводить речь в реальном времени с сохранением интонации.",
]

GENERAL_FACTS = [
    "Кошки могут производить более 100 различных звуков.",
    "Мёд никогда не портится.",
    "Сердце креветки находится в её голове.",
    "Бабочки пробуют вкус ногами.",
    "Слоны — единственные животные, которые не умеют прыгать."
]

# ====================== КЛАВИАТУРЫ ======================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('🎮 Игры', '📚 Факт об ИИ', '📖 Обычный факт', '🌤️ Погода')
    return markup

def games_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🎲 Угадай число', '🔙 Назад')
    return markup

# ====================== ОСНОВНЫЕ КОМАНДЫ ======================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     "👋 Привет! Я умный Telegram-бот 🤖\n\n"
                     "Могу поиграть, рассказать крутые факты про ИИ или показать погоду.\n"
                     "Выбирай 👇",
                     reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "Просто используй кнопки меню или напиши мне что угодно!")

# ====================== ИГРЫ ======================
@bot.message_handler(func=lambda m: m.text in ['🎮 Игры', '/games'])
def show_games(message):
    bot.send_message(message.chat.id, "🎮 Доступные игры:", reply_markup=games_menu())

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
    bot.send_message(chat_id,
                     "🔢 Я загадал число от **1 до 100**!\nПопробуй угадать 👇",
                     reply_markup=markup, parse_mode="Markdown")

def handle_guess_number(message):
    chat_id = message.chat.id
    text = message.text

    if text == '🔙 Назад':
        cleanup_guess(chat_id)
        bot.send_message(chat_id, "Возвращаемся в меню игр", reply_markup=games_menu())
        return

    try:
        guess = int(text)
        number = user_states.get(f"{chat_id}_num")
        attempts = user_states.get(f"{chat_id}_att", 0) + 1
        user_states[f"{chat_id}_att"] = attempts

        if guess == number:
            bot.send_message(chat_id,
                             f"🎉 **Отлично!** Ты угадал число {number} за {attempts} попыток!",
                             parse_mode="Markdown")
            cleanup_guess(chat_id)
        elif guess < number:
            user_states[f"{chat_id}_min"] = guess + 1
            bot.send_message(chat_id, f"🔼 Больше! Диапазон: {guess + 1} — {user_states[f'{chat_id}_max']}")
        else:
            user_states[f"{chat_id}_max"] = guess - 1
            bot.send_message(chat_id, f"🔽 Меньше! Диапазон: {user_states[f'{chat_id}_min']} — {guess - 1}")
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введи число.")

def cleanup_guess(chat_id):
    for key in [chat_id, f"{chat_id}_num", f"{chat_id}_att", f"{chat_id}_min", f"{chat_id}_max"]:
        user_states.pop(key, None)

# ====================== ФАКТЫ ======================
@bot.message_handler(func=lambda m: m.text in ['📚 Факт об ИИ', '/aifact'])
def send_ai_fact(message):
    fact = random.choice(AI_FACTS)
    bot.send_message(message.chat.id, f"🤖 **Факт об ИИ:**\n\n{fact}", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text in ['📖 Обычный факт', '/fact'])
def send_general_fact(message):
    fact = random.choice(GENERAL_FACTS)
    bot.send_message(message.chat.id, f"📚 **Интересный факт:**\n\n{fact}", parse_mode="Markdown")

# ====================== ПОГОДА ======================
@bot.message_handler(func=lambda m: m.text in ['🌤️ Погода', '/weather'])
def ask_city(message):
    user_states[message.chat.id] = 'waiting_city'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('🔙 Назад')
    bot.send_message(message.chat.id, "🌍 Напиши название города:", reply_markup=markup)

def send_weather(message, city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        data = requests.get(url, timeout=10).json()

        if data.get('cod') != 200:
            bot.send_message(message.chat.id, "❌ Город не найден. Попробуй другой.")
            return

        icon_code = data['weather'][0]['icon'][:2]
        icons = {'01':'☀️','02':'⛅','03':'☁️','04':'☁️','09':'🌧️','10':'🌦️','11':'⛈️','13':'❄️','50':'🌫️'}

        text = f"{icons.get(icon_code, '🌤️')} **Погода в {data['name']}**\n\n" \
               f"🌡️ {round(data['main']['temp'])}°C (ощущается как {round(data['main']['feels_like'])}°C)\n" \
               f"📝 {data['weather'][0]['description'].capitalize()}"

        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())
        user_states.pop(message.chat.id, None)
    except:
        bot.send_message(message.chat.id, "⚠️ Не удалось получить данные о погоде.")

# ====================== РАЗГОВОРЧИВЫЙ БОТ ======================
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    chat_id = message.chat.id
    text = message.text.strip()
    state = user_states.get(chat_id)

    # Обработка состояний
    if state == 'guess_number':
        handle_guess_number(message)
        return
    elif state == 'waiting_city':
        if text == '🔙 Назад':
            user_states.pop(chat_id, None)
            bot.send_message(chat_id, "Главное меню", reply_markup=main_menu())
        else:
            send_weather(message, text)
        return
    elif text == '🔙 Назад':
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "Главное меню", reply_markup=main_menu())
        return

    # Разговорные ответы
    lower_text = text.lower()

    if any(g in lower_text for g in ['привет', 'здравствуй', 'hi', 'hello', 'добрый']):
        bot.send_message(chat_id, "Привет! Рад тебя видеть 😊 Чем займёмся?")
    elif any(word in lower_text for word in ['как дела', 'как ты', 'how are you']):
        bot.send_message(chat_id, "У меня всё отлично! А у тебя как настроение?")
    elif 'спасибо' in lower_text:
        bot.send_message(chat_id, "Пожалуйста! Всегда рад помочь ❤️")
    elif any(word in lower_text for word in ['пока', 'до свидания', 'goodbye', 'bye']):
        bot.send_message(chat_id, "До встречи! Возвращайся скорее 🤖")
    elif 'кто ты' in lower_text or 'ты кто' in lower_text:
        bot.send_message(chat_id, "Я Telegram-бот, созданный чтобы развлекать и помогать 😎")
    elif 'иил' in lower_text or 'нейросет' in lower_text or 'gpt' in lower_text:
        bot.send_message(chat_id, "Хочешь факт про ИИ? Нажми кнопку «📚 Факт об ИИ»!")
    else:
        # Если ничего не подошло — предлагаем меню
        bot.send_message(chat_id, "Не совсем понял 😅\n\nИспользуй кнопки меню:", reply_markup=main_menu())

# ====================== ЗАПУСК ======================
if __name__ == "__main__":
    print("🤖 Бот успешно запущен! Ожидаем сообщения...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"Ошибка: {e}. Перезапуск через 5 секунд...")
            time.sleep(5)