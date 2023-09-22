import os
import uuid
from random import seed

from gtts import gTTS
from telegram.ext import ConversationHandler

from data import *


class DictionaryModule(BaseModule):
    @staticmethod
    async def play(update: Update, context: CallbackContext):
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
            await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                           text=f"{text}\nПравильный ответ: *{context.user_data['last_word'].lower()}*\n" +
                                                (f"Осталось {left} слов.\n"
                                                 f"Если хочешь закончить, то напиши /stop" if left > 0 else ''))
        else:
            context.user_data['word'] = 0
            context.user_data['incorrect'] = []

        if context.user_data['word'] >= len(context.user_data['sample']):
            return await DictionaryModule.stop(update, context, True)
        context.user_data['last_word'] = context.user_data['sample'][context.user_data['word']]
        await DictionaryModule.send_word(context.bot, update.effective_chat.id, context.user_data['last_word'])
        return PLAYING

    @staticmethod
    async def send_word(bot, chat_id, word):
        tts = gTTS(word, lang='ru')
        name = str(uuid.uuid4())
        tts.save(name)
        await bot.send_voice(chat_id=chat_id, voice=open(name, 'rb'))
        os.remove(name)

    @staticmethod
    async def select(update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        if int(query.data) < 0:
            return await start(update, context)

        dict_ = dicts[int(query.data)]
        context.user_data['sample'] = dict_[1] \
            .sample(frac=1, random_state=seed()) \
            .reset_index(drop=True)

        await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                       text='✏ Поехали!\n'
                                            f'Ты выбрал словарь *{dict_[0]}*, который состоит из {len(dict_[1])} слов')

        return await DictionaryModule.play(update, context)

    @staticmethod
    async def stop(update: Update, context: CallbackContext, out_of_words=False):
        correct_words = context.user_data['word'] - len(context.user_data['incorrect'])
        if context.user_data['word'] < 1:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="🤓 Хорошо, выбери что-нибудь другое.")
            return await start(update, context)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=("🥳 Ура, слова закончились!" if out_of_words
                                                 else "👌 Хорошо, заканчиваем.") +
                                                f"\nРезультат: {correct_words}/{context.user_data['word']} "
                                                f"({round(correct_words / context.user_data['word'] * 100)}%)\n"
                                                f"Если хочешь начать заново, то напиши /start\n"
                                                f"Чтобы сделать работу над ошибками, напиши /fix\n"
                                                f"А чтобы просто узнать где ты ошибся, напиши /show")
        return GAME_OVER

    @staticmethod
    async def show(update: Update, context: CallbackContext):
        if len(context.user_data['incorrect']) < 1:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='🤩 Поздравляю! У тебя нет ошибок!')
        else:
            mistakes = []
            for correct, incorrect in context.user_data['incorrect']:
                mistakes.append((correct.replace("-", "\\-"), incorrect.replace("-", "\\-")))
            await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='MarkdownV2',
                                           text='Твои ошибки:\n'
                                                + ',\n'.join(
                                               f'*{correct}* \(~{incorrect}~\)' for correct, incorrect in mistakes))
        return ConversationHandler.END

    @staticmethod
    async def fix(update: Update, context: CallbackContext):
        if len(context.user_data['incorrect']) < 1:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='🤩 Поздравляю! У тебя нет ошибок!')
            return ConversationHandler.END
        incorrect = context.user_data['incorrect']
        context.user_data.clear()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='✏ Поехали!\n'
                                            f'Ты решил сделать работу над ошибками ({len(incorrect)} слов)')
        context.user_data['sample'] = list(x[0] for x in incorrect)
        return await DictionaryModule.play(update, context)
