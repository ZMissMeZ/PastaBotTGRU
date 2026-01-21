# pasta2.py
import asyncio
import json
import random
import re
import logging
from collections import deque
from io import BytesIO
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InputFile
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from bs4 import BeautifulSoup
import requests

# ── Настройки ────────────────────────────────────────────────────────────────
BOT_TOKEN = "8520620674:AAEI6e3RC61QKoZhxI4QOxxRoTtMS0NdN0M"
API_ID = 37663298
API_HASH = "e95ae41cc104070a17d8e8a28484e21d"
SESSION_STRING = "1ApWapzMBuxKduX8s5zxdlU0sVnfBpD90549W0pRm8VNHLb7k1OI7wcAXDVtqTwf2UkrNwncTxllSdc0qT5dhX59_CQyrW1tH6erac9V1AmQ1Nqyo7HYkAH6YKob74z-EHb_zKcn9rzHXPCBQiQdHmKa3fLu1T7TJ7P_KLyXB4lexBzvxJ5KVX10zCg0okXkjlAIxhqpFs017LkMkcmqVL7QUrd9jtIdN3ZgVyNA55vTACsjNw4MS4eU9_QHKbOmkz6oQE0wALLskSSjdvXAJ2gW1SPJdE119v9qz3ACz1Y6n4QKYZhUTfx7ufyGwjEZVTkhRztSJZvBttmKDkWbYTKIFfQm9hJA="

JSON_FILE = "result.json"
SPECIAL_USER_DROCHIT = 936315572
SPECIAL_USER_PSRAL = 1328231117
MIN_LENGTH = 20
RECENT_LIMIT = 10
SPECIAL_CHANCE = 0.5
OTHER_CHANCE = 0.1
GIF_CHANCE = 0.3

CHANNEL_USERNAMES = ["rand2ch", "memeskwin"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

teyki_list = []
media_cache = []  # список (type, bytes_io)
recently_sent = deque(maxlen=RECENT_LIMIT)

# ZOV пасты (вставь свои 70 штук)
zov_pasty = [
    "Когда в 3 ночи прилетает оповещение о мобилизации, а ты уже третий день в запое и думаешь: «Ну всё, гойда по полной» 😂",
    # ... все твои пасты сюда
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

# ── Парсинг каналов без фильтров ─────────────────────────────────────────────
async def parse_channels():
    global media_cache
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("Сессия не авторизована! Проверь SESSION_STRING.")
            return

        for username in CHANNEL_USERNAMES:
            try:
                entity = await client.get_entity(username)
                print(f"Получен канал @{username} (ID: {entity.id})")

                # Автоподписка
                if not hasattr(entity, 'participant') or not entity.participant:
                    await client(JoinChannelRequest(entity))
                    print(f"Подписался на @{username}")

                async for message in client.iter_messages(entity, limit=300):
                    if message.photo:
                        bytes_io = await message.download_media(file=BytesIO())
                        if bytes_io:
                            bytes_io.seek(0)
                            media_cache.append(("photo", bytes_io))
                    elif message.video:
                        bytes_io = await message.download_media(file=BytesIO())
                        if bytes_io:
                            bytes_io.seek(0)
                            media_cache.append(("video", bytes_io))
                    elif message.gif or (message.document and message.document.mime_type.startswith('video/')):
                        bytes_io = await message.download_media(file=BytesIO())
                        if bytes_io:
                            bytes_io.seek(0)
                            media_cache.append(("animation", bytes_io))

            except Exception as e:
                logging.error(f"Ошибка парсинга @{username}: {e}")

        print(f"Закэшировано {len(media_cache)} медиа из каналов")
    except Exception as e:
        logging.error(f"Глобальная ошибка Telethon: {e}")
    finally:
        await client.disconnect()

# ── Команда /prikol ──────────────────────────────────────────────────────────
@dp.message(Command("prikol"))
async def on_prikol(message: Message):
    if not media_cache:
        await message.answer("Медиа из каналов пока не загружены. Перезапусти бота или подожди 1–2 минуты.")
        return

    media_type, bytes_io = random.choice(media_cache)
    bytes_io.seek(0)  # обязательно!

    try:
        if media_type == "photo":
            await message.answer_photo(InputFile(bytes_io, filename="photo.jpg"))
        elif media_type == "video":
            await message.answer_video(InputFile(bytes_io, filename="video.mp4"))
        elif media_type == "animation":
            await message.answer_animation(InputFile(bytes_io, filename="animation.gif"))
        print(f"Отправлено медиа: {media_type}")
    except Exception as e:
        logging.error(f"Ошибка отправки медиа: {e}")
        await message.answer(f"Не удалось отправить прикол: {str(e)} 😢 Попробуй ещё раз.")

# ── Остальные команды (без изменений) ────────────────────────────────────────
# ... (вставь сюда свои /pasta и /pastazov из предыдущей версии)

# ── Запуск ───────────────────────────────────────────────────────────────────
async def main():
    load_teyki()
    await parse_channels()  # парсим каналы при старте
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())
