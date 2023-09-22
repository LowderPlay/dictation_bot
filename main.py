import logging
import os

from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, filters, ConversationHandler, CallbackQueryHandler, \
    ApplicationBuilder

from data import *
from dictionaries import DictionaryModule
from tests import TestModule

app = ApplicationBuilder().token(os.environ['TOKEN']).build()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def create_keyboard(keys_in_row, options, back=False):
    keyboard = list(InlineKeyboardButton(dict_[0], callback_data=i) for i, dict_ in enumerate(options))
    return InlineKeyboardMarkup(([[InlineKeyboardButton('⬅ Назад', callback_data=-1)]] if back else []) +
                                [keyboard[i:i + keys_in_row] for i in range(0, len(keyboard), keys_in_row)])


async def select_mode(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if int(query.data) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='🎤 Я буду присылать голосовые, а ты будешь правильно писать слова.\n'
                                            'Выбери набор слов, который хочешь проверить',
                                       reply_markup=create_keyboard(2, dicts, back=True))
        return SELECT_DICTIONARY
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='✍ Я буду присылать предложения, '
                                            'а ты будешь выбирать правильный вариант написания.\n'
                                            'Выбери тренажёр, который хочешь использовать',
                                       reply_markup=create_keyboard(2, tests, back=True))
        return SELECT_TEST


async def start_query(update: Update, context: CallbackContext):
    await update.callback_query.answer("Бот был перезапущен, придётся начать сначала :(")
    return await start(update, context)


restart = MessageHandler(filters=(~filters.COMMAND | filters.Regex('/start')), callback=start)
conv_handler = ConversationHandler(
    entry_points=[restart, CallbackQueryHandler(callback=start_query)],
    states={
        SELECT_MODE: [CallbackQueryHandler(select_mode)],

        SELECT_DICTIONARY: [CallbackQueryHandler(DictionaryModule.select)],
        PLAYING: [
            MessageHandler(filters=~filters.COMMAND, callback=DictionaryModule.play),
            CommandHandler('stop', DictionaryModule.stop)
        ],
        GAME_OVER: [
            CommandHandler('fix', DictionaryModule.fix),
            CommandHandler('show', DictionaryModule.show),
            restart
        ],

        SELECT_TEST: [CallbackQueryHandler(TestModule.select)],
        PLAYING_TEST: [CallbackQueryHandler(TestModule.play), CommandHandler('stop', TestModule.stop)],
    },
    fallbacks=[]
)

app.add_handler(conv_handler)

app.run_polling()
