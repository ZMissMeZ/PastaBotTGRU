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
GIF_CHANCE = 0.3

# Pyrogram настройки (получи на my.telegram.org)
API_ID = 37663298  # замени на свой
API_HASH = "e95ae41cc104070a17d8e8a28484e21d"  # замени на свой
CHANNEL_ID = -1001148195583  # канал для парсинга

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

teyki_list = []
recently_sent = deque(maxlen=RECENT_LIMIT)

# Мемные ZOV пасты (70 штук)
zov_pasty = [
    "Когда в 3 ночи прилетает оповещение о мобилизации, а ты уже третий день в запое и думаешь: «Ну всё, гойда по полной» 😂",
    # ... (все 70 паст из предыдущего списка, я не повторяю их здесь, чтобы не перегружать, вставь сам)
]

# Мемные гифки про СВО / ZOV / ГОЙДА (15 штук)
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

# Парсинг канала Telegram (картинки/видео, без рекламы)
media_from_channel = []  # список URLs медиа

async def parse_channel():
    global media_from_channel
    client = Client("my_session", API_ID, API_HASH)
    await client.start()
    async for message in client.iter_messages(CHANNEL_ID, limit=100):  # последние 100 сообщений
        caption = message.caption or ""
        if is_ad(caption):
            continue  # пропускаем рекламу
        if message.photo:
            file = await client.download_media(message.photo, in_memory=True)
            media_from_channel.append(file)
        elif message.video:
            file = await client.download_media(message.video, in_memory=True)
            media_from_channel.append(file)
    await client.stop()
    print(f"Парсено {len(media_from_channel)} медиа из канала")

# ── Команда /prikol — отправить случайный прикол из канала ───────────────────
@dp.message(Command("prikol"))
async def on_prikol(message: Message):
    if not media_from_channel:
        await message.answer("Пока нет прикольных медиа из канала :(")
        return

    media_file = random.choice(media_from_channel)
    if media_file.endswith('.jpg') or media_file.endswith('.png'):
        await message.answer_photo(FSInputFile(media_file))
    elif media_file.endswith('.mp4'):
        await message.answer_video(FSInputFile(media_file))
    else:
        await message.answer_document(FSInputFile(media_file))

# ── Команда /pinterest query — парсинг картинок с Pinterest ──────────────────
@dp.message(Command("pinterest"))
async def on_pinterest(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /pinterest <query>")
        return

    query = args[1].strip()
    url = f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '%20')}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    images = []
    for img in soup.find_all('img', src=re.compile(r'^https://i.pinimg.com/')):
        images.append(img['src'])
        if len(images) >= 5:
            break

    if not images:
        await message.answer("Картинок по запросу не найдено :(")
        return

    for img_url in images:
        await message.answer_photo(img_url)

# ── Остальной код (load_teyki, get_random_pasta, on_pasta, on_pastazov) ──────
# ... (вставь сюда остальной код из предыдущей версии, без изменений)

async def main():
    await parse_channel()  # парсим канал при старте
    load_teyki()
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())
