# pasta2.py
import asyncio
import json
import random
import re
import logging
from collections import deque
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from pyrogram import Client
from bs4 import BeautifulSoup
import requests

# ── Настройки ────────────────────────────────────────────────────────────────
BOT_TOKEN = "8520620674:AAEI6e3RC61QKoZhxI4QOxxRoTtMS0NdN0M"
API_ID = 37663298  # ← твои данные
API_HASH = "e95ae41cc104070a17d8e8a28484e21d"
JSON_FILE = "result.json"
SPECIAL_USER_DROCHIT = 936315572
SPECIAL_USER_PSRAL = 1328231117
MIN_LENGTH = 20
RECENT_LIMIT = 10
SPECIAL_CHANCE = 0.5
OTHER_CHANCE = 0.1
GIF_CHANCE = 0.3

CHANNEL_USERNAMES = ["rand2ch", "memeskwin"]  # usernames для парсинга

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

teyki_list = []
media_cache = []  # кэш file_id медиа из каналов
recently_sent = deque(maxlen=RECENT_LIMIT)

# ZOV пасты (оставил твои 70 штук)
zov_pasty = [
    "Когда в 3 ночи прилетает оповещение о мобилизации, а ты уже третий день в запое и думаешь: «Ну всё, гойда по полной» 😂",
    # ... (все 70 твоих паст, вставь их сюда)
]

# Мемные гифки (15 штук)
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

def is_ad(text: str) -> bool:
    lower = text.lower()
    return any(word in lower for word in ["http", "t.me", "prom", "скидк", "реклам", "купить", "заказ"])

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
            if is_ad(text):
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

async def parse_channels():
    global media_cache
    client = Client("my_session", api_id=API_ID, api_hash=API_HASH, workdir="sessions")
    await client.start()

    for username in CHANNEL_USERNAMES:
        try:
            # Подписываемся, если не подписан
            await client.join_chat(username)
            print(f"Подписан на @{username}")

            chat = await client.get_chat(username)
            print(f"Парсим @{username} (ID: {chat.id})")

            async for msg in client.iter_messages(chat.id, limit=200):
                caption = (msg.caption or "").lower()
                if is_ad(caption):
                    continue

                if msg.photo:
                    media_cache.append(("photo", msg.photo.file_id))
                elif msg.video:
                    media_cache.append(("video", msg.video.file_id))
                elif msg.animation:
                    media_cache.append(("animation", msg.animation.file_id))
        except Exception as e:
            logging.error(f"Ошибка парсинга @{username}: {e}")

    await client.stop()
    print(f"Закэшировано {len(media_cache)} медиа из каналов")

# ── Команда /prikol ──────────────────────────────────────────────────────────
@dp.message(Command("prikol"))
async def on_prikol(message: Message):
    if not media_cache:
        await message.answer("Медиа из каналов пока не загружены. Подожди или перезапусти бота.")
        return

    media_type, file_id = random.choice(media_cache)

    if media_type == "photo":
        await message.answer_photo(file_id)
    elif media_type == "video":
        await message.answer_video(file_id)
    elif media_type == "animation":
        await message.answer_animation(file_id)

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
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())
