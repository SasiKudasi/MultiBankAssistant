import os
import json
from dotenv import load_dotenv
import telebot
from langchain_community.chat_models import GigaChat
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv('config.env')

credentials = os.getenv('GIGACHAT_CREDENTIALS')
tbot_token = os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(tbot_token)
llm = GigaChat(credentials=credentials, verify_ssl_certs=False)

# Хранилище истории сообщений для каждого пользователя
user_histories = {}

MEMORY_FILE = 'user_session.json'

def load_memory():
    """Загружаем историю чатов из файла"""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for user_id_str, history in data.items():
            user_id = int(user_id_str)
            messages = []
            
            # Восстанавливаем историю сообщений
            if history.get("user"):
                messages.append(HumanMessage(content=history["user"]))
            if history.get("bot"):
                messages.append(AIMessage(content=history["bot"]))
            
            user_histories[user_id] = messages
                
    except FileNotFoundError:
        print("Файл истории не найден, начинаем с чистого листа")

def save_memory():
    """Сохраняем историю чатов в файл"""
    data = {}
    
    for user_id, messages in user_histories.items():
        # Ищем последние сообщения пользователя и бота
        last_user_msg = None
        last_bot_msg = None
        
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) and last_user_msg is None:
                last_user_msg = msg.content
            elif isinstance(msg, AIMessage) and last_bot_msg is None:
                last_bot_msg = msg.content
            
            if last_user_msg and last_bot_msg:
                break
        
        # Сохраняем только если есть оба сообщения
        if last_user_msg and last_bot_msg:
            data[str(user_id)] = {
                "user": last_user_msg,
                "bot": last_bot_msg
            }
    
    # Сохраняем в файл
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@bot.message_handler(content_types=['text'])
def handle_text_message(message):
    user_id = message.chat.id
    text = message.text.strip()

    # Создаем или получаем историю пользователя
    if user_id not in user_histories:
        user_histories[user_id] = [
            SystemMessage(content="Ты полезный ассистент. Отвечай на вопросы пользователя.")
        ]
    
    # Добавляем сообщение пользователя в историю
    user_histories[user_id].append(HumanMessage(content=text))

    try:
        # Используем .invoke() вместо predict/predictMessages
        response = llm.invoke(user_histories[user_id])
        
        # Добавляем ответ AI в историю
        ai_message = AIMessage(content=response.content)
        user_histories[user_id].append(ai_message)

        # Отправляем ответ пользователю
        bot.send_message(user_id, response.content)
        
        # Сохраняем историю
        save_memory()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.send_message(user_id, "Произошла ошибка, попробуйте еще раз")

# Загружаем историю при старте
load_memory()

# Запускаем бота
print("Бот запущен...")
bot.polling(none_stop=True)