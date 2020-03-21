import os
from pathlib import Path
from dotenv import load_dotenv
import logging
import re

import asyncio

from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.message import ContentType
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from chat_dispatcher import ChatDispatcher
from messages import MESSAGES
from forex import instruments
from data import get_traders, add_new_trade


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

API_TOKEN = os.getenv('TOKEN')
TRADERS = get_traders()

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# States
class BotStates(StatesGroup):
    open = State()  # Will be represented in storage as 'BotState:open'


async def send_message(user_id: int, text: str, disable_notification: bool = False) -> bool:
    """
    Safe messages sender

    :param user_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        await bot.send_message(user_id, text, disable_notification=disable_notification)
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    else:
        log.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def broadcast(text: str):
    for trader in TRADERS:
        await send_message(trader['telegram'], text)
        await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    user = message.from_user.full_name
    id = message.from_user.id
    log.info(f'user {user}, id {id}')
    await message.reply(MESSAGES['start'].format(user=user), parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply(MESSAGES['help'])


async def open_chat(get_message, cancel_state):
    try:        
        symbol = await get_message()
        log.info(f'symbol: {symbol.text}')

        if symbol.text.upper() not in instruments:
            await symbol.answer('Мне неизвестен такой инструмент! Повторите ввод.')
            await cancel_state()
            return
    
    
        inline_btn_direction_sell = InlineKeyboardButton('SELL', callback_data='btn_SELL')
        inline_btn_direction_buy = InlineKeyboardButton('BUY', callback_data='btn_BUY')
        inline_kb_direction = InlineKeyboardMarkup().add(inline_btn_direction_buy, inline_btn_direction_sell)

        await symbol.reply('Направление открытия?', reply_markup=inline_kb_direction)
        direction = await get_message()
        
        await symbol.reply(MESSAGES['open_volume'], parse_mode=ParseMode.MARKDOWN)
        volume = await get_message()

        try:
            float(volume.text)
        except ValueError:
            await volume.answer('Это не число, начните сначала!')
            await cancel_state()
            return

        log.info(f'volume: {volume.text}')
        await volume.answer(MESSAGES['received'])
        await cancel_state()

        user = volume.from_user.full_name
        telegram = volume.from_user.id

        direction_text = 'длинную' if direction.data == 'btn_BUY' else 'короткую'
        direction_key = 'sell' if direction.data == 'btn_BUY' else 'buy'
        add_new_trade(telegram=telegram, symbol=symbol.text.upper(), direction=direction_key, volume=float(volume.text))
        # await broadcast(MESSAGES['open_info'].format(user=user, symbol=symbol.text.upper(), direction=direction_text, volume=str(float(volume.text))))

    except ChatDispatcher.Timeout as te:
        await te.last_message.answer(MESSAGES['timeout'])


open_chat_dispatcher = ChatDispatcher(chatcb=open_chat,
                                 inactive_timeout=20)


@dp.message_handler(commands=['open'])
async def process_open_command(message: types.Message):
    await message.reply(MESSAGES['open_symbol'], parse_mode=ParseMode.MARKDOWN)
    await BotStates.open.set()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('btn'), state=BotStates.open)
async def process_callback_btn(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    # await bot.send_message(callback_query.from_user.id, 'Нажата первая кнопка!')
    await open_chat_dispatcher.handle(callback_query, state)

@dp.message_handler(state=BotStates.open)
async def message_handle(message: types.Message, state: FSMContext):
    await open_chat_dispatcher.handle(message, state)

@dp.message_handler(content_types=ContentType.ANY)
async def unknown_message(message: types.Message):
    await message.reply(MESSAGES['unknown'], parse_mode=ParseMode.MARKDOWN)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_shutdown=shutdown)