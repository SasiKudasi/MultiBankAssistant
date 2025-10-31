import os
import json
import asyncio
from dotenv import load_dotenv
import telebot
from langchain_community.chat_models import GigaChat
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from typing import Dict, Any, Annotated
from langchain_core.prompts import ChatPromptTemplate
from dotenv import find_dotenv, load_dotenv
from langchain_community.chat_models import GigaChat
from langgraph.prebuilt import create_react_agent
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.client import MultiServerMCPClient
from rich import print as rprint

load_dotenv('config.env')

credentials = os.getenv('GIGACHAT_CREDENTIALS')
tbot_token = os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(tbot_token)

llm = GigaChat(credentials=credentials, verify_ssl_certs=False)

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

        last_user_msg = None
        last_bot_msg = None
        
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage) and last_user_msg is None:
                last_user_msg = msg.content
            elif isinstance(msg, AIMessage) and last_bot_msg is None:
                last_bot_msg = msg.content
            
            if last_user_msg and last_bot_msg:
                break

        if last_user_msg and last_bot_msg:
            data[str(user_id)] = {
                "user": last_user_msg,
                "bot": last_bot_msg
            }

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@bot.message_handler(content_types=['text'])
def handle_text_message(message):
    user_id = message.chat.id
    text = message.text.strip()

    if user_id not in user_histories:
        user_histories[user_id] = [
            HumanMessage(content="SYSTEM: Ты полезный ассистент. Отвечай на вопросы пользователя.")
        ]

    user_histories[user_id].append(HumanMessage(content=text))

    try:
        response = llm.invoke(user_histories[user_id])

        ai_message = AIMessage(content=response.content)
        user_histories[user_id].append(ai_message)

        bot.send_message(user_id, response.content)

        save_memory()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.send_message(user_id, "Произошла ошибка, попробуйте еще раз")

load_memory()

bot.polling(none_stop=True)

load_dotenv(find_dotenv())

model = GigaChat(model="GigaChat-2-Max",
                streaming=False,
                max_tokens=8000,
                timeout=600)


def _log(ans):
    for message in ans['messages']:
        rprint(f"[{type(message).__name__}] {message.content} {getattr(message, 'tool_calls', '')}")


async def main():
    async with MultiServerMCPClient(
        {
            "math": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }
    ) as client:
        agent = create_react_agent(model, client.get_tools())
        
        agent_response = await agent.ainvoke({"messages": [
            {"role": "user", "content": "Сколько будет (3 + 5) x 12?"}]})
        _log(agent_response)
        
        agent_response = await agent.ainvoke({"messages": [
            {"role": "user", "content": "Найди сколько лет Джону Доу?"}]})
        _log(agent_response)

    bot.polling(none_stop=True)

asyncio.run(main())