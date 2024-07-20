from  database import pool, execute_update_query, execute_select_query
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import types
from database import pool
import json

quiz_data = []
def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()
    
    print("Generating keyboard for options:", answer_options)  # Отладочное сообщение

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    builder.adjust(1)
    return builder.as_markup()

def get_quiz_data():
    return quiz_data


async def new_quiz(message):
    global quiz_data
    quiz_data = await get_all_quiz_questions(pool)
    print("Quiz data at new_quiz:", quiz_data, len(quiz_data))  # Отладочное сообщение
    user_id = message.from_user.id
    current_question_index = 0
    score = 0
    await update_quiz_index_and_score(user_id, current_question_index, score)
    await get_question(message, user_id)


async def get_question(message, user_id):
    current_question_index = await get_quiz_index(user_id)
    print("Current question index:", current_question_index)  # Отладочное сообщение
    print("Quiz data at get_question:", quiz_data)  # Отладочное сообщение
        
    question_data = quiz_data[current_question_index]
    correct_index = question_data['correct_option']
    opts = question_data['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{question_data['question']}", reply_markup=kb, parse_mode="MarkdownV2")




async def get_quiz_index(user_id):
    get_user_index = f"""
        DECLARE $user_id AS Uint64;

        SELECT question_index
        FROM `quiz_state`
        WHERE user_id == $user_id;
    """
    results = await execute_select_query(pool, get_user_index, user_id=user_id)

    if len(results) == 0:
        return 0
    if results[0]["question_index"] is None:
        return 0
    return results[0]["question_index"]

async def get_user_score(user_id):
    get_score = f"""
        DECLARE $user_id AS Uint64;

        SELECT score
        FROM `quiz_state`
        WHERE user_id == $user_id;
    """
    results = await execute_select_query(pool, get_score, user_id=user_id)

    if len(results) == 0:
        return 0
    if results[0]["score"] is None:
        return 0
    return results[0]["score"]

async def update_quiz_index_and_score(user_id, question_index, score):
    set_quiz_state = f"""
        DECLARE $user_id AS Uint64;
        DECLARE $question_index AS Uint64;
        DECLARE $score AS Uint64;

        UPSERT INTO `quiz_state` (`user_id`, `question_index`, `score`)
        VALUES ($user_id, $question_index, $score);
    """

    await execute_update_query(
        pool,
        set_quiz_state,
        user_id=user_id,
        question_index=question_index,
        score = score
    )

# Получение квиза из БД
async def get_all_quiz_questions(pool):
    get_all_questions_query = """
        SELECT *
        FROM `quiz`;
    """
    results = await execute_select_query(pool, get_all_questions_query)
    
    # Преобразуем строки в словари
    questions = []
    for row in results:
        question_text = row['question']
        if isinstance(question_text, bytes):
            question_text = question_text.decode('utf-8')
        question = {
            'question': question_text,
            'options': json.loads(row['options'])['options'],  # Извлечение вложенного списка options
            'correct_option': row['correct_option']
        }
        questions.append(question)
    print("Loaded questions:", questions)  # Отладочное сообщение
    return questions
