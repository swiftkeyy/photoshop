"""
WHYNOT Photoshop Bot - С AI удалением фона
Простая версия для BotHost
"""

import asyncio
import logging
import os
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, BufferedInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "8681310168:AAHoG7GRdsClCptLvd8-bT0_vmdiNgrdgG6M")
REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY", "sdeuTvFVGwUXhK1sBCJo7rq6")

# Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ===== СОСТОЯНИЯ =====
class PhotoStates(StatesGroup):
    waiting_for_photo = State()


# ===== ФУНКЦИЯ УДАЛЕНИЯ ФОНА =====
def remove_background(image_bytes: bytes) -> bytes:
    """Удаляет фон через remove.bg API"""
    try:
        response = requests.post(
            'https://api.remove.bg/v1.0/removebg',
            files={'image_file': image_bytes},
            data={'size': 'auto'},
            headers={'X-Api-Key': REMOVE_BG_API_KEY},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.content
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None


# ===== КЛАВИАТУРЫ =====
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎭 Убрать фон", callback_data="remove_bg")],
        [InlineKeyboardButton(text="📚 Мои работы", callback_data="history")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])

def back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])

def cancel_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])


# ===== КОМАНДЫ =====
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Я <b>WHYNOT Photoshop</b> — AI-помощник для фото!\n\n"
        f"🎭 <b>Умею:</b>\n"
        f"• Убирать фон с фотографий\n"
        f"• Делать прозрачный PNG\n\n"
        f"Выбери действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Как пользоваться:</b>\n\n"
        "1. Нажми 🎭 Убрать фон\n"
        "2. Отправь фото\n"
        "3. Жди 10-20 секунд\n"
        "4. Получи результат!\n\n"
        "<b>Лимиты:</b> 50 фото/месяц бесплатно",
        reply_markup=back_button(),
        parse_mode="HTML"
    )


# ===== CALLBACK =====
@dp.callback_query(F.data == "back")
async def cb_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "remove_bg")
async def cb_remove_bg(callback: types.CallbackQuery, state: FSMContext):
    if REMOVE_BG_API_KEY == "YOUR_API_KEY_HERE":
        await callback.message.edit_text(
            "❌ <b>API ключ не настроен</b>\n\n"
            "Получи ключ на https://remove.bg/api\n"
            "и добавь в переменные окружения BotHost",
            reply_markup=back_button(),
            parse_mode="HTML"
        )
        await callback.answer("⚠️ Не настроено")
        return
    
    await state.set_state(PhotoStates.waiting_for_photo)
    await callback.message.edit_text(
        "📸 <b>Удаление фона</b>\n\n"
        "Отправь фото, и я уберу фон!\n\n"
        "✅ Подходит для:\n"
        "• Фото людей\n"
        "• Фото животных\n"
        "• Фото предметов\n\n"
        "Жду фото! 📤",
        reply_markup=cancel_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "cancel")
async def cb_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Отменено",
        reply_markup=main_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "history")
async def cb_history(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📚 <b>Мои работы</b>\n\nУ тебя пока нет работ.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def cb_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "❓ <b>Помощь</b>\n\n"
        "Нажми 🎭 Убрать фон и отправь фото.\n"
        "Результат через 10-20 секунд.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== ОБРАБОТКА ФОТО =====
@dp.message(PhotoStates.waiting_for_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    msg = await message.answer("⏳ <b>Обрабатываю...</b>", parse_mode="HTML")
    
    try:
        # Скачиваем фото
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        photo_bytes = await bot.download_file(file.file_path)
        
        await msg.edit_text("⏳ <b>Удаляю фон...</b>\n▓▓▓▓▓░░░░░ 50%", parse_mode="HTML")
        
        # Удаляем фон
        result = await asyncio.to_thread(remove_background, photo_bytes.read())
        
        if result:
            await msg.edit_text("⏳ <b>Отправляю...</b>\n▓▓▓▓▓▓▓▓▓░ 90%", parse_mode="HTML")
            
            # Отправляем результат
            result_file = BufferedInputFile(result, filename="result.png")
            
            await message.answer_document(
                document=result_file,
                caption="✅ <b>Готово!</b>\n\nФон удален!",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎭 Еще фото", callback_data="remove_bg")],
                    [InlineKeyboardButton(text="◀️ В меню", callback_data="back")]
                ])
            )
            
            await msg.delete()
            await state.clear()
        else:
            await msg.edit_text(
                "❌ <b>Ошибка</b>\n\n"
                "Возможно превышен лимит (50 фото/месяц)",
                reply_markup=back_button(),
                parse_mode="HTML"
            )
            await state.clear()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await msg.edit_text(
            "❌ Ошибка. Попробуй еще раз.",
            reply_markup=back_button()
        )
        await state.clear()


@dp.message(F.photo)
async def handle_photo_no_state(message: Message):
    await message.answer(
        "📸 Фото получено!\n\nЧто делать?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎭 Убрать фон", callback_data="remove_bg")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back")]
        ])
    )


@dp.message()
async def handle_other(message: Message):
    await message.answer("Попробуй /start")


# ===== ЗАПУСК =====
async def main():
    logger.info("🚀 Бот запускается...")
    if REMOVE_BG_API_KEY != "YOUR_API_KEY_HERE":
        logger.info("✅ API ключ настроен")
    else:
        logger.warning("⚠️ API ключ не настроен")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
