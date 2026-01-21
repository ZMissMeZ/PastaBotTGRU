# bot_pasta.py
import asyncio
import json
import random
import re
import logging
from collections import deque
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from pyrogram import Client
from bs4 import BeautifulSoup  # ← этот импорт теперь будет работать
import requests

# ── Настройки ────────────────────────────────────────────────────────────────
BOT_TOKEN = "8520620674:AAEI6e3RC61QKoZhxI4QOxxRoTtMS0NdN0M"
JSON_FILE = "result.json"
API_ID = 37663298          # ← твой API_ID
API_HASH = "e95ae41cc104070a17d8e8a28484e21d"  # ← твой API_HASH
SPECIAL_USER_DROCHIT = 936315572
SPECIAL_USER_PSRAL = 1328231117
MIN_LENGTH = 20
RECENT_LIMIT = 10
SPECIAL_CHANCE = 0.5
OTHER_CHANCE = 0.1
GIF_CHANCE = 0.3

CHANNELS = ["rand2ch", "memeskwin"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

teyki_list = []
media_cache = []
recently_sent = deque(maxlen=RECENT_LIMIT)

# ZOV пасты и гифки (оставил как было)
zov_pasty = [ ... ]  # твои 70 паст
zov_gifs = [ ... ]   # твои 15 гифок

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

# ── Команда /pasta ───────────────────────────────────────────────────────────
@dp.message(Command("pasta"))
async def on_pasta(message: Message):
    # ... (твой прежний код без изменений)
    pass  # вставь свой код обработки /pasta

# ── Команда /pastazov ────────────────────────────────────────────────────────
@dp.message(Command("pastazov"))
async def on_pastazov(message: Message):
    reply_text = random.choice(zov_pasty)

    if random.random() < GIF_CHANCE:
        gif_url = random.choice(zov_gifs)
        await message.answer_animation(gif_url, caption=reply_text)
    else:
        await message.answer(reply_text, disable_web_page_preview=True)

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
            if src and '236x' in src:  # берём превью, можно заменить на оригинал
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

# ── Запуск ───────────────────────────────────────────────────────────────────
async def main():
    load_teyki()
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())

