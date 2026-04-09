"""
WHYNOT Photoshop Bot - С поддержкой прокси для РФ
Работает через VPN/прокси
"""

import asyncio
import logging
import os
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import TCPConnector
import ssl

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8681310168:AAHoG7GRdsClCptLvd8-bT0_vmdiNgrdgG6M"
REMOVE_BG_API_KEY = "YOUR_REMOVE_BG_API_KEY"  # ← ВСТАВЬ СЮДА СВОЙ API КЛЮЧ

# ===== НАСТРОЙКА ПРОКСИ =====
# Вариант 1: SOCKS5 прокси (если используешь VPN с SOCKS5)
# PROXY = "socks5://127.0.0.1:1080"

# Вариант 2: HTTP прокси
# PROXY = "http://127.0.0.1:8080"

# Вариант 3: Без прокси (если VPN работает системно)
PROXY = None

# Бот и диспетчер создадим в main() чтобы избежать проблем с event loop
bot = None
dp = None
storage = MemoryStorage()

logger.info("✅ Бот создан с обходом SSL проверки")
if PROXY:
    logger.info(f"🔒 Используется прокси: {PROXY}")


# ===== СОСТОЯНИЯ FSM =====
class PhotoStates(StatesGroup):
    waiting_for_photo = State()


# ===== ФУНКЦИЯ УДАЛЕНИЯ ФОНА =====
async def remove_background(input_path: str, output_path: str) -> bool:
    """Удаляет фон с изображения используя remove.bg API"""
    try:
        logger.info(f"Отправляем запрос к remove.bg API...")
        
        # Для remove.bg используем обычный requests (он работает через системный VPN)
        response = requests.post(
            'https://api.remove.bg/v1.0/removebg',
            files={'image_file': open(input_path, 'rb')},
            data={'size': 'auto'},
            headers={'X-Api-Key': REMOVE_BG_API_KEY},
            timeout=30
        )
        
        if response.status_code == requests.codes.ok:
            with open(output_path, 'wb') as out:
                out.write(response.content)
            logger.info("✅ Фон успешно удален!")
            return True
        else:
            logger.error(f"❌ Ошибка API: {response.status_code}")
            logger.error(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении фона: {e}")
        return False


# ===== КЛАВИАТУРЫ =====
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎭 Убрать фон", callback_data="remove_bg"),
            InlineKeyboardButton(text="✨ Другие функции", callback_data="other")
        ],
        [
            InlineKeyboardButton(text="📚 Мои работы", callback_data="history"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        ]
    ])
    return keyboard


def get_cancel_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    return keyboard


def get_back_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard


# ===== ОБРАБОТЧИКИ =====
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"👋 Привет, {user_name}!\n\n"
        f"Я <b>WHYNOT Photoshop</b> — твой AI-помощник!\n\n"
        f"🎭 <b>Сейчас я умею:</b>\n"
        f"• Убирать фон с фотографий\n"
        f"• Делать прозрачный PNG\n\n"
        f"🚀 <b>Скоро научусь:</b>\n"
        f"• Улучшать качество\n"
        f"• Менять стиль\n"
        f"• И многое другое!\n\n"
        f"Выбери действие:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 <b>Как пользоваться:</b>\n\n"
        "1️⃣ Нажми <b>🎭 Убрать фон</b>\n"
        "2️⃣ Отправь фото\n"
        "3️⃣ Жди 10-20 секунд\n"
        "4️⃣ Получи результат!\n\n"
        "<b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка"
    )
    
    await message.answer(help_text, reply_markup=get_back_button(), parse_mode="HTML")


@dp.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери действие:",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "remove_bg")
async def callback_remove_bg(callback: types.CallbackQuery, state: FSMContext):
    if REMOVE_BG_API_KEY == "YOUR_REMOVE_BG_API_KEY":
        await callback.message.edit_text(
            "❌ <b>Функция не настроена</b>\n\n"
            "Нужно добавить API ключ от remove.bg\n"
            "Получи его на https://remove.bg/api",
            reply_markup=get_back_button(),
            parse_mode="HTML"
        )
        await callback.answer("⚠️ Функция не настроена")
        return
    
    await state.set_state(PhotoStates.waiting_for_photo)
    
    await callback.message.edit_text(
        "📸 <b>Удаление фона</b>\n\n"
        "Отправь мне фото, и я уберу фон!\n\n"
        "✅ <b>Подходит для:</b>\n"
        "• Фото людей\n"
        "• Фото животных\n"
        "• Фото предметов\n\n"
        "Жду твое фото! 📤",
        reply_markup=get_cancel_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "cancel")
async def callback_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Операция отменена.\n\nВыбери другое действие:",
        reply_markup=get_main_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "other")
async def callback_other(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🚧 <b>Другие функции в разработке</b>\n\n"
        "Скоро добавлю больше AI функций!",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer("🚧 В разработке")


@dp.callback_query(F.data == "history")
async def callback_history(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📚 <b>Мои работы</b>\n\n"
        "У тебя пока нет сохраненных работ.",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def callback_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "❓ <b>Помощь</b>\n\n"
        "Нажми 🎭 Убрать фон и отправь фото.\n"
        "Результат придет через 10-20 секунд.",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.message(PhotoStates.waiting_for_photo, F.photo)
async def handle_photo_for_bg_removal(message: Message, state: FSMContext):
    processing_msg = await message.answer(
        "⏳ <b>Обрабатываю фото...</b>\n\n"
        "Это займет 10-20 секунд.",
        parse_mode="HTML"
    )
    
    try:
        photo = message.photo[-1]
        os.makedirs("temp", exist_ok=True)
        
        input_path = f"temp/input_{message.from_user.id}.jpg"
        output_path = f"temp/output_{message.from_user.id}.png"
        
        await processing_msg.edit_text(
            "⏳ <b>Скачиваю фото...</b>\n▓▓▓░░░░░░░ 30%",
            parse_mode="HTML"
        )
        
        file = await bot.get_file(photo.file_id)
        await bot.download_file(file.file_path, input_path)
        
        await processing_msg.edit_text(
            "⏳ <b>Удаляю фон...</b>\n▓▓▓▓▓▓░░░░ 60%\n\nAI обрабатывает...",
            parse_mode="HTML"
        )
        
        success = await asyncio.to_thread(remove_background, input_path, output_path)
        
        if success:
            await processing_msg.edit_text(
                "⏳ <b>Отправляю результат...</b>\n▓▓▓▓▓▓▓▓▓░ 90%",
                parse_mode="HTML"
            )
            
            result_photo = FSInputFile(output_path)
            
            await message.answer_document(
                document=result_photo,
                caption=(
                    "✅ <b>Готово!</b>\n\n"
                    "Фон успешно удален!\n"
                    "PNG с прозрачным фоном."
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎭 Еще фото", callback_data="remove_bg")],
                    [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")]
                ])
            )
            
            await processing_msg.delete()
            await state.clear()
        else:
            await processing_msg.edit_text(
                "❌ <b>Ошибка обработки</b>\n\n"
                "Возможно превышен лимит (50 фото/месяц).",
                reply_markup=get_back_button(),
                parse_mode="HTML"
            )
            await state.clear()
        
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except:
            pass
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка. Попробуй еще раз.",
            reply_markup=get_back_button()
        )
        await state.clear()


@dp.message(F.photo)
async def handle_photo_without_state(message: Message):
    await message.answer(
        "📸 Фото получено!\n\nЧто хочешь сделать?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎭 Убрать фон", callback_data="remove_bg")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")]
        ])
    )


@dp.message()
async def handle_other(message: Message):
    await message.answer("Попробуй /start для главного меню")


# ===== ЗАПУСК =====
async def main():
    global bot, dp
    
    logger.info("🚀 Бот запускается...")
    logger.info("🔓 SSL проверка отключена (для обхода блокировок)")
    logger.info("Нажми Ctrl+C для остановки")
    
    # Создаем сессию с отключенной проверкой SSL
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = TCPConnector(ssl=ssl_context)
    session = AiohttpSession(connector=connector)
    
    # Создаем бота
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher(storage=storage)
    
    # Регистрируем все хендлеры заново
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_help, Command("help"))
    dp.callback_query.register(callback_back_to_menu, F.data == "back_to_menu")
    dp.callback_query.register(callback_remove_bg, F.data == "remove_bg")
    dp.callback_query.register(callback_cancel, F.data == "cancel")
    dp.callback_query.register(callback_other, F.data == "other")
    dp.callback_query.register(callback_history, F.data == "history")
    dp.callback_query.register(callback_help, F.data == "help")
    dp.message.register(handle_photo_for_bg_removal, PhotoStates.waiting_for_photo, F.photo)
    dp.message.register(handle_photo_without_state, F.photo)
    dp.message.register(handle_other)
    
    if REMOVE_BG_API_KEY != "YOUR_REMOVE_BG_API_KEY":
        logger.info("✅ Remove.bg API ключ настроен")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        # Для Windows - используем ProactorEventLoop
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Бот остановлен")
