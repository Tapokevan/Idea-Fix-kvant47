from ...domain.grades import average
from ...domain.school import DEMO_STUDENT
from .. import keyboards as kb
from ..context import Context
from ..router import Router


async def render_profile(ctx: Context) -> None:
    if not ctx.is_demo:
        await ctx.show("Демопрофиль доступен при MAX_DEMO_MODE=true.", keyboard=kb.back_to_menu())
        return
    student = DEMO_STUDENT
    grades = await ctx.storage.list_grades(ctx.data_chat_id, ctx.student_id)
    homework = await ctx.storage.list_homework(ctx.data_chat_id, ctx.student_id, only_pending=True)
    events = await ctx.storage.list_events(ctx.data_chat_id, from_date=ctx.today)
    text = (
        f"Профиль ученика · БЕТА\n\n{student.name}\n{student.school} · {student.classroom}\n"
        f"Классный руководитель: {student.teacher}\n\n"
        f"Средний балл: {average(grades):.2f}\n"
        f"Заданий осталось: {len(homework)}\nПредстоящих событий: {len(events)}\n\n"
        "Это вымышленный ученик. Профиль и отметки о выполнении домашки общие для всех участников беты. "
        "Даты заданий и событий обновляются ежедневно; выполненные задания при этом сбрасываются."
    )
    await ctx.show(text, keyboard=kb.main_menu())


async def render_school(ctx: Context) -> None:
    if not ctx.is_demo:
        await ctx.show("Демошкола доступна при MAX_DEMO_MODE=true.", keyboard=kb.back_to_menu())
        return
    student = DEMO_STUDENT
    await ctx.show(
        f"{student.school} · БЕТА\n\nКласс: {student.classroom}\n"
        f"Классный руководитель: {student.teacher}\n"
        "Учебная неделя: понедельник–пятница\nНачало занятий: 08:30\n"
        "Урок: 45 минут\n\n"
        "Вымышленная школа для знакомства с ботом. Расписание, домашка, оценки и события уже заполнены. "
        "Подключения к реальному электронному дневнику нет.",
        keyboard=kb.main_menu(),
    )


def register(router: Router) -> None:
    @router.command("/profile")
    async def profile(ctx: Context, args: str) -> None:
        await render_profile(ctx)

    @router.command("/school")
    async def school(ctx: Context, args: str) -> None:
        await render_school(ctx)
