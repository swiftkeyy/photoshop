"""
WHYNOT Photoshop Bot - Улучшенная версия
Использует .env файл для настроек
"""

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка настроек из .env (опционально)
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ .env файл загружен")
except ImportError:
    logger.warning("⚠️ python-dotenv не установлен, используем переменные окружения")

# Получаем токен
BOT_TOKEN = "8681310168:AAGexFEkN6gTZ7cN64o3ZWiRYPsEbhi5mHY"

# Проверка токена (можно убрать эту проверку)
if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    logger.error("❌ Токен не настроен! Отредактируй bot.py или создай .env файл")
    exit(1)

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# ===== КЛАВИАТУРЫ =====

def get_main_menu():
    """Главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📸 Редактировать фото", callback_data="edit_photo"),
            InlineKeyboardButton(text="✨ Генерация", callback_data="generate")
        ],
        [
            InlineKeyboardButton(text="🎨 Шаблоны", callback_data="templates"),
            InlineKeyboardButton(text="📚 Мои работы", callback_data="history")
        ],
        [
            InlineKeyboardButton(text="💎 Кредиты", callback_data="credits"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
        ],
        [
            InlineKeyboardButton(text="❓ Помощь", callback_data="help")
        ]
    ])
    return keyboard


def get_back_button():
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    return keyboard


# ===== ОБРАБОТЧИКИ КОМАНД =====

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Приветствие при старте"""
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"👋 Привет, {user_name}!\n\n"
        f"Я <b>WHYNOT Photoshop</b> — твой AI-помощник для редактирования фото!\n\n"
        f"🎁 У тебя есть <b>3 бесплатные генерации</b> для старта!\n\n"
        f"Что я умею:\n"
        f"• 🎭 Убирать фон\n"
        f"• ✨ Улучшать качество\n"
        f"• 🎨 Менять стиль (аниме, живопись, кино)\n"
        f"• 👔 Менять одежду\n"
        f"• 🌅 Менять фон\n"
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
    """Помощь"""
    help_text = (
        "📖 <b>Как пользоваться:</b>\n\n"
        "1️⃣ Нажми <b>📸 Редактировать фото</b>\n"
        "2️⃣ Загрузи свое фото\n"
        "3️⃣ Выбери что хочешь сделать\n"
        "4️⃣ Получи результат за 30 секунд!\n\n"
        "<b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/balance - Баланс кредитов\n"
        "/templates - Все шаблоны\n\n"
        "<b>Поддержка:</b> @your_support"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )


@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    """Баланс кредитов"""
    # TODO: Получить реальный баланс из БД
    balance = 3
    
    balance_text = (
        f"💎 <b>Твой баланс:</b> {balance} кредитов\n\n"
        f"1 кредит = 1 генерация\n\n"
        f"Купить больше кредитов:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Купить кредиты", callback_data="buy_credits")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    
    await message.answer(
        balance_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@dp.message(Command("templates"))
async def cmd_templates(message: Message):
    """Список шаблонов"""
    templates_text = (
        "🎨 <b>Доступные шаблоны:</b>\n\n"
        "📸 <b>Улучшение фото:</b>\n"
        "• Убрать фон\n"
        "• Улучшить качество\n"
        "• Исправить освещение\n\n"
        "🎭 <b>Стили:</b>\n"
        "• Аниме/Манга\n"
        "• Масляная живопись\n"
        "• Кинематограф\n\n"
        "👔 <b>Мода:</b>\n"
        "• Сменить одежду\n"
        "• Изменить прическу\n\n"
        "💼 <b>Бизнес:</b>\n"
        "• Фото на документы\n"
        "• Фото товара\n\n"
        "🎉 <b>Развлечения:</b>\n"
        "• Киноафиша\n"
        "• Фигурка\n"
        "• Стикер\n\n"
        "<i>Скоро будет еще больше!</i>"
    )
    
    await message.answer(
        templates_text,
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )


# ===== ОБРАБОТЧИКИ CALLBACK =====

@dp.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: types.CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери действие:",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "edit_photo")
async def callback_edit_photo(callback: types.CallbackQuery):
    """Редактирование фото"""
    await callback.message.edit_text(
        "📸 <b>Редактирование фото</b>\n\n"
        "Загрузи фото, которое хочешь отредактировать.\n\n"
        "<i>Поддерживаются форматы: JPG, PNG</i>",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "generate")
async def callback_generate(callback: types.CallbackQuery):
    """Генерация"""
    await callback.message.edit_text(
        "✨ <b>Генерация изображения</b>\n\n"
        "Эта функция пока в разработке.\n"
        "Скоро ты сможешь создавать изображения из текста!",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer("🚧 В разработке")


@dp.callback_query(F.data == "templates")
async def callback_templates(callback: types.CallbackQuery):
    """Шаблоны"""
    await callback.message.edit_text(
        "🎨 <b>Шаблоны</b>\n\n"
        "Выбери категорию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 Улучшение фото", callback_data="cat_enhance")],
            [InlineKeyboardButton(text="🎭 Художественные стили", callback_data="cat_styles")],
            [InlineKeyboardButton(text="👔 Мода и стиль", callback_data="cat_fashion")],
            [InlineKeyboardButton(text="💼 Бизнес", callback_data="cat_business")],
            [InlineKeyboardButton(text="🎉 Развлечения", callback_data="cat_fun")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "history")
async def callback_history(callback: types.CallbackQuery):
    """История"""
    await callback.message.edit_text(
        "📚 <b>Мои работы</b>\n\n"
        "У тебя пока нет сохраненных работ.\n"
        "Создай первую генерацию!",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "credits")
async def callback_credits(callback: types.CallbackQuery):
    """Кредиты"""
    # TODO: Получить реальный баланс
    balance = 3
    
    await callback.message.edit_text(
        f"💎 <b>Баланс кредитов</b>\n\n"
        f"У тебя: <b>{balance} кредитов</b>\n\n"
        f"<b>Пакеты кредитов:</b>\n"
        f"• 10 кредитов — $2.99\n"
        f"• 50 кредитов — $9.99 ⭐\n"
        f"• 150 кредитов — $24.99\n\n"
        f"<i>Или пригласи друга и получи +5 кредитов!</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Купить кредиты", callback_data="buy_credits")],
            [InlineKeyboardButton(text="👥 Пригласить друга", callback_data="referral")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "settings")
async def callback_settings(callback: types.CallbackQuery):
    """Настройки"""
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        "Язык: 🇷🇺 Русский\n"
        "Качество: Стандартное\n"
        "Уведомления: Включены",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Изменить язык", callback_data="change_lang")],
            [InlineKeyboardButton(text="🔔 Уведомления", callback_data="notifications")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def callback_help(callback: types.CallbackQuery):
    """Помощь"""
    await callback.message.edit_text(
        "❓ <b>Помощь</b>\n\n"
        "Если у тебя возникли вопросы:\n\n"
        "📖 /help - Инструкция\n"
        "💬 @your_support - Поддержка\n"
        "📢 @your_channel - Новости\n\n"
        "<b>FAQ:</b>\n"
        "• Как работают кредиты?\n"
        "• Как пригласить друга?\n"
        "• Какие форматы поддерживаются?",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


# Заглушки для остальных callback
@dp.callback_query(F.data.startswith("cat_"))
async def callback_category(callback: types.CallbackQuery):
    await callback.answer("🚧 Категория в разработке")


@dp.callback_query(F.data == "buy_credits")
async def callback_buy_credits(callback: types.CallbackQuery):
    await callback.answer("🚧 Оплата скоро будет доступна")


@dp.callback_query(F.data == "referral")
async def callback_referral(callback: types.CallbackQuery):
    await callback.answer("🚧 Реферальная программа в разработке")


# ===== ОБРАБОТЧИКИ ФОТО =====

@dp.message(F.photo)
async def handle_photo(message: Message):
    """Обработка фото"""
    await message.answer(
        "📸 <b>Фото получено!</b>\n\n"
        "Выбери что хочешь сделать:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎭 Убрать фон", callback_data="action_remove_bg")],
            [InlineKeyboardButton(text="✨ Улучшить качество", callback_data="action_enhance")],
            [InlineKeyboardButton(text="🎨 Изменить стиль", callback_data="action_style")],
            [InlineKeyboardButton(text="🌅 Сменить фон", callback_data="action_change_bg")],
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("action_"))
async def callback_action(callback: types.CallbackQuery):
    """Обработка действий с фото"""
    action = callback.data.replace("action_", "")
    
    await callback.message.edit_text(
        f"⏳ <b>Обрабатываю...</b>\n\n"
        f"Обычно это занимает 15-30 секунд.\n"
        f"Не закрывай чат!",
        parse_mode="HTML"
    )
    
    # TODO: Здесь будет реальная обработка через AI
    await asyncio.sleep(2)
    
    await callback.message.edit_text(
        f"🚧 <b>Функция в разработке</b>\n\n"
        f"Скоро здесь будет настоящая AI-магия!\n"
        f"Следи за обновлениями.",
        reply_markup=get_back_button(),
        parse_mode="HTML"
    )
    
    await callback.answer()


# ===== ОБРАБОТЧИК ОСТАЛЬНЫХ СООБЩЕНИЙ =====

@dp.message()
async def handle_other(message: Message):
    """Обработка остальных сообщений"""
    await message.answer(
        "Я понимаю только команды и фото.\n"
        "Попробуй /start для главного меню",
        reply_markup=get_back_button()
    )


# ===== ЗАПУСК БОТА =====

async def main():
    """Запуск бота"""
    logger.info("🚀 Бот запускается...")
    logger.info("Нажми Ctrl+C для остановки")
    
    # Удаляем старые обновления
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем polling
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Бот остановлен")
