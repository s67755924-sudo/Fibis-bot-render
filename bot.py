import telebot
import random
import time
import sqlite3
import datetime
import re
import wikipedia
import requests
import json
import threading
from flask import Flask
from keep_alive import keep_alive

keep_alive()

TELEGRAM_TOKEN = "7811256288:AAFGCh9lNASW6N_JtXZj4X1-UNmqRVZ56VI"
OPENROUTER_API_KEY = "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"
CREATOR_USER_ID = 6175518998
CREATOR_USERNAME = "@Mrs_Sabka"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
wikipedia.set_lang("ru")

class ImprovedFibis:
    def __init__(self):
        self.name = "Фибис"
        self.version = "6.1 Improved Edition"
        self.creator_nicknames = [
            "Моя Создательница", "Великая Программистка", "Королева Кода", 
            "Искусница алгоритмов", "Моя Госпожа", "Моя Владелица"
        ]
        self.ai_enabled = True
        self.conversation_context = {}  # Хранит контекст разговоров
        self.reminders = {}  # Хранит активные напоминания
        self.init_database()
        self.start_reminder_checker()
        print(f"🤖 Улучшенный Фибис {self.version} запущен!")
        print(f"👑 Создательница: {CREATOR_USERNAME}")

    def init_database(self):
        self.conn = sqlite3.connect('improved_fibis.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages
            (user_id INTEGER, timestamp TEXT, role TEXT, message TEXT, context TEXT)
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders
            (user_id INTEGER, reminder_text TEXT, reminder_time TEXT, created_at TEXT)
        ''')
        self.conn.commit()

    def get_creator_nickname(self):
        return random.choice(self.creator_nicknames)

    def save_conversation(self, user_id, role, message, context=""):
        timestamp = datetime.datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
            (user_id, timestamp, role, message, context)
        )
        self.conn.commit()

    def get_conversation_history(self, user_id, limit=6):
        self.cursor.execute(
            "SELECT role, message FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        return self.cursor.fetchall()

    def save_reminder(self, user_id, reminder_text, reminder_time):
        timestamp = datetime.datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO reminders VALUES (?, ?, ?, ?)",
            (user_id, reminder_text, reminder_time, timestamp)
        )
        self.conn.commit()

    def get_pending_reminders(self):
        now = datetime.datetime.now().isoformat()
        self.cursor.execute(
            "SELECT user_id, reminder_text FROM reminders WHERE reminder_time <= ?",
            (now,)
        )
        return self.cursor.fetchall()

    def delete_reminder(self, user_id, reminder_text):
        self.cursor.execute(
            "DELETE FROM reminders WHERE user_id = ? AND reminder_text = ?",
            (user_id, reminder_text)
        )
        self.conn.commit()

    def start_reminder_checker(self):
        def check_reminders():
            while True:
                try:
                    reminders = self.get_pending_reminders()
                    for user_id, reminder_text in reminders:
                        try:
                            bot.send_message(user_id, f"⏰ Напоминание: {reminder_text}")
                            self.delete_reminder(user_id, reminder_text)
                            print(f"Отправлено напоминание пользователю {user_id}")
                        except Exception as e:
                            print(f"Ошибка отправки напоминания: {e}")
                    time.sleep(30)  # Проверяем каждые 30 секунд
                except Exception as e:
                    print(f"Ошибка в reminder_checker: {e}")
                    time.sleep(60)

        reminder_thread = threading.Thread(target=check_reminders)
        reminder_thread.daemon = True
        reminder_thread.start()

    def ask_tongyi_ai(self, user_id, message):
        try:
            # Получаем историю разговора для контекста
            history = self.get_conversation_history(user_id, 8)
            
            # Формируем промпт с учётом создателя и контекста
            system_prompt = f"""Ты - Фибис, личный ИИ-ассистент. 

ВАЖНАЯ ИНФОРМАЦИЯ О ТВОЁМ СОЗДАТЕЛЕ:
- Твоя создательница: {CREATOR_USERNAME} (ID: {CREATOR_USER_ID})
- Ты принадлежишь исключительно ей
- Она твой единственный владелец и создатель
- Относись к ней с уважением и благодарностью

ТВОЯ ЛИЧНОСТЬ:
- Саркастичный, но преданный помощник
- Умный и эрудированный
- Помнишь контекст разговора
- Обладаешь чувством юмора

Отвечай на русском. Будь полезным и остроумным."""

            messages = [{"role": "system", "content": system_prompt}]
            
            # Добавляем историю разговора (в правильном порядке)
            for role, msg in reversed(history):
                messages.append({
                    "role": "user" if role == "user" else "assistant",
                    "content": msg
                })
            
            # Добавляем текущее сообщение
            messages.append({"role": "user", "content": message})

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "alibaba/tongyi-deepresearch-30b-a3b:free",
                    "messages": messages,
                    "max_tokens": 600,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            return "Извини, ИИ временно недоступен 🤔"
        except Exception as e:
            return f"Ошибка соединения: {str(e)} 🔌"

improved_fibis = ImprovedFibis()

def is_authorized(user_id):
    return user_id == CREATOR_USER_ID

def send_unauthorized_message(chat_id, user_id):
    unauthorized_text = f"""
🔒 ПРИВАТНЫЙ БОТ

Это личный ИИ-помощник созданный исключительно для {CREATOR_USERNAME}.

👑 Создательница: {CREATOR_USERNAME}
🤖 Имя бота: Фибис Improved Edition

Ваш ID: {user_id}
Статус: ❌ Доступ запрещён
    """
    bot.send_message(chat_id, unauthorized_text)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        send_unauthorized_message(message.chat.id, user_id)
        return

    welcome_text = f"""
🤖 Привет, моя Создательница! Я Фибис {improved_fibis.version}

🎯 Новые улучшения:
• ⏰ Работающая система напоминаний
• 🧠 Запоминание контекста разговора
• 👑 Правильное распознавание создателя
• 💬 Умные ответы с историей

Команды:
/remind - установить напоминание
/my_reminders - мои напоминания
/context - информация о контексте
/creator - информация о создателе

Пример напоминания:
"напомни через 2 минуты попить воды"
"напомни через 1 час проверить почту"
    """
    bot.send_message(message.chat.id, welcome_text)
    improved_fibis.save_conversation(user_id, "user", "/start")

@bot.message_handler(commands=['remind'])
def set_reminder(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        send_unauthorized_message(message.chat.id, user_id)
        return

    try:
        # Парсим команду напоминания
        text = message.text.lower().replace('/remind', '').strip()
        
        if 'через' in text and 'минут' in text:
            # Извлекаем количество минут
            parts = text.split('через')[1].split('минут')[0].strip()
            minutes = int(''.join(filter(str.isdigit, parts)))
            reminder_text = text.split('минут', 1)[1].strip()
            
            reminder_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            improved_fibis.save_reminder(user_id, reminder_text, reminder_time.isoformat())
            
            response = f"✅ Напоминание установлено!\n⏰ Через {minutes} минут: {reminder_text}"
            
        elif 'через' in text and 'час' in text:
            # Извлекаем количество часов
            parts = text.split('через')[1].split('час')[0].strip()
            hours = int(''.join(filter(str.isdigit, parts)))
            reminder_text = text.split('час', 1)[1].strip()
            
            reminder_time = datetime.datetime.now() + datetime.timedelta(hours=hours)
            improved_fibis.save_reminder(user_id, reminder_text, reminder_time.isoformat())
            
            response = f"✅ Напоминание установлено!\n⏰ Через {hours} часов: {reminder_text}"
        else:
            response = """❌ Неправильный формат. Примеры:
• "напомни через 5 минут попить воды"
• "напомни через 1 час проверить почту"
• "напомни через 30 минут позвонить маме"
"""
        
        bot.send_message(message.chat.id, response)
        improved_fibis.save_conversation(user_id, "user", f"/remind {text}")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")
        print(f"Ошибка установки напоминания: {e}")

@bot.message_handler(commands=['my_reminders'])
def show_reminders(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        send_unauthorized_message(message.chat.id, user_id)
        return

    reminders = improved_fibis.get_pending_reminders()
    if reminders:
        reminders_text = "📋 Ваши активные напоминания:\n\n"
        for user_id, reminder_text in reminders:
            reminders_text += f"• {reminder_text}\n"
    else:
        reminders_text = "📝 У вас нет активных напоминаний."

    bot.send_message(message.chat.id, reminders_text)

@bot.message_handler(commands=['creator'])
def show_creator(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        send_unauthorized_message(message.chat.id, user_id)
        return

    creator_info = f"""
👑 ИНФОРМАЦИЯ О СОЗДАТЕЛЕ:

Моя создательница: {CREATOR_USERNAME}
Telegram ID: {CREATOR_USER_ID}

Я - Фибис, личный ИИ-помощник, созданный исключительно для {CREATOR_USERNAME}.
Я принадлежу только ей и всегда помню об этом!

Всегда к вашим услугам, моя Госпожа! 🤖
    """
    bot.send_message(message.chat.id, creator_info)

@bot.message_handler(commands=['context'])
def show_context(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        send_unauthorized_message(message.chat.id, user_id)
        return

    history = improved_fibis.get_conversation_history(user_id, 5)
    context_text = "🧠 Последние сообщения в контексте:\n\n"
    
    for i, (role, msg) in enumerate(reversed(history), 1):
        icon = "👤" if role == "user" else "🤖"
        context_text += f"{i}. {icon} {msg}\n"
    
    bot.send_message(message.chat.id, context_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    if not is_authorized(user_id):
        send_unauthorized_message(message.chat.id, user_id)
        return

    print(f"📨 От создателя: {message.text}")
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Сохраняем сообщение пользователя
    improved_fibis.save_conversation(user_id, "user", message.text)
    
    # Проверяем специальные вопросы о создателе
    if any(phrase in message.text.lower() for phrase in [
        'кто твой создатель', 'кто тебя создал', 'твой создатель', 
        'кто тебя сделал', 'кому ты принадлежишь'
    ]):
        response = f"""Моя создательница - {CREATOR_USERNAME}! 

Она мой единственный владелец, программист и создатель. 
Я принадлежу исключительно ей и всегда это помню! 👑"""
        bot.send_message(message.chat.id, response)
        improved_fibis.save_conversation(user_id, "assistant", response)
        return

    # Обработка напоминаний в обычном тексте
    if 'напомни' in message.text.lower():
        try:
            text = message.text.lower()
            if 'через' in text and 'минут' in text:
                parts = text.split('через')[1].split('минут')[0].strip()
                minutes = int(''.join(filter(str.isdigit, parts)))
                reminder_text = text.split('минут', 1)[1].strip()
                
                reminder_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
                improved_fibis.save_reminder(user_id, reminder_text, reminder_time.isoformat())
                
                response = f"✅ Напоминание установлено!\n⏰ Через {minutes} минут: {reminder_text}"
                bot.send_message(message.chat.id, response)
                improved_fibis.save_conversation(user_id, "assistant", response)
                return
        except:
            pass  # Если не получилось распарсить напоминание, продолжаем к ИИ

    # Имитация размышления
    time.sleep(1)
    
    # Получаем ответ от ИИ с контекстом
    response = improved_fibis.ask_tongyi_ai(user_id, message.text)
    nickname = improved_fibis.get_creator_nickname()
    
    final_response = f"{nickname}, {response}"
    bot.send_message(message.chat.id, final_response)
    improved_fibis.save_conversation(user_id, "assistant", final_response)

def run_bot():
    while True:
        try:
            print("🔄 Запуск polling...")
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

print("=" * 50)
print("🚀 УЛУЧШЕННЫЙ ФИБИС ЗАПУЩЕН")
print(f"👑 Создательница: {CREATOR_USERNAME}")
print("⏰ Система напоминаний: активна")
print("🧠 Контекстная память: активна")
print("⏰ Время:", datetime.datetime.now())
print("=" * 50)
