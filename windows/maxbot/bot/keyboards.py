from __future__ import annotations

from ..api import keyboard as btn
from ..domain.dates import WEEKDAYS_SHORT


def main_menu() -> dict:
    return btn.keyboard(
        [btn.callback("👤 Профиль", "menu:profile"), btn.callback("🏫 Моя школа", "menu:school")],
        [btn.callback("📅 Расписание", "menu:schedule"), btn.callback("🔔 Звонки", "menu:bells")],
        [btn.callback("📝 Домашка", "menu:homework"), btn.callback("🎯 Оценки", "menu:grades")],
        [btn.callback("⏰ Контрольные", "menu:events"), btn.callback("⚙️ Настройки", "menu:settings")],
        [btn.callback("🤖 ИИ-помощник", "menu:ai")],
        [btn.callback("❓ Помощь", "menu:help")],
    )


def back_to_menu() -> dict:
    return btn.keyboard([btn.callback("⬅️ Меню", "menu:root")])


def cancel_only() -> dict:
    return btn.keyboard([btn.callback("Отмена", "flow:cancel")])


def schedule_menu(today_weekday: int, *, editable: bool = True) -> dict:
    days = [
        btn.callback(f"• {WEEKDAYS_SHORT[i]} •" if i == today_weekday else WEEKDAYS_SHORT[i], f"day:{i}")
        for i in range(7)
    ]
    return btn.keyboard(
        days[:4],
        days[4:],
        [btn.callback("📋 Вся неделя", "sched:week")],
        *([[btn.callback("➕ Добавить урок", "sched:add"), btn.callback("🔔 Звонки", "menu:bells")]] if editable else []),
        [btn.callback("⬅️ Меню", "menu:root")],
    )


def day_view(weekday: int, lesson_ids: list[int], *, editable: bool = True) -> dict:
    rows = []
    if editable:
        rows = [[btn.callback(f"🗑 Урок {i + 1}", f"sched:del:{lesson_id}")] for i, lesson_id in enumerate(lesson_ids)]
        rows.append([btn.callback("➕ Добавить сюда", f"sched:addto:{weekday}")])
    rows.append([btn.callback("⬅️ Дни недели", "menu:schedule")])
    return btn.keyboard(*rows)


def bells_menu(*, editable: bool = True) -> dict:
    if not editable:
        return back_to_menu()
    return btn.keyboard(
        [btn.callback("✏️ Задать своё расписание", "bells:set")],
        [btn.callback("↩️ Сбросить на стандартное", "bells:reset")],
        [btn.callback("⬅️ Меню", "menu:root")],
    )


def homework_menu() -> dict:
    return btn.keyboard(
        [btn.callback("📋 Показать всё", "hw:list"), btn.callback("➕ Добавить", "hw:add")],
        [btn.callback("⬅️ Меню", "menu:root")],
    )


def homework_list_keyboard(items: list[tuple[int, bool]], *, editable: bool = True) -> dict:
    rows = []
    for homework_id, done in items:
        mark = "↩️ Вернуть" if done else "✅ Готово"
        row = [btn.callback(mark, f"hw:done:{homework_id}")]
        if editable:
            row.append(btn.callback("🗑", f"hw:del:{homework_id}"))
        rows.append(row)
    rows.append(([btn.callback("➕ Добавить", "hw:add")] if editable else []) + [btn.callback("⬅️ Меню", "menu:root")])
    return btn.keyboard(*rows)


def grades_menu() -> dict:
    return btn.keyboard(
        [btn.callback("📋 Показать", "gr:list"), btn.callback("➕ Добавить", "gr:add")],
        [btn.callback("⬅️ Меню", "menu:root")],
    )


def grades_list_keyboard(ids: list[int], *, editable: bool = True) -> dict:
    if not editable:
        return back_to_menu()
    rows = [[btn.callback(f"🗑 Удалить #{gid}", f"gr:del:{gid}")] for gid in ids]
    rows.append([btn.callback("➕ Добавить", "gr:add"), btn.callback("⬅️ Меню", "menu:root")])
    return btn.keyboard(*rows)


def events_menu() -> dict:
    return btn.keyboard(
        [btn.callback("📋 Показать", "ev:list"), btn.callback("➕ Добавить", "ev:add")],
        [btn.callback("⬅️ Меню", "menu:root")],
    )


def events_list_keyboard(ids: list[int], *, editable: bool = True) -> dict:
    if not editable:
        return back_to_menu()
    rows = [[btn.callback(f"🗑 Удалить #{eid}", f"ev:del:{eid}")] for eid in ids]
    rows.append([btn.callback("➕ Добавить", "ev:add"), btn.callback("⬅️ Меню", "menu:root")])
    return btn.keyboard(*rows)


def ai_menu() -> dict:
    return btn.keyboard(
        [btn.callback("💬 Спросить", "ai:ask"), btn.callback("🧠 Тест по теме", "ai:quiz")],
        [btn.callback("✅ Проверить работу", "ai:check"), btn.callback("🔎 Найти в материалах", "ai:find")],
        [btn.callback("⬅️ Меню", "menu:root")],
    )


def ai_again(action: str) -> dict:
    return btn.keyboard(
        [btn.callback("🆕 Новый диалог" if action == "ask" else "🔁 Ещё раз", f"ai:{action}")],
        [btn.callback("🤖 ИИ-помощник", "menu:ai"), btn.callback("⬅️ Меню", "menu:root")],
    )


def quiz_options(options: list[str]) -> dict:
    letters = "АБВГДЕЖ"
    rows = [
        [btn.callback(f"{letters[i]}. {text}"[:60], f"quiz:answer:{i}")]
        for i, text in enumerate(options)
    ]
    rows.append([btn.callback("🛑 Закончить", "quiz:stop")])
    return btn.keyboard(*rows)


def quiz_next(last: bool) -> dict:
    label = "🏁 Итоги" if last else "➡️ Дальше"
    return btn.keyboard([btn.callback(label, "quiz:next")], [btn.callback("🛑 Закончить", "quiz:stop")])


def settings_menu(digest_enabled: bool) -> dict:
    toggle = btn.callback("🔕 Выключить дайджест" if digest_enabled else "🔔 Включить дайджест", "set:digest")
    return btn.keyboard([toggle], [btn.callback("⬅️ Меню", "menu:root")])
