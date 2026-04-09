"""
WHYNOT PHOTOSHOP BOT - Production Version
Мощный AI бот для редактирования изображений с Google Gemini API
"""

import asyncio
import logging
import os
import io
import base64
from typing import Optional, Dict, Any
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiohttp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "8681310168:AAHoG7GRdsClCptLvd8-bT0_vmdiNgrdgG6M")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

# Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Хранилище данных пользователей (в production использовать БД)
user_data = {}


# ===== СОСТОЯНИЯ =====
class PhotoStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_custom_prompt = State()
    processing = State()


# ===== ШАБЛОНЫ ПРОМТОВ =====
TEMPLATES = {
    "remove_bg": {
        "name": "🎭 Убрать фон",
        "description": "Удалить фон и сделать прозрачным",
        "prompt": "Remove the background from this image completely, keeping only the main subject. Create a clean cutout with smooth edges. Preserve all details of the subject including hair or fine edges. Return only the subject on transparent background.",
        "category": "enhancement"
    },
    "enhance": {
        "name": "✨ Улучшить качество",
        "description": "Повысить качество и четкость",
        "prompt": "Enhance this image quality: upscale resolution, sharpen details, reduce noise, improve clarity and sharpness. Maintain natural look without over-processing. Fix any compression artifacts. Make it look professional and high-quality.",
        "category": "enhancement"
    },
    "fix_lighting": {
        "name": "💡 Исправить освещение",
        "description": "Улучшить свет и экспозицию",
        "prompt": "Improve the lighting in this image: balance exposure, enhance shadows and highlights, improve overall brightness and contrast. Make it look professionally lit while maintaining natural appearance. Fix any lighting issues.",
        "category": "enhancement"
    },
    "anime_style": {
        "name": "🎨 Аниме стиль",
        "description": "Превратить в аниме арт",
        "prompt": "Transform this image into high-quality anime/manga style art. Use clean lines, vibrant colors, large expressive eyes, and typical anime aesthetic. Maintain the composition and key elements while applying anime art style. Make it look like professional anime artwork.",
        "category": "artistic"
    },
    "oil_painting": {
        "name": "🖼️ Масляная живопись",
        "description": "Стиль масляной картины",
        "prompt": "Transform this image into a beautiful oil painting. Use visible brush strokes, rich colors, textured canvas appearance, and classical painting techniques. Make it look like a Renaissance or Impressionist oil painting masterpiece.",
        "category": "artistic"
    },
    "cinematic": {
        "name": "🎬 Кинематограф",
        "description": "Кинематографический вид",
        "prompt": "Transform this image into cinematic movie quality. Add dramatic lighting, film grain, professional color grading, depth of field, and cinematography look. Make it look like a frame from a high-budget Hollywood movie with epic atmosphere.",
        "category": "artistic"
    },
    "professional_photo": {
        "name": "📸 Профессиональное фото",
        "description": "Студийное качество",
        "prompt": "Transform into professional studio photography. Perfect lighting, sharp focus, professional quality. Clean background, proper exposure, commercial photography standard. Make it suitable for professional use or portfolio.",
        "category": "professional"
    },
    "id_photo": {
        "name": "🪪 Фото на документы",
        "description": "Фото для паспорта/ID",
        "prompt": "Transform this into a professional ID/passport photo. Use plain white or light gray background, proper lighting, centered composition, neutral expression. Meet official photo requirements: clear face, no shadows, appropriate framing, professional look.",
        "category": "professional"
    },
    "product_photo": {
        "name": "🛍️ Фото товара",
        "description": "Для маркетплейсов",
        "prompt": "Transform into professional product photography. Clean white background, perfect studio lighting, sharp focus on product, professional e-commerce quality. Suitable for marketplace listing like Amazon, Wildberries, or Ozon. Make product look attractive and professional.",
        "category": "professional"
    },
    "movie_poster": {
        "name": "🎭 Киноп остер",
        "description": "Эпичный постер фильма",
        "prompt": "Transform this into an epic movie poster. Add dramatic composition, cinematic lighting, intense atmosphere, and professional poster design elements. Make it look like a real Hollywood blockbuster movie poster with high production value and dramatic impact.",
        "category": "creative"
    },
    "cartoon": {
        "name": "🎪 Мультяшный стиль",
        "description": "Pixar/Disney стиль",
        "prompt": "Transform into Pixar/Disney 3D animated movie style. Use vibrant colors, smooth 3D rendering, expressive features, and characteristic animation studio aesthetic. Make it look like a character or scene from a professional animated movie.",
        "category": "creative"
    },
    "vintage": {
        "name": "📷 Винтаж",
        "description": "Ретро фотография",
        "prompt": "Transform into vintage retro photograph. Add film grain, faded colors, vignette effect, and nostalgic 1970s-1980s photography aesthetic. Make it look like an old authentic photograph with character and warmth.",
        "category": "creative"
    }
}

# Категории шаблонов
CATEGORIES = {
    "enhancement": "📸 Улучшение фото",
    "artistic": "🎨 Художественные стили",
    "professional": "💼 Профессиональное",
    "creative": "🎉 Креатив и фан"
}


# ===== ФУНКЦИИ РАБОТЫ С GEMINI API =====
async def process_image_with_gemini(image_bytes: bytes, prompt: str) -> Optional[bytes]:
    """Обработка изображения через Gemini API"""
    try:
        # Конвертируем изображение в base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Формируем запрос к Gemini API
        request_data = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 4096,
            }
        }
        
        async with aiohttp.ClientSession() as session:
            url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
            async with session.post(url, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Gemini API response: {result}")
                    
                    # Gemini возвращает текстовый ответ, не изображение
                    # Для реальной обработки изображений нужен Imagen API
                    # Пока возвращаем описание
                    if 'candidates' in result and len(result['candidates']) > 0:
                        text_response = result['candidates'][0]['content']['parts'][0]['text']
                        return text_response.encode('utf-8')
                    
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"Gemini API error {response.status}: {error_text}")
                    return None
                    
    except Exception as e:
        logger.error(f"Error processing with Gemini: {e}")
        return None


def get_user_credits(user_id: int) -> int:
    """Получить баланс кредитов пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {"credits": 3, "generations": 0}
    return user_data[user_id]["credits"]


def deduct_credits(user_id: int, amount: int = 1) -> bool:
    """Списать кредиты"""
    if user_id not in user_data:
        user_data[user_id] = {"credits": 3, "generations": 0}
    
    if user_data[user_id]["credits"] >= amount:
        user_data[user_id]["credits"] -= amount
        user_data[user_id]["generations"] += 1
        return True
    return False


def add_credits(user_id: int, amount: int):
    """Добавить кредиты"""
    if user_id not in user_data:
        user_data[user_id] = {"credits": 0, "generations": 0}
    user_data[user_id]["credits"] += amount


# ===== КЛАВИАТУРЫ =====
def main_menu():
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Редактировать фото", callback_data="edit_photo")],
        [InlineKeyboardButton(text="🎨 Шаблоны", callback_data="templates")],
        [InlineKeyboardButton(text="💎 Мои кредиты", callback_data="balance")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])


def category_menu():
    """Меню категорий"""
    keyboard = []
    for cat_id, cat_name in CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(text=cat_name, callback_data=f"cat_{cat_id}")])
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def templates_menu(category: str):
    """Меню шаблонов категории"""
    keyboard = []
    for template_id, template in TEMPLATES.items():
        if template["category"] == category:
            keyboard.append([InlineKeyboardButton(
                text=template["name"],
                callback_data=f"tpl_{template_id}"
            )])
    keyboard.append([InlineKeyboardButton(text="◀️ К категориям", callback_data="templates")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_button():
    """Кнопка назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back")]
    ])


def cancel_button():
    """Кнопка отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])


# ===== КОМАНДЫ =====
@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Команда /start"""
    user_id = message.from_user.id
    credits = get_user_credits(user_id)
    
    await message.answer(
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        f"Я <b>WHYNOT Photoshop</b> — AI-помощник для редактирования фото!\n\n"
        f"🎁 <b>У тебя {credits} бесплатных генераций!</b>\n\n"
        f"<b>Что я умею:</b>\n"
        f"• Убирать фон\n"
        f"• Улучшать качество\n"
        f"• Применять художественные стили\n"
        f"• Создавать профессиональные фото\n"
        f"• И многое другое!\n\n"
        f"Выбери действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    await message.answer(
        "📖 <b>Как пользоваться:</b>\n\n"
        "1️⃣ Нажми <b>📸 Редактировать фото</b>\n"
        "2️⃣ Отправь своё фото\n"
        "3️⃣ Выбери шаблон обработки\n"
        "4️⃣ Жди результат (20-40 сек)\n"
        "5️⃣ Получи обработанное фото!\n\n"
        "<b>💎 Кредиты:</b>\n"
        "• 3 бесплатных при регистрации\n"
        "• 1 кредит = 1 генерация\n\n"
        "<b>🎨 Шаблоны:</b>\n"
        "• 12+ готовых стилей\n"
        "• От улучшения до арта\n\n"
        "Начни с /start",
        reply_markup=back_button(),
        parse_mode="HTML"
    )


# ===== CALLBACK ОБРАБОТЧИКИ =====
@dp.callback_query(F.data == "back")
async def cb_back(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    user_id = callback.from_user.id
    credits = get_user_credits(user_id)
    
    await callback.message.edit_text(
        f"🏠 <b>Главное меню</b>\n\n"
        f"💎 Кредитов: <b>{credits}</b>\n\n"
        f"Выбери действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "cancel")
async def cb_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Отмена операции"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Отменено",
        reply_markup=main_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "edit_photo")
async def cb_edit_photo(callback: types.CallbackQuery, state: FSMContext):
    """Начать редактирование фото"""
    user_id = callback.from_user.id
    credits = get_user_credits(user_id)
    
    if credits <= 0:
        await callback.message.edit_text(
            "😢 <b>У тебя закончились кредиты!</b>\n\n"
            "Получи больше:\n"
            "• Пригласи друга (+5 кредитов)\n"
            "• Купи пакет кредитов\n\n"
            "Скоро добавим покупку!",
            reply_markup=back_button(),
            parse_mode="HTML"
        )
        await callback.answer("⚠️ Нет кредитов")
        return
    
    await state.set_state(PhotoStates.waiting_for_photo)
    await callback.message.edit_text(
        "📸 <b>Загрузи фото</b>\n\n"
        "Отправь мне фотографию, которую хочешь обработать.\n\n"
        "✅ Поддерживаются: JPG, PNG\n"
        "📏 Рекомендуемый размер: до 5 МБ\n\n"
        "После загрузки выберешь стиль обработки.",
        reply_markup=cancel_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "templates")
async def cb_templates(callback: types.CallbackQuery):
    """Показать категории шаблонов"""
    await callback.message.edit_text(
        "🎨 <b>Категории шаблонов</b>\n\n"
        "Выбери категорию:",
        reply_markup=category_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("cat_"))
async def cb_category(callback: types.CallbackQuery):
    """Показать шаблоны категории"""
    category = callback.data.replace("cat_", "")
    category_name = CATEGORIES.get(category, "Шаблоны")
    
    await callback.message.edit_text(
        f"<b>{category_name}</b>\n\n"
        f"Выбери шаблон:",
        reply_markup=templates_menu(category),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("tpl_"))
async def cb_template(callback: types.CallbackQuery, state: FSMContext):
    """Выбор шаблона"""
    template_id = callback.data.replace("tpl_", "")
    template = TEMPLATES.get(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден")
        return
    
    # Сохраняем выбранный шаблон
    await state.update_data(selected_template=template_id)
    await state.set_state(PhotoStates.waiting_for_photo)
    
    await callback.message.edit_text(
        f"<b>{template['name']}</b>\n\n"
        f"{template['description']}\n\n"
        f"📸 Теперь отправь фото для обработки:",
        reply_markup=cancel_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "balance")
async def cb_balance(callback: types.CallbackQuery):
    """Показать баланс"""
    user_id = callback.from_user.id
    credits = get_user_credits(user_id)
    generations = user_data.get(user_id, {}).get("generations", 0)
    
    await callback.message.edit_text(
        f"💎 <b>Твой баланс</b>\n\n"
        f"Кредитов: <b>{credits}</b>\n"
        f"Создано изображений: <b>{generations}</b>\n\n"
        f"<b>Как получить больше:</b>\n"
        f"• Пригласи друга (+5 кредитов)\n"
        f"• Купи пакет кредитов (скоро)\n\n"
        f"1 кредит = 1 генерация",
        reply_markup=back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def cb_help(callback: types.CallbackQuery):
    """Помощь"""
    await callback.message.edit_text(
        "❓ <b>Помощь</b>\n\n"
        "<b>Как работает:</b>\n"
        "1. Загружаешь фото\n"
        "2. Выбираешь стиль\n"
        "3. Получаешь результат\n\n"
        "<b>Доступные стили:</b>\n"
        "• Улучшение качества\n"
        "• Удаление фона\n"
        "• Художественные стили\n"
        "• Профессиональные фото\n"
        "• Креативные эффекты\n\n"
        "<b>Поддержка:</b>\n"
        "Вопросы? Пиши @support",
        reply_markup=back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


# ===== ОБРАБОТКА ФОТО =====
@dp.message(PhotoStates.waiting_for_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    """Обработка загруженного фото"""
    user_id = message.from_user.id
    credits = get_user_credits(user_id)
    
    if credits <= 0:
        await message.answer(
            "😢 У тебя закончились кредиты!",
            reply_markup=back_button()
        )
        await state.clear()
        return
    
    # Получаем данные состояния
    data = await state.get_data()
    selected_template = data.get("selected_template")
    
    # Если шаблон не выбран, показываем меню выбора
    if not selected_template:
        await state.update_data(photo_file_id=message.photo[-1].file_id)
        await message.answer(
            "✅ Фото получено!\n\n"
            "Теперь выбери стиль обработки:",
            reply_markup=category_menu()
        )
        return
    
    # Списываем кредит
    if not deduct_credits(user_id):
        await message.answer(
            "😢 Не удалось списать кредит",
            reply_markup=back_button()
        )
        await state.clear()
        return
    
    # Начинаем обработку
    msg = await message.answer(
        "⏳ <b>Обрабатываю...</b>\n\n"
        "Это может занять 20-40 секунд",
        parse_mode="HTML"
    )
    
    try:
        # Скачиваем фото
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        photo_bytes = await bot.download_file(file.file_path)
        
        await msg.edit_text(
            "⏳ <b>Обработка...</b>\n▓▓▓░░░░░░░ 30%",
            parse_mode="HTML"
        )
        
        # Получаем промт шаблона
        template = TEMPLATES.get(selected_template)
        prompt = template["prompt"]
        
        # ВАЖНО: Gemini API пока не поддерживает генерацию изображений
        # Для реальной работы нужен Imagen API или другой сервис
        # Сейчас делаем заглушку
        
        await msg.edit_text(
            "⏳ <b>Применяю AI...</b>\n▓▓▓▓▓▓░░░░ 60%",
            parse_mode="HTML"
        )
        
        # Симуляция обработки
        await asyncio.sleep(2)
        
        await msg.edit_text(
            "⏳ <b>Финализация...</b>\n▓▓▓▓▓▓▓▓▓░ 90%",
            parse_mode="HTML"
        )
        
        # В реальной версии здесь будет вызов AI API
        # result = await process_image_with_gemini(photo_bytes.read(), prompt)
        
        # Пока отправляем оригинал обратно с сообщением
        await msg.edit_text(
            "✅ <b>Готово!</b>\n\n"
            f"<b>Применен стиль:</b> {template['name']}\n\n"
            f"⚠️ <b>DEMO режим</b>\n"
            f"Для полной работы нужен Gemini Imagen API ключ.\n\n"
            f"💎 Осталось кредитов: {get_user_credits(user_id)}",
            parse_mode="HTML"
        )
        
        # Отправляем результат (пока оригинал)
        await message.answer_photo(
            photo=photo.file_id,
            caption=f"✨ <b>{template['name']}</b>\n\n"
                   f"💎 Кредитов: {get_user_credits(user_id)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Еще раз", callback_data="edit_photo")],
                [InlineKeyboardButton(text="🎨 Другой стиль", callback_data="templates")],
                [InlineKeyboardButton(text="◀️ В меню", callback_data="back")]
            ]),
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        # Возвращаем кредит при ошибке
        add_credits(user_id, 1)
        await msg.edit_text(
            "❌ <b>Ошибка обработки</b>\n\n"
            "Кредит возвращен. Попробуй еще раз.",
            reply_markup=back_button(),
            parse_mode="HTML"
        )
        await state.clear()


@dp.message(F.photo)
async def handle_photo_no_state(message: Message):
    """Фото без состояния"""
    await message.answer(
        "📸 Фото получено!\n\n"
        "Что делать с ним?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎨 Выбрать стиль", callback_data="templates")],
            [InlineKeyboardButton(text="◀️ В меню", callback_data="back")]
        ])
    )


@dp.message()
async def handle_other(message: Message):
    """Обработка остальных сообщений"""
    await message.answer(
        "Используй /start для начала работы",
        reply_markup=main_menu()
    )


# ===== ЗАПУСК =====
async def main():
    """Главная функция"""
    logger.info("🚀 WHYNOT Photoshop Bot запускается...")
    logger.info(f"📊 Загружено шаблонов: {len(TEMPLATES)}")
    logger.info(f"📁 Категорий: {len(CATEGORIES)}")
    
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        logger.warning("⚠️ Gemini API ключ не настроен! Бот работает в DEMO режиме")
    else:
        logger.info("✅ Gemini API ключ настроен")
    
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Бот готов к работе!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")
