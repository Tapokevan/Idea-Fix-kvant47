from __future__ import annotations

import logging
from typing import Any

from ...ai import HomeworkReview, describe_error
from ...ai.assistant import ASK_MESSAGE_CHARS, Quiz, QuizQuestion, trim_dialogue_history
from ...ai.gigachat import GigaChatError
from ...domain import events as events_domain
from ...domain import homework as homework_domain
from ...domain import schedule as schedule_domain
from .. import keyboards as kb
from ..context import Context
from ..formatting import format_ai_text
from ..router import Router

log = logging.getLogger(__name__)
THINKING = "Думаю…"
ASK_INTRO = (
    "О чём спросить? Напиши вопрос по любому предмету.\n\n"
    "После ответа можно сразу задать уточнение — я сохраняю контекст разговора. "
    "Кнопка «Новый диалог» начинает разговор заново, а «Меню» завершает его."
)
MATERIALS_LIMIT = 6000
QUIZ_TOPIC_LIMIT = 120
REVIEW_SUBJECT_LIMIT = 100
REVIEW_TASK_LIMIT = 500
REVIEW_ANSWER_LIMIT = 4000

QUIZ_STATE = "quiz_active"

AI_FLOWS = {
    "ask": ("ask_question", ASK_INTRO),
    "quiz": ("quiz_topic", "По какой теме сделать тест? Например «Фотосинтез» или «Дроби»."),
    "check": ("check_work", "По какому предмету работа?"),
    "find": ("find_query", "Что найти? Например «когда контрольная по химии» или «что задали по алгебре»."),
}


def _log_failure(operation: str, exc: Exception) -> None:
    log.error(
        "AI operation=%s failed: type=%s status=%s cause=%s",
        operation, type(exc).__name__, exc.status if isinstance(exc, GigaChatError) else "-",
        type(exc.__cause__).__name__ if exc.__cause__ else "-",
    )


async def _start_flow(ctx: Context, action: str) -> None:
    flow, prompt = AI_FLOWS[action]
    data = {"step": "subject"} if action == "check" else {}
    await ctx.set_pending(flow, data)
    await ctx.show(prompt, keyboard=kb.cancel_only())


async def _guard(ctx: Context) -> bool:
    if ctx.ai.enabled:
        return True
    await ctx.show(
        "ИИ-функции пока не подключены. Администратору бота нужно добавить GIGACHAT_AUTH_KEY "
        "в настройки — ключ выдаётся в личном кабинете GigaChat API.",
        keyboard=kb.back_to_menu(),
    )
    return False


async def _collect_materials(ctx: Context) -> str:
    lessons = await ctx.storage.list_lessons(ctx.data_chat_id)
    bells = await ctx.storage.get_bells(ctx.data_chat_id)
    homework = await ctx.storage.list_homework(ctx.data_chat_id, ctx.student_id)
    events = await ctx.storage.list_events(ctx.data_chat_id, from_date=ctx.today)

    blocks = [f"Сегодня: {ctx.today.isoformat()}"]
    if lessons:
        week = schedule_domain.format_week(schedule_domain.group_by_weekday(lessons), bells)
        blocks.append(f"Расписание уроков:\n{week}")
    if homework:
        blocks.append(f"Домашние задания:\n{homework_domain.format_list(homework, today_date=ctx.today)}")
    if events:
        blocks.append(f"Контрольные и события:\n{events_domain.format_list(events, today_date=ctx.today)}")

    return "\n\n".join(blocks)[:MATERIALS_LIMIT] if len(blocks) > 1 else ""


def _format_review(review: HomeworkReview) -> str:
    lines = [f"Оценка за работу: {review.score} из 5"]
    if review.correct:
        lines += ["", "Получилось:"] + [f"+ {item}" for item in review.correct]
    if review.mistakes:
        lines += ["", "Стоит исправить:"] + [f"- {item}" for item in review.mistakes]
    if review.advice:
        lines += ["", f"Совет: {review.advice}"]
    return "\n".join(lines)


def _quiz_to_data(quiz: Quiz) -> dict[str, Any]:
    return {
        "topic": quiz.topic,
        "index": 0,
        "score": 0,
        "answered": False,
        "questions": [
            {
                "question": item.question,
                "options": item.options,
                "correct_index": item.correct_index,
                "explanation": item.explanation,
            }
            for item in quiz.questions
        ],
    }


def _question_at(data: dict[str, Any], index: int) -> QuizQuestion | None:
    questions = data.get("questions") or []
    if not 0 <= index < len(questions):
        return None
    item = questions[index]
    return QuizQuestion(
        question=item["question"],
        options=list(item["options"]),
        correct_index=item["correct_index"],
        explanation=item.get("explanation", ""),
    )


async def _show_question(ctx: Context, data: dict[str, Any]) -> None:
    index = data["index"]
    question = _question_at(data, index)
    if question is None:
        await _show_result(ctx, data)
        return
    total = len(data["questions"])
    text = f"Тест: {data['topic']}\nВопрос {index + 1} из {total}\n\n{question.question}"
    options = [format_ai_text(option, markdown=False) for option in question.options]
    await ctx.show(format_ai_text(text), keyboard=kb.quiz_options(options), fmt="markdown")


async def _show_result(ctx: Context, data: dict[str, Any]) -> None:
    await ctx.clear_pending()
    score, total = data["score"], len(data["questions"])
    if total and score == total:
        verdict = "идеально!"
    elif total and score * 2 >= total:
        verdict = "неплохо, но есть что повторить."
    else:
        verdict = "тему стоит разобрать ещё раз."
    await ctx.show(
        f"Тест по теме «{data['topic']}» закончен.\nРезультат: {score} из {total} — {verdict}",
        keyboard=kb.ai_again("quiz"),
    )


async def _run_quiz(ctx: Context, topic: str) -> None:
    if len(topic) > QUIZ_TOPIC_LIMIT:
        await ctx.set_pending("quiz_topic", {})
        await ctx.reply(
            f"Тема слишком длинная ({len(topic)} знаков). Сократи её до {QUIZ_TOPIC_LIMIT} знаков и отправь снова.",
            keyboard=kb.cancel_only(),
        )
        return
    await ctx.show(f"Составляю тест по теме «{topic}»…")
    try:
        quiz = await ctx.ai.make_quiz(topic)
    except Exception as exc:
        _log_failure("quiz", exc)
        await ctx.reply(describe_error(exc), keyboard=kb.ai_again("quiz"))
        return
    data = _quiz_to_data(quiz)
    await ctx.set_pending(QUIZ_STATE, data)
    await _show_question(ctx, data)


async def _run_ask(ctx: Context, question: str, history: list[dict[str, str]] | None = None) -> None:
    history = trim_dialogue_history(history or [])
    await ctx.set_pending("ask_question", {"history": history})
    if len(question) > ASK_MESSAGE_CHARS:
        await ctx.reply(
            f"Вопрос слишком длинный ({len(question)} знаков). Сократи его до {ASK_MESSAGE_CHARS} знаков "
            "и отправь снова. Предыдущий разговор сохранён.",
            keyboard=kb.ai_again("ask"),
        )
        return
    await ctx.show(THINKING)
    try:
        answer = await ctx.ai.ask(question, history=history)
    except Exception as exc:
        _log_failure("ask", exc)
        await ctx.reply(describe_error(exc), keyboard=kb.ai_again("ask"))
        return
    history = trim_dialogue_history([*history, {"question": question, "answer": answer}])
    await ctx.set_pending("ask_question", {"history": history})
    await ctx.reply(format_ai_text(answer), keyboard=kb.ai_again("ask"), fmt="markdown")


async def _run_find(ctx: Context, query: str) -> None:
    await ctx.show("Ищу в материалах класса…")
    materials = await _collect_materials(ctx)
    try:
        answer = await ctx.ai.search(query, materials)
    except Exception as exc:
        _log_failure("find", exc)
        await ctx.reply(describe_error(exc), keyboard=kb.ai_again("find"))
        return
    await ctx.reply(format_ai_text(answer), keyboard=kb.ai_again("find"), fmt="markdown")


def register(router: Router) -> None:
    @router.command("/ask")
    async def ask_cmd(ctx: Context, args: str) -> None:
        if not await _guard(ctx):
            return
        if args.strip():
            await _run_ask(ctx, args.strip())
            return
        await _start_flow(ctx, "ask")

    @router.command("/quiz")
    async def quiz_cmd(ctx: Context, args: str) -> None:
        if not await _guard(ctx):
            return
        if args.strip():
            await _run_quiz(ctx, args.strip())
            return
        await _start_flow(ctx, "quiz")

    @router.command("/check")
    async def check_cmd(ctx: Context, args: str) -> None:
        if not await _guard(ctx):
            return
        await _start_flow(ctx, "check")

    @router.command("/find")
    async def find_cmd(ctx: Context, args: str) -> None:
        if not await _guard(ctx):
            return
        if args.strip():
            await _run_find(ctx, args.strip())
            return
        await _start_flow(ctx, "find")

    @router.callback("ai")
    async def ai_callback(ctx: Context, args: list[str]) -> None:
        if not args or not await _guard(ctx):
            return
        action = args[0]

        if action in AI_FLOWS:
            await _start_flow(ctx, action)

    @router.callback("quiz")
    async def quiz_callback(ctx: Context, args: list[str]) -> None:
        if not args or ctx.user_id is None:
            return
        pending = await ctx.storage.get_pending(ctx.chat_id, ctx.user_id)
        if not pending or pending[0] != QUIZ_STATE:
            await ctx.toast("Тест уже завершён")
            return
        data = pending[1]
        action = args[0]

        if action == "stop":
            await _show_result(ctx, data)
            return

        if action == "next":
            if not data.get("answered"):
                await ctx.toast("Сначала выбери ответ на вопрос")
                return
            data["index"] += 1
            data["answered"] = False
            await ctx.set_pending(QUIZ_STATE, data)
            await _show_question(ctx, data)
            return

        if action == "answer" and len(args) > 1 and args[1].isdigit():
            if data.get("answered"):
                await ctx.toast("Ответ уже принят")
                return
            question = _question_at(data, data["index"])
            if question is None:
                await _show_result(ctx, data)
                return
            chosen = int(args[1])
            if not 0 <= chosen < len(question.options):
                await ctx.toast("Такого варианта ответа нет")
                return
            correct = chosen == question.correct_index
            data["answered"] = True
            if correct:
                data["score"] += 1
            await ctx.set_pending(QUIZ_STATE, data)

            total = len(data["questions"])
            head = "Верно!" if correct else f"Неверно. Правильный ответ: {question.correct_option}"
            lines = [head]
            if question.explanation:
                lines += ["", question.explanation]
            lines += ["", f"Счёт: {data['score']} из {data['index'] + 1}"]
            await ctx.show(format_ai_text("\n".join(lines)), keyboard=kb.quiz_next(data["index"] + 1 >= total), fmt="markdown")

    @router.flow("ask_question")
    async def ask_flow(ctx: Context, text: str, data: dict) -> None:
        history = data.get("history", [])
        await _run_ask(ctx, text, history if isinstance(history, list) else [])

    @router.flow("quiz_topic")
    async def quiz_topic_flow(ctx: Context, text: str, data: dict) -> None:
        await ctx.clear_pending()
        await _run_quiz(ctx, text)

    @router.flow("find_query")
    async def find_flow(ctx: Context, text: str, data: dict) -> None:
        await ctx.clear_pending()
        await _run_find(ctx, text)

    @router.flow(QUIZ_STATE)
    async def quiz_guard_flow(ctx: Context, text: str, data: dict) -> None:
        await ctx.reply("Сейчас идёт тест — выбери вариант кнопкой под вопросом или нажми «Закончить».")

    @router.flow("check_work")
    async def check_flow(ctx: Context, text: str, data: dict) -> None:
        step = data.get("step")

        if step == "subject":
            subject = text.strip()
            if not subject or len(subject) > REVIEW_SUBJECT_LIMIT:
                await ctx.reply(
                    f"Укажи предмет: от 1 до {REVIEW_SUBJECT_LIMIT} знаков.", keyboard=kb.cancel_only(),
                )
                return
            data["subject"] = subject
            data["step"] = "task"
            await ctx.set_pending("check_work", data)
            await ctx.reply("Что было задано? Опиши задание в двух словах.", keyboard=kb.cancel_only())
            return

        if step == "task":
            task = text.strip()
            if not task or len(task) > REVIEW_TASK_LIMIT:
                await ctx.reply(
                    f"Условие должно содержать от 1 до {REVIEW_TASK_LIMIT} знаков. Сократи его и отправь снова.",
                    keyboard=kb.cancel_only(),
                )
                return
            data["task"] = task
            data["step"] = "answer"
            await ctx.set_pending("check_work", data)
            await ctx.reply("Теперь пришли свою работу или решение целиком.", keyboard=kb.cancel_only())
            return

        if step == "answer":
            answer = text.strip()
            if not answer or len(answer) > REVIEW_ANSWER_LIMIT:
                await ctx.reply(
                    f"Работа должна содержать от 1 до {REVIEW_ANSWER_LIMIT} знаков. "
                    "Сократи её и отправь снова. Предмет и условие сохранены.",
                    keyboard=kb.cancel_only(),
                )
                return
            await ctx.reply("Проверяю…")
            try:
                review = await ctx.ai.review(data["subject"], data["task"], answer)
            except Exception as exc:
                _log_failure("check", exc)
                await ctx.reply(
                    describe_error(exc) + "\n\nПредмет и условие сохранены. Отправь работу ещё раз, чтобы повторить проверку.",
                    keyboard=kb.cancel_only(),
                )
                return
            await ctx.reply(format_ai_text(_format_review(review)), keyboard=kb.ai_again("check"), fmt="markdown")
            await ctx.clear_pending()
