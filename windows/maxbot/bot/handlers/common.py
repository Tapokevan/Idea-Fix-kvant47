from __future__ import annotations

from .. import keyboards as kb
from ..context import Context
from ..router import Router
from . import events, grades, homework, schedule, school, settings

HELP_TEXT = (
    "Вот что я умею:\n\n"
    "/profile — профиль ученика (бета)\n"
    "/school — моя школа (бета)\n"
    "/today — расписание и дела на сегодня\n"
    "/tomorrow — то же самое на завтра\n"
    "/week — расписание на неделю\n"
    "/bells — звонки и сколько осталось до конца урока\n"
    "/homework — домашние задания\n"
    "/grades — оценки\n"
    "/events — контрольные, экзамены, дедлайны\n"
    "/timezone — часовой пояс для дайджестов\n"
    "/menu — открыть меню с кнопками\n\n"
    "ИИ-помощник (работает на GigaChat):\n"
    "/ask — объяснить тему или разобрать задачу\n"
    "/quiz — тест с вариантами ответа по любой теме\n"
    "/check — проверить свою работу и получить разбор\n"
    "/find — найти ответ в расписании, домашке и контрольных\n\n"
    "Расписание, домашку и события в общем чате может редактировать любой участник — "
    "это общий список для всего класса. Оценки у каждого свои."
)

START_TEXT = (
    "Привет{name}! Я школьный бот-помощник 🎒\n\n"
    "Слежу за расписанием уроков и звонков, домашкой, оценками и контрольными, "
    "а по утрам и вечерам сама напоминаю, что нас ждёт.\n\n"
    "Ещё умею объяснять темы, делать тесты и проверять работы — это раздел «ИИ-помощник».\n\n"
    "Выбирай раздел кнопками ниже или набери /help."
)


def register(router: Router) -> None:
    @router.command("/start")
    async def start(ctx: Context, args: str) -> None:
        name = f", {ctx.user.first_name}" if ctx.user else ""
        if ctx.is_demo:
            await school.render_profile(ctx)
        else:
            await ctx.reply(START_TEXT.format(name=name), keyboard=kb.main_menu())

    @router.command("/help")
    async def help_(ctx: Context, args: str) -> None:
        text = HELP_TEXT
        if ctx.is_demo:
            text = text[:text.index("Расписание, домашку")] + "БЕТА: школа и профиль вымышленные и общие для всех. Данные уже заполнены."
        await ctx.reply(text)

    @router.command("/menu")
    async def menu(ctx: Context, args: str) -> None:
        await ctx.show("Выбирай раздел:", keyboard=kb.main_menu())

    @router.callback("menu")
    async def menu_callback(ctx: Context, args: list[str]) -> None:
        await ctx.clear_pending()
        section = args[0] if args else "root"

        if section == "profile":
            await school.render_profile(ctx)
        elif section == "school":
            await school.render_school(ctx)
        elif section == "schedule":
            await schedule.render_schedule_menu(ctx)
        elif section == "bells":
            await schedule.render_bells(ctx)
        elif section == "homework":
            await homework.render_list(ctx)
        elif section == "grades":
            await grades.render_list(ctx)
        elif section == "events":
            await events.render_list(ctx)
        elif section == "ai":
            await ctx.show("ИИ-помощник — что нужно?", keyboard=kb.ai_menu())
        elif section == "settings":
            await settings.render(ctx)
        elif section == "help":
            text = HELP_TEXT
            if ctx.is_demo:
                text = text[:text.index("Расписание, домашку")] + "БЕТА: школа и профиль вымышленные и общие для всех. Данные уже заполнены."
            await ctx.show(text, keyboard=kb.back_to_menu())
        else:
            await ctx.show("Выбирай раздел:", keyboard=kb.main_menu())

    @router.callback("flow")
    async def flow_callback(ctx: Context, args: list[str]) -> None:
        if args and args[0] == "cancel":
            await ctx.clear_pending()
            await ctx.show("Отменила. Выбирай раздел:", keyboard=kb.main_menu())
