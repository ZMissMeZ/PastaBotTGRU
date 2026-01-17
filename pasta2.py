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

# ── Настройки ────────────────────────────────────────────────────────────────
BOT_TOKEN = "8520620674:AAEI6e3RC61QKoZhxI4QOxxRoTtMS0NdN0M"
JSON_FILE = "result.json"
ALLOWED_GROUP_CHAT_ID = -1002675373747    # только эта группа (если нужно ограничить)
MIN_LENGTH = 20
RECENT_LIMIT = 10                         # не повторять последние 10

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

# ── Команда /pasta ───────────────────────────────────────────────────────────
@dp.message(Command("pasta"))
async def send_random_pasta(message: Message):
    chat_id = message.chat.id

    # Разрешаем в личке ИЛИ в указанной группе
    if chat_id != ALLOWED_GROUP_CHAT_ID and not message.chat.type == "private":
        return  # игнорируем в других группах

    if not teyki_list:
        await message.answer("Пока нет текстовых паст в базе :(")
        return

    candidates = [t for t in teyki_list if t not in recently_sent]
    if not candidates:
        candidates = teyki_list

    text = random.choice(candidates)
    recently_sent.append(text)

    text = re.sub(r'\s*#тейк\s*', ' ', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'\s+', ' ', text).strip()

    try:
        await message.answer(text, disable_web_page_preview=True)
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        await message.answer("Не получилось отправить пасту, попробуй ещё раз.")

# ── Запуск ───────────────────────────────────────────────────────────────────
async def main():
    load_teyki()
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())
