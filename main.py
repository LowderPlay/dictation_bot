import os
import uuid
from random import seed

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackContext, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
import logging
from telegram.ext import CommandHandler
from gtts import gTTS
import pandas as pd


dictionary = pd.read_excel('dict.xls', 0, header=None).transpose().stack().reset_index(drop=True)
dicts = [
    ('Словарь (1-3)', dictionary[:3*64].reset_index(drop=True)),
    ('Словарь (4-6)', dictionary[3*64:].reset_index(drop=True)),
    ('56 наречий', pd.read_excel('adverbs.xls', 0, header=None).stack()),
    ('Н и НН', pd.read_excel('nn.xls', 0, header=None).stack()),
    ('При/Пре', pd.read_excel('pri_pre.xls', 0, header=None).stack()),
]

updater = Updater(token=os.environ['TOKEN'], use_context=True)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
dispatcher = updater.dispatcher

PLAYING, SELECT, GAME_OVER = range(3)


def start(update: Update, context: CallbackContext):
    context.user_data.clear()
    keyboard = list(InlineKeyboardButton(dict_[0], callback_data=i) for i, dict_ in enumerate(dicts))
    keys_in_row = 2
    reply_markup = InlineKeyboardMarkup([keyboard[i:i + keys_in_row] for i in range(0, len(keyboard), keys_in_row)])
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Привет! ✌\nЯ буду присылать голосовые, а ты будешь правильно писать слова.\n'
                                  'Выбери набор слов, который хочешь проверить',
                             reply_markup=reply_markup)
    return SELECT


def show(update: Update, context: CallbackContext):
    if len(context.user_data['incorrect']) < 1:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='🤩 Поздравляю! У тебя нет ошибок!')
    else:
        mistakes = []
        for correct, incorrect in context.user_data['incorrect']:
            mistakes.append((correct.replace("-", "\\-"), incorrect.replace("-", "\\-")))
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='MarkdownV2',
                                 text='Твои ошибки:\n'
                                      + ',\n'.join(f'*{correct}* \(~{incorrect}~\)' for correct, incorrect in mistakes))
    return ConversationHandler.END


def fix(update: Update, context: CallbackContext):
    if len(context.user_data['incorrect']) < 1:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='🤩 Поздравляю! У тебя нет ошибок!')
        return ConversationHandler.END
    incorrect = context.user_data['incorrect']
    context.user_data.clear()
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='✏ Поехали!\n'
                                  f'Ты решил сделать работу над ошибками ({len(incorrect)} слов)')
    context.user_data['sample'] = list(x[0] for x in incorrect)
    play(update, context)
    return PLAYING


def play(update: Update, context: CallbackContext):
    if 'last_word' in context.user_data:
        context.user_data['word'] += 1
        correct = context.user_data['last_word'].strip().lower()
        user_input = update.message.text.strip().lower()
        if correct.replace('ё', 'е') != user_input.replace('ё', 'е'):
            text = "❌ Неверно!"
            context.user_data['incorrect'].append((correct, user_input))
        else:
            text = "✅ Верно!"
        left = len(context.user_data['sample']) - context.user_data['word']
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                 text=f"{text}\nПравильный ответ: *{context.user_data['last_word'].lower()}*\n" +
                                      (f"Осталось {left} слов.\n"
                                       f"Если хочешь закончить, то напиши /stop" if left > 0 else ''))
    else:
        context.user_data['word'] = 0
        context.user_data['incorrect'] = []

    if context.user_data['word'] >= len(context.user_data['sample']):
        return stop(update, context, True)
    context.user_data['last_word'] = context.user_data['sample'][context.user_data['word']]
    send_word(context.bot, update.effective_chat.id, context.user_data['last_word'])
    return PLAYING


def send_word(bot, chat_id, word):
    tts = gTTS(word, lang='ru')
    name = str(uuid.uuid4())
    tts.save(name)
    bot.send_voice(chat_id=chat_id, voice=open(name, 'rb'))
    os.remove(name)


def stop(update: Update, context: CallbackContext, win=False):
    correct_words = context.user_data['word'] - len(context.user_data['incorrect'])
    if context.user_data['word'] < 1:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="🤓 Хорошо, выбери что-нибудь другое.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=("🥳 Ура, слова закончились!" if win else "👌 Хорошо, заканчиваем.") +
                                      f"\nРезультат: {correct_words}/{context.user_data['word']} "
                                      f"({round(correct_words / context.user_data['word'] * 100)}%)\n"
                                      f"Если хочешь начать заново, то напиши /start\n"
                                      f"Чтобы сделать работу над ошибками, напиши /fix, "
                                      f"а чтобы просто узнать где ты ошибся, напиши /show")
    return GAME_OVER


def select(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    dict_ = dicts[int(query.data)]
    context.user_data['sample'] = dict_[1]\
        .sample(frac=1, random_state=seed()) \
        .reset_index(drop=True)

    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                             text='✏ Поехали!\n'
                                  f'Ты выбрал словарь *{dict_[0]}*, который состоит из {len(dict_[1])} слов')
    play(update, context)
    return PLAYING


restart = MessageHandler(filters=(~Filters.command | Filters.regex('/start')), callback=start)
conv_handler = ConversationHandler(
    entry_points=[restart],
    states={
        PLAYING: [MessageHandler(filters=~Filters.command, callback=play)],
        SELECT: [CallbackQueryHandler(select)],
        GAME_OVER: [CommandHandler('fix', fix), CommandHandler('show', show), restart]
    },
    fallbacks=[CommandHandler('stop', stop)]
)

dispatcher.add_handler(conv_handler)

updater.start_polling()
updater.idle()
