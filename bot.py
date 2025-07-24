import asyncio
import logging
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN
from utils.text_processor import split_text_to_lines, validate_text_length
from utils.psd_processor import processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Отправь мне текст, и я создам превью.\n"
        "Максимум 6 слов (по 2 слова на строку, 3 строки).\n\n"
        "⚠️ Требуется установленный Adobe Photoshop!"
    )

@dp.message(F.text)
async def process_text(message: Message):
    text = message.text.strip()
    
    if not text:
        await message.answer("Отправь непустой текст!")
        return
    
    if not validate_text_length(text):
        await message.answer("Слишком длинный текст! Максимум 6 слов.")
        return
    
    try:
        await message.answer("Создаю превью в Photoshop...")
        
        text_lines = split_text_to_lines(text)
        
        if not processor.doc:
            processor.load_psd()
        
        image_bytes = processor.create_preview(text_lines)
        
        input_file = BufferedInputFile(
            image_bytes,
            filename="preview.png"
        )
        
        await message.answer_photo(input_file)
        
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        if "Photoshop" in str(e):
            await message.answer(
                "❌ Ошибка подключения к Photoshop!\n"
                "Убедись что Adobe Photoshop установлен и запущен."
            )
        else:
            await message.answer("Произошла ошибка при создании превью. Попробуй ещё раз.")

async def main():
    try:
        logger.info("Loading PSD file in Photoshop...")
        processor.load_psd()
        logger.info("PSD loaded successfully")
        
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
    finally:
        processor.close()

if __name__ == "__main__":
    asyncio.run(main()) 