# ── Команда /mem — случайный русский мем (картинка/гифка) ─────────────────────
@dp.message(Command("mem"))
async def on_mem(message: Message):
    try:
        # Основной источник — главная страница JoyReactor (скрапинг)
        url = "https://joyreactor.cc/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # если ошибка HTTP — сразу вылетит

        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем все картинки постов (класс postImage — стандартный для JoyReactor)
        images = []
        for img in soup.find_all('img', class_='postImage'):
            src = img.get('src') or img.get('data-src')
            if src and 'post' in src and not 'avatar' in src and (src.endswith('.jpg') or src.endswith('.png') or src.endswith('.gif')):
                images.append(src)

        if images:
            random_img = random.choice(images)
            await message.answer_photo(random_img, caption="Случайный мем 🔥")
            logging.info(f"Отправлен мем из JoyReactor: {random_img}")
            return

        # Резервный источник — Memepedia свежие
        url = "https://memepedia.ru/"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and 'memepedia' in src and (src.endswith('.jpg') or src.endswith('.png') or src.endswith('.gif')):
                images.append(src)

        if images:
            random_img = random.choice(images)
            await message.answer_photo(random_img, caption="Случайный мем с Memepedia 🔥")
            logging.info(f"Отправлен мем из Memepedia: {random_img}")
            return

        await message.answer("Мемы пока не грузятся 😔 Попробуй позже или /mem ещё раз")

    except Exception as e:
        logging.error(f"Ошибка в /mem: {str(e)}")
        await message.answer("Что-то пошло не так с мемами... Попробуй позже 😅")
