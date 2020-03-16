from aiogram.utils.markdown import text, bold, italic, code, pre
from aiogram.utils.emoji import emojize


start_message = text('Привет', bold('БабкаНаЛавке'), 'приветствует тебя, {user}!\nЖду твоей команды!')
help_message = 'Я помогу тебе торговать и придерживаться дисциплины.'
unknown_message = text(emojize('Я не знаю, что с этим делать :astonished:'),
                      italic('\nЯ просто напомню,'), 'что есть',
                      code('команда'), '/help')
timeout_message = 'Что-то Вы долго молчите, пойду посплю'
information_received_message = 'Информация получена. Спасибо'

open_position_message_symbol = text('По какому', bold('инструменту'), 'открыта сделка?\nУкажите название инструмента без символа "/".')
open_position_message_volume = text('Какой', bold('объем?'))
open_position_message_info = '{user} открыл {direction} позицию по {symbol}, объем {volume}.'

MESSAGES = {
    'start': start_message,
    'help': help_message,
    'unknown': unknown_message,
    'open_symbol': open_position_message_symbol,
    'open_volume': open_position_message_volume,
    'open_info': open_position_message_info,
    'timeout': timeout_message,
    'received': information_received_message,
}