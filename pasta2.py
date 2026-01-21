# pasta2.py
import asyncio
import json
import random
import re
import logging
from collections import deque
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from telethon import TelegramClient
from telethon.sessions import StringSession
from bs4 import BeautifulSoup
import requests

# ── Настройки ────────────────────────────────────────────────────────────────
BOT_TOKEN = "8520620674:AAEI6e3RC61QKoZhxI4QOxxRoTtMS0NdN0M"
API_ID = 37663298
API_HASH = "e95ae41cc104070a17d8e8a28484e21d"
JSON_FILE = "result.json"
SPECIAL_USER_DROCHIT = 936315572
SPECIAL_USER_PSRAL = 1328231117
MIN_LENGTH = 20
RECENT_LIMIT = 10
SPECIAL_CHANCE = 0.5
OTHER_CHANCE = 0.1
GIF_CHANCE = 0.3

CHANNEL_USERNAMES = ["rand2ch", "memeskwin"]

# Твоя строка сессии Telethon (вставлена)
SESSION_STRING = "1ApWapzMBuxKduX8s5zxdlU0sVnfBpD90549W0pRm8VNHLb7k1OI7wcAXDVtqTwf2UkrNwncTxllSdc0qT5dhX59_CQyrW1tH6erac9V1AmQ1Nqyo7HYkAH6YKob74z-EHb_zKcn9rzHXPCBQiQdHmKa3fLu1T7TJ7P_KLyXB4lexBzvxJ5KVX10zCg0okXkjlAIxhqpFs017LkMkcmqVL7QUrd9jtIdN3ZgVyNA55vTACsjNw4MS4eU9_QHKbOmkz6oQE0wALLskSSjdvXAJ2gW1SPJdE119v9qz3ACz1Y6n4QKYZhUTfx7ufyGwjEZVTkhRztSJZvBttmKDkWbYTKIFfQm9hJA="

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

teyki_list = []
media_cache = []  # список (type, media) из каналов
recently_sent = deque(maxlen=RECENT_LIMIT)

# ZOV пасты (вставь свои 70 штук)
zov_pasty = [
    "Когда в 3 ночи прилетает оповещение о мобилизации, а ты уже третий день в запое и думаешь: «Ну всё, гойда по полной» 😂",
    # ... добавь все свои пасты сюда
]

# Гифки ZOV
zov_gifs = [
    "https://media.tenor.com/ND_8Z8BDk-wAAAAM/объявлена-гойда.gif",
    "https://media.tenor.com/THnsLR2MfUUAAAAM/охлобыстин-гойда.gif",
    "https://media.tenor.com/qqV2NeMwhwQAAAAC/гойда-zov.gif",
    "https://media.tenor.com/1vKzKzKzKzKAAAAC/zov-гойда.gif",
    "https://media.tenor.com/abc123def456AAAAC/сво-гойда.gif",
    "https://media.tenor.com/xyz789abc123AAAAM/потужно-гойда.gif",
    "https://media.tenor.com/potuzhno-zovAAAAC/гойда-сво.gif",
    "https://media.tenor.com/goyda-powerAAAAM/zov-сво.gif",
    "https://media.tenor.com/russian-spiritAAAAC/гойда.gif",
    "https://media.tenor.com/warrior-zovAAAAM/сво-гойда.gif",
    "https://media.tenor.com/putin-goydaAAAAC/zov.gif",
    "https://media.tenor.com/soldier-zovAAAAM/гойда-потужно.gif",
    "https://media.tenor.com/strong-russiaAAAAC/сво.gif",
    "https://media.tenor.com/victory-goydaAAAAM/zov.gif",
    "https://media.tenor.com/goyda-brothersAAAAC/сво-потужно.gif"
]

def clean_text(raw_text):
    if isinstance(raw_text, str):
        return raw_text.strip()
    if isinstance(raw_text, list):
        return "".join(
            part["text"] if isinstance(part, dict) and "text" in part else ""
            for part in raw_text
        ).strip()
    return ""

def load_teyki():
    global teyki_list
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        messages = data.get("messages", [])

        for msg in messages:
            if any(k in msg for k in ["photo", "video", "document", "sticker", "voice", "audio"]):
                continue

            text = clean_text(msg.get("text", ""))
            if not text or len(text) < MIN_LENGTH:
                continue
            if "#тейк" not in text:
                continue

            teyki_list.append(text)

        print(f"\n=== Найдено {len(teyki_list)} текстовых паст с #тейк ===\n")

    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        exit(1)

async def get_random_pasta():
    candidates = [t for t in teyki_list if t not in recently_sent]
    if not candidates:
        candidates = teyki_list

    text = random.choice(candidates)
    recently_sent.append(text)

    text = re.sub(r'\s*#тейк\s*', ' ', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\s+', ' ', text).strip()

    return text

# ── Парсинг каналов через Telethon (без фильтров) ────────────────────────────
async def parse_channels():
    global media_cache
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("Сессия не авторизована! Запусти tele_auth.py локально и обнови SESSION_STRING.")
            return

        for username in CHANNEL_USERNAMES:
            try:
                entity = await client.get_entity(username)
                print(f"Получен канал @{username} (ID: {entity.id})")

                async for message in client.iter_messages(entity, limit=200):
                    # Без фильтров — берём всё медиа
                    if message.photo:
                        media_cache.append(("photo", message.photo))
                    elif message.video:
                        media_cache.append(("video", message.video))
                    elif message.gif or (message.document and message.document.mime_type.startswith('video/')):
                        media_cache.append(("animation", message.document))
            except Exception as e:
                logging.error(f"Ошибка парсинга @{username}: {e}")

        print(f"Закэшировано {len(media_cache)} медиа из каналов")
    finally:
        await client.disconnect()

# ── Команда /prikol ──────────────────────────────────────────────────────────
@dp.message(Command("prikol"))
async def on_prikol(message: Message):
    if not media_cache:
        await message.answer("Медиа из каналов пока не загружены. Перезапусти бота.")
        return

    media_type, media = random.choice(media_cache)

    try:
        if media_type == "photo":
            await message.answer_photo(media)
        elif media_type == "video":
            await message.answer_video(media)
        elif media_type == "animation":
            await message.answer_animation(media)
    except Exception as e:
        logging.error(f"Ошибка отправки медиа: {e}")
        await message.answer("Не удалось отправить прикол 😢 Попробуй ещё раз.")

# ── Команда /pinterest query ─────────────────────────────────────────────────
@dp.message(Command("pinterest"))
async def on_pinterest(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /pinterest <запрос>")
        return

    query = args[1].strip()
    url = f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        images = []
        for img in soup.find_all('img', src=re.compile(r'^https://i\.pinimg\.com/')):
            src = img.get('src')
            if src:
                images.append(src)
            if len(images) >= 5:
                break

        if not images:
            await message.answer("Картинок по запросу не найдено :(")
            return

        for img_url in images:
            await message.answer_photo(img_url)
    except Exception as e:
        logging.error(f"Ошибка парсинга Pinterest: {e}")
        await message.answer("Не удалось загрузить картинки с Pinterest 😢")

# ── Команда /pasta ───────────────────────────────────────────────────────────
@dp.message(Command("pasta"))
async def on_pasta(message: Message):
    user_id = message.from_user.id
    chat_type = message.chat.type

    if not teyki_list:
        await message.answer("Пока нет текстовых паст в базе :(")
        return

    reply_text = ""

    if chat_type == "private":
        if user_id == SPECIAL_USER_DROCHIT:
            if random.random() < SPECIAL_CHANCE:
                reply_text = "Создатель этого бота тайно дрочит на тебя"
            else:
                reply_text = await get_random_pasta()
        elif user_id == SPECIAL_USER_PSRAL:
            if random.random() < SPECIAL_CHANCE:
                count = random.randint(1, 100)
                reply_text = f"Сегодня ты посрал {count} раз"
            else:
                reply_text = await get_random_pasta()
        else:
            reply_text = await get_random_pasta()
            if random.random() < OTHER_CHANCE:
                reply_text += "\n\nрецепт фасослей 1. Закипитити во ду\n2. Пашол нахуй"
    else:
        reply_text = await get_random_pasta()
        if random.random() < OTHER_CHANCE:
            reply_text += "\n\nрецепт фасослей 1. Закипитити во ду\n2. Пашол нахуй"

    await message.answer(reply_text, disable_web_page_preview=True)

# ── Команда /pastazov ────────────────────────────────────────────────────────
@dp.message(Command("pastazov"))
async def on_pastazov(message: Message):
    reply_text = random.choice(zov_pasty)

    if random.random() < GIF_CHANCE:
        gif_url = random.choice(zov_gifs)
        await message.answer_animation(gif_url, caption=reply_text)
    else:
        await message.answer(reply_text, disable_web_page_preview=True)

# ── Запуск ───────────────────────────────────────────────────────────────────
async def main():
    load_teyki()
    await parse_channels()  # парсим каналы при старте
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())
