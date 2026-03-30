import json
import os
import random
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
WORDS_FILE = "words.json"
if not os.path.exists(WORDS_FILE):
    with open(WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

TOKEN = "8673774767:AAE0uRYCYr8-_Rb7-P2asgmYRAu2homCppg"
bot = Bot(token=TOKEN)
dp = Dispatcher()

users_state = {}
user_test = {}
bot_messages = {}


def load_words():
    if not os.path.exists(WORDS_FILE):
        return {}
    try:
        with open(WORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {}


user_words = load_words()


def save_words(words):
    with open(WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)


def get_test_word(user_id):
    user_dict = user_words.get(user_id, {})
    if not user_dict:
        return {}
    all_user_word_list = list(user_dict.items())
    if len(all_user_word_list) > 10:
        select_words = random.sample(all_user_word_list, 10)
    else:
        select_words = all_user_word_list
    return dict(select_words)


def format_words_display(words_dict):
    result = []
    for word, translation in words_dict.items():
        result.append(f"{word} - {translation}")
    return "\n".join(result)


async def save_bot_message(message, user_id):
    if user_id not in bot_messages:
        bot_messages[user_id] = []
    bot_messages[user_id].append(message.message_id)


async def delete_all_bot_messages(chat_id, user_id):
    if user_id not in bot_messages:
        return
    for msg_id in bot_messages[user_id]:
        try:
            await bot.delete_message(chat_id, msg_id)
        except:
            pass
    bot_messages[user_id] = []


async def ask_question(chat_id, user_id):
    test_data = user_test.get(user_id)
    if not test_data or test_data.get("mode") != "testing":
        return

    questions = test_data["questions"]
    current_index = test_data["current_index"]

    if current_index >= len(questions):
        if test_data["mistakes"]:
            test_data["questions"] = test_data["mistakes"].copy()
            test_data["current_index"] = 0
            test_data["mistakes"] = []
            await ask_question(chat_id, user_id)
            return
        else:
            await finish_test(chat_id, user_id)
            return

    word = questions[current_index]
    translation = test_data["words"][word]
    test_data["current_word"] = word

    rdm = random.randint(0, 1)
    test_data["question_type"] = "eng_to_rus" if rdm == 0 else "rus_to_eng"

    btn_exit = InlineKeyboardButton(text="Всё, я заебался", callback_data="main_menu")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_exit]])

    if rdm == 0:
        msg = await bot.send_message(chat_id, f"Как переводится {word}?", reply_markup=keyboard)
    else:
        msg = await bot.send_message(chat_id, f"Как будет по-английски {translation}?", reply_markup=keyboard)

    await save_bot_message(msg, user_id)


async def finish_test(chat_id, user_id):
    test_data = user_test.get(user_id)
    if not test_data:
        return

    mistakes_count = len(test_data.get("mistakes_history", []))

    btn_menu = InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_menu]])

    msg = await bot.send_message(
        chat_id,
        f"Тест окончен!\n\nКоличество ошибок: {mistakes_count}",
        reply_markup=keyboard
    )
    await save_bot_message(msg, user_id)

    if user_id in user_test:
        del user_test[user_id]


@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    await delete_all_bot_messages(chat_id, user_id)

    btn_add = InlineKeyboardButton(text="➕ Добавить слово", callback_data="add")
    btn_list = InlineKeyboardButton(text="📖 Мои слова", callback_data="list")
    btn_test = InlineKeyboardButton(text="🎯 Тест", callback_data="test")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [btn_add],
        [btn_list],
        [btn_test]
    ])

    msg = await message.answer("Здоров, будем учить английский ёпта", reply_markup=keyboard)
    await save_bot_message(msg, user_id)


@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    global user_words
    user_id = str(callback.from_user.id)
    chat_id = callback.message.chat.id
    action = callback.data

    try:
        await callback.message.delete()
    except:
        pass

    user_words = load_words()
    count_word = len(user_words.get(user_id, {}))

    if action == "add":
        users_state[user_id] = "adding"
        btn_menu = InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_menu]])
        msg = await callback.message.answer(
            f'В твоём словаре {count_word} слов.\n\nПиши слово и перевод через пробел.\nМожно добавить несколько слов, каждое с новой строки:\napple яблоко\ncat кот\ndog собака',
            reply_markup=keyboard)
        await save_bot_message(msg, user_id)
        await callback.answer()

    elif action == "list":
        btn_menu = InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_menu]])
        if user_id in user_words and user_words[user_id]:
            text = "📖 Твои слова:\n\n"
            for word, trans in user_words[user_id].items():
                text += f"{word} - {trans}\n"
            msg = await callback.message.answer(text, reply_markup=keyboard)
        else:
            msg = await callback.message.answer("📭 У тебя пока нет слов", reply_markup=keyboard)
        await save_bot_message(msg, user_id)
        await callback.answer()

    elif action == "test":
        btn_menu = InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_menu]])
        if user_id not in user_words or not user_words[user_id]:
            msg = await callback.message.answer("📭 У тебя пока нет слов", reply_markup=keyboard)
            await save_bot_message(msg, user_id)
            await callback.answer()
            return

        test_words = get_test_word(user_id)
        words_text = format_words_display(test_words)

        user_test[user_id] = {
            "words": test_words
        }

        btn_start = InlineKeyboardButton(text="Погнали", callback_data="start_test")
        btn_menu = InlineKeyboardButton(text="Я заебался", callback_data="main_menu")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_start], [btn_menu]])

        msg = await callback.message.answer(
            f"Запоминай слова: \n\n{words_text}",
            reply_markup=keyboard
        )
        await save_bot_message(msg, user_id)
        await callback.answer()

    elif action == "start_test":
        if user_id not in user_test:
            msg = await callback.message.answer("Сначала нажми «Тест»")
            await save_bot_message(msg, user_id)
            await callback.answer()
            return

        test_words = user_test[user_id]["words"]
        if not test_words:
            msg = await callback.message.answer("У тебя нет слов для теста")
            await save_bot_message(msg, user_id)
            await callback.answer()
            return

        questions = list(test_words.keys())
        random.shuffle(questions)
        user_test[user_id] = {
            "mode": "testing",
            "words": test_words,
            "questions": questions,
            "current_index": 0,
            "current_word": None,
            "question_type": None,
            "mistakes": [],
            "mistakes_history": []
        }

        await delete_all_bot_messages(chat_id, user_id)
        await ask_question(chat_id, user_id)
        await callback.answer()

    elif action == "main_menu":
        users_state[user_id] = None
        if user_id in user_test:
            del user_test[user_id]

        await delete_all_bot_messages(chat_id, user_id)

        btn_add = InlineKeyboardButton(text="➕ Добавить слово", callback_data="add")
        btn_list = InlineKeyboardButton(text="📖 Мои слова", callback_data="list")
        btn_test = InlineKeyboardButton(text="🎯 Тест", callback_data="test")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn_add], [btn_list], [btn_test]])

        msg = await callback.message.answer("Инглиш ёпта", reply_markup=keyboard)
        await save_bot_message(msg, user_id)
        await callback.answer()


@dp.message()
async def handle_message(message: types.Message):
    global user_words
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    text = message.text.strip()

    if users_state.get(user_id) == "adding":
        lines = text.split('\n')
        added_words = []
        errors = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) != 2:
                errors.append(f"❌ {line} - нужно слово и перевод через пробел")
                continue

            word = parts[0].lower()
            translation = parts[1].lower()

            if user_id not in user_words:
                user_words[user_id] = {}

            if word in user_words[user_id]:
                errors.append(f"⚠️ {word} - уже есть в словаре, нахуй ты его пишешь")
            else:
                user_words[user_id][word] = translation
                added_words.append(f"{word} - {translation}")

        if added_words:
            save_words(user_words)

        result_text = ""
        if added_words:
            result_text += f"✅ Добавлено:\n" + "\n".join(added_words) + "\n\n"
        if errors:
            result_text += "\n".join(errors)

        if not added_words and not errors:
            result_text = "❌ Ничего не добавлено"

        menu_button = InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[menu_button]])
        msg = await message.answer(result_text, reply_markup=keyboard)
        await save_bot_message(msg, user_id)
        users_state[user_id] = None
        return

    if user_id in user_test and user_test[user_id].get("mode") == "testing":
        test_data = user_test[user_id]
        current_word = test_data.get("current_word")

        if not current_word:
            return

        current_translation = test_data["words"][current_word].lower()
        question_type = test_data.get("question_type")

        try:
            await message.delete()
        except:
            pass

        is_correct = False
        if question_type == "eng_to_rus":
            if text.lower() == current_translation:
                is_correct = True
        else:
            if text.lower() == current_word:
                is_correct = True

        if is_correct:
            msg = await bot.send_message(chat_id, "✅ Правильно!")
            await save_bot_message(msg, user_id)
            test_data["current_index"] += 1
            await ask_question(chat_id, user_id)
        else:
            msg = await bot.send_message(chat_id, f"❌ Неправильно!\n{current_word} - {current_translation}")
            await save_bot_message(msg, user_id)
            test_data["mistakes"].append(current_word)
            if "mistakes_history" not in test_data:
                test_data["mistakes_history"] = []
            test_data["mistakes_history"].append(current_word)
            test_data["current_index"] += 1
            await ask_question(chat_id, user_id)
        return

    msg = await message.answer("Используй кнопки меню")
    await save_bot_message(msg, user_id)


import atexit

atexit.register(lambda: save_words(user_words))


async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
