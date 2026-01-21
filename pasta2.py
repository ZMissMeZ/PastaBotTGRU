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
from bs4 import BeautifulSoup
import requests

# ── Настройки ────────────────────────────────────────────────────────────────
BOT_TOKEN = "8520620674:AAEI6e3RC61QKoZhxI4QOxxRoTtMS0NdN0M"
JSON_FILE = "result.json"
SPECIAL_USER_DROCHIT = 936315572
SPECIAL_USER_PSRAL = 1328231117
MIN_LENGTH = 20
RECENT_LIMIT = 10
SPECIAL_CHANCE = 0.5
OTHER_CHANCE = 0.1

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

teyki_list = []
recently_sent = deque(maxlen=RECENT_LIMIT)

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

# ── Команда /mem ─────────────────────────────────────────────────────────────
@dp.message(Command("mem"))
async def on_mem(message: Message):
    try:
        url = "https://joyreactor.cc/api/v1/posts?tags=мем&limit=20"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=8)
        data = response.json()

        if not data.get("posts"):
            await message.answer("Мемы кончились 😔 Попробуй позже")
            return

        post = random.choice(data["posts"])
        image_url = post.get("image", {}).get("url") or post.get("media", [{}])[0].get("url")

        if image_url:
            if image_url.endswith('.mp4') or 'video' in post.get("media_type", ""):
                await message.answer_video(image_url, caption=post.get("title", "Мем дня 🔥"))
            elif image_url.endswith('.gif'):
                await message.answer_animation(image_url, caption=post.get("title", "Мем дня 🔥"))
            else:
                await message.answer_photo(image_url, caption=post.get("title", "Мем дня 🔥"))
        else:
            await message.answer("Не удалось найти мем 😢 Попробуй ещё раз")
    except Exception as e:
        logging.error(f"JoyReactor ошибка: {e}")
        await message.answer("Что-то пошло не так с мемами... Попробуй позже 😅")

# ── Команда /pinterest <запрос> ──────────────────────────────────────────────
@dp.message(Command("pinterest"))
async def on_pinterest(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Напиши запрос, например: /pinterest мем кот")
        return

    query = args[1].strip().lower()
    meme_keywords = ["meme", "мем", "прикол", "funny"]
    if not any(kw in query for kw in meme_keywords):
        query += " мем"

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
            if src and any(kw in img.get('alt', '').lower() + src for kw in meme_keywords):
                images.append(src)
            if len(images) >= 5:
                break

        if not images:
            await message.answer("Мемных картинок по запросу не нашёл 😔 Попробуй добавить 'мем'")
            return

        random_image = random.choice(images)
        await message.answer_photo(random_image)
    except Exception as e:
        logging.error(f"Pinterest ошибка: {e}")
        await message.answer("Не удалось загрузить картинку с Pinterest 😢")

# ── Запуск ───────────────────────────────────────────────────────────────────
async def main():
    load_teyki()
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())
