import html
from random import seed

from telegram.ext import ConversationHandler

from data import *


class TestModule(BaseModule):
    @staticmethod
    async def select(update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        if int(query.data) < 0:
            return await start(update, context)

        test = tests[int(query.data)]
        context.user_data['options'] = test[2]
        context.user_data['sample'] = test[1] \
            .sample(frac=1, random_state=seed()) \
            .reset_index(drop=True)

        await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                       text='✏ Поехали!\n'
                                            f'Ты выбрал тренажёр *{test[0]}*, который состоит из {len(test[1])} слов')

        return await TestModule.play(update, context, first=True)

    @staticmethod
    async def play(update: Update, context: CallbackContext, first=False):
        query = update.callback_query
        if first:
            context.user_data['index'] = 0
            context.user_data['incorrect'] = 0
        else:
            reply = int(query.data) == 0
            task = context.user_data['sample'].loc[context.user_data['index']]
            context.user_data['index'] += 1
            left = len(context.user_data['sample']) - context.user_data['index']

            if task['together'] == reply:
                text = "✅ Верно!"
            else:
                text = "❌ Неверно!"
                context.user_data['incorrect'] += 1

            await context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='HTML',
                                           text=f"{text}\nПравильный ответ: <b>{task['correct']}</b>\n\n"
                                                f"{html.escape(task['explanation'])}\n"
                                                f"(<a href='https://rus-ege.sdamgia.ru/problem?id={task['id']}'>"
                                                f"Источник"
                                                f"</a>)\n\n" +
                                                (f"Осталось {left} слов.\n"
                                                 f"Если хочешь закончить, то напиши /stop" if left > 0 else ''))

        await query.answer()

        if context.user_data['index'] >= len(context.user_data['sample']):
            return await TestModule.stop(update, context, True)

        task = context.user_data['sample'].loc[context.user_data['index']]

        keyboard = [list(InlineKeyboardButton(option, callback_data=i)
                         for i, option in enumerate(context.user_data['options']))]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f'❓Выбери правильный вариант написания:\n\n{task["question"]}',
                                       reply_markup=reply_markup)
        return PLAYING_TEST

    @staticmethod
    async def stop(update: Update, context: CallbackContext, out_of_words=False):
        correct_words = context.user_data['index'] - context.user_data['incorrect']
        if context.user_data['index'] < 1:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="🤓 Хорошо, выбери что-нибудь другое.")
            return await start(update, context)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=(
                                                    "🥳 Ура, слова закончились!" if out_of_words
                                                    else "👌 Хорошо, заканчиваем.") +
                                                f"\nРезультат: {correct_words}/{context.user_data['index']} "
                                                f"({round(correct_words / context.user_data['index'] * 100)}%)\n"
                                                f"Если хочешь начать заново, то напиши /start\n")
        return ConversationHandler.END
