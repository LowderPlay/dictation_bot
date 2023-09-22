import abc

import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

PLAYING, SELECT_DICTIONARY, GAME_OVER, SELECT_MODE, SELECT_TEST, PLAYING_TEST = range(6)

dictionary = pd.read_excel('dictionaries/dict.xls', 0, header=None).transpose().stack().reset_index(drop=True)
dicts = [
    ('Словарь (1-3)', dictionary[:3 * 64].reset_index(drop=True)),
    ('Словарь (4-6)', dictionary[3 * 64:].reset_index(drop=True)),
    ('56 наречий', pd.read_excel('dictionaries/adverbs.xls', 0, header=None).stack()),
    ('Н и НН', pd.read_excel('dictionaries/nn.xls', 0, header=None).stack()),
    ('При/Пре', pd.read_excel('dictionaries/pri_pre.xls', 0, header=None).stack()),
]
tests = [
    ('НЕ и НИ', pd.read_excel('tests/ne-ni.xls', 0), ('слитно', 'раздельно'))
]


class BaseModule(metaclass=abc.ABCMeta):
    @staticmethod
    @abc.abstractmethod
    async def select(update: Update, context: CallbackContext):
        pass

    @staticmethod
    @abc.abstractmethod
    async def play(update: Update, context: CallbackContext):
        pass

    @staticmethod
    @abc.abstractmethod
    async def stop(update: Update, context: CallbackContext, out_of_words=False):
        pass


async def start(update: Update, context: CallbackContext):
    context.user_data.clear()
    keyboard = list(InlineKeyboardButton(label, callback_data=i) for i, label in enumerate(["Диктанты", "Тренажёры"]))
    reply_markup = InlineKeyboardMarkup([keyboard])
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='Привет! ✌\n'
                                        'Ты можешь провести диктант или проверить знание правил с помощью тренажёров.\n'
                                        'Выбери режим, который тебе нужен',
                                   reply_markup=reply_markup)
    return SELECT_MODE