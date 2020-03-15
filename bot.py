import os
from pathlib import Path
from dotenv import load_dotenv
import logging

from aiogram import Bot, Dispatcher, executor, types


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

API_TOKEN = os.getenv('TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
