import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

# Путь к шрифтам
FONTS_DIR = Path(__file__).parent.parent / "fonts"
FONTS_DIR.mkdir(exist_ok=True)


def register_font() -> str:
    """Регистрация шрифта с поддержкой Unicode. Возвращает имя шрифта."""
    for font_name, font_file in [
        ("ArialUnicode", "arial.ttf"),
        ("DejaVuSans", "DejaVuSans.ttf"),
    ]:
        font_path = FONTS_DIR / font_file
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                logger.debug(f"Зарегистрирован шрифт: {font_name} ({font_file})")
                return font_name
            except Exception as e:
                logger.warning(f"Не удалось зарегистрировать шрифт {font_name}: {e}")
    logger.warning("Используется резервный шрифт: Helvetica")
    return "Helvetica"


def safe_str(value: Any, max_len: int = 0) -> str:
    """Безопасное преобразование значения в строку с обрезанием по длине."""
    result = "—" if value is None else str(value)
    if max_len > 0 and len(result) > max_len:
        return result[:max_len] + "..."
    return result


def safe_project_name(project: Any) -> str:
    """Безопасное получение имени проекта."""
    if project is None:
        return "Без проекта"
    if isinstance(project, dict):
        return project.get("name", "Без проекта") or "Без проекта"
    return str(project) or "Без проекта"


def generate_faults_pdf(
    faults: List[Dict[str, Any]], title: str = "Отчёт по неисправностям"
) -> BytesIO:
    """Генерация PDF-отчёта по неисправностям в альбомной ориентации"""

    buffer = BytesIO()
    font_name = register_font()

    # Альбомная ориентация
    page_width, page_height = landscape(A4)

    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Заголовок
    c.setFont(font_name, 18)
    c.drawString(50, page_height - 50, title)

    # Дата отчета
    c.setFont(font_name, 11)
    c.drawString(
        50,
        page_height - 80,
        f"Дата создания отчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )
    c.drawString(50, page_height - 100, f"Всего неисправностей: {len(faults)}")

    # Таблица
    y_position = page_height - 140

    if faults:
        # ✅ Все колонки с увеличенной шириной для альбомной ориентации
        headers = [
            "ID",
            "Название",
            "Проект",
            "Категория",
            "Важность",
            "Статус",
            "Создана",
            "Закрыта",
            "Меропр.",
        ]
        # Увеличенные ширины колонок
        col_widths = [25, 160, 130, 80, 50, 55, 60, 60, 45]

        # Рисуем заголовок
        x_pos = 50
        c.setFont(font_name, 9)
        c.setFillColorRGB(0.05, 0.43, 0.99)
        c.rect(x_pos, y_position - 18, sum(col_widths), 18, fill=1)
        c.setFillColorRGB(1, 1, 1)
        for i, header in enumerate(headers):
            c.drawString(x_pos + 4, y_position - 12, header)
            x_pos += col_widths[i]
        y_position -= 18

        # Данные
        c.setFillColorRGB(0, 0, 0)
        for i, fault in enumerate(faults):
            # Чередование цветов строк
            if i % 2 == 0:
                c.setFillColorRGB(0.95, 0.95, 0.95)
                c.rect(50, y_position - 14, sum(col_widths), 14, fill=1)
                c.setFillColorRGB(0, 0, 0)

            # Словари для перевода
            severity_map = {
                "critical": "Критическая",
                "major": "Серьёзная",
                "minor": "Незначительная",
                "trivial": "Тривиальная",
            }
            status_map = {
                "open": "Открыта",
                "in_progress": "В работе",
                "review": "На проверке",
                "closed": "Закрыта",
            }

            severity = fault.get("severity", "")
            status = fault.get("status", "")

            # Обрезаем длинные значения
            title_val = safe_str(fault.get("title"), 40)
            project_val = safe_project_name(fault.get("project"))
            project_val = project_val[:35] + ("..." if len(project_val) > 35 else "")
            category_val = safe_str(fault.get("category"), 20)

            row = [
                safe_str(fault.get("id"), 0),
                title_val,
                project_val,
                category_val,
                severity_map.get(severity, severity) or "—",
                status_map.get(status, status) or "—",
                safe_str(fault.get("created_at", ""), 10)
                if fault.get("created_at")
                else "—",
                safe_str(fault.get("resolved_at", ""), 10)
                if fault.get("resolved_at")
                else "—",
                "Да" if fault.get("planned_actions") else "Нет",
            ]

            x_pos = 50
            c.setFont(font_name, 8)
            for j, cell in enumerate(row):
                c.drawString(x_pos + 3, y_position - 8, str(cell))
                x_pos += col_widths[j]
            y_position -= 14

            if y_position < 50:
                c.showPage()
                y_position = page_height - 50
                c.setFont(font_name, 8)

        # Если записей больше 100
        if len(faults) > 100:
            y_position -= 10
            c.setFont(font_name, 8)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(
                50, y_position, f"* Показано первых 100 записей из {len(faults)}"
            )
    else:
        c.setFont(font_name, 12)
        c.drawString(50, y_position, "Нет данных для отображения")

    # Подвал
    c.setFont(font_name, 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 30, "Система отслеживания неисправностей АСУ ТП")
    c.drawString(page_width - 150, 30, f"Страница {c.getPageNumber()}")

    c.save()
    buffer.seek(0)
    return buffer


def generate_single_fault_pdf(fault: Dict[str, Any]) -> BytesIO:
    """Генерация PDF-отчёта по одной неисправности"""

    buffer = BytesIO()
    font_name = register_font()

    page_width, page_height = landscape(A4)

    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Заголовок
    c.setFont(font_name, 20)
    c.drawString(50, page_height - 50, f"Неисправность #{fault.get('id', '')}")

    # Дата
    c.setFont(font_name, 11)
    c.drawString(
        50,
        page_height - 80,
        f"Дата создания отчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )

    y_position = page_height - 110

    # Основная информация (в две колонки)
    severity_map = {
        "critical": "Критическая",
        "major": "Серьёзная",
        "minor": "Незначительная",
        "trivial": "Тривиальная",
    }
    status_map = {
        "open": "Открыта",
        "in_progress": "В работе",
        "review": "На проверке",
        "closed": "Закрыта",
    }

    fields_left = [
        ("Название", safe_str(fault.get("title"), 0)),
        ("Описание", safe_str(fault.get("description"), 0) or "—"),
        ("Проект", safe_project_name(fault.get("project"))),
        ("Категория", safe_str(fault.get("category"), 0) or "—"),
    ]

    fields_right = [
        (
            "Важность",
            severity_map.get(fault.get("severity"), fault.get("severity") or "—"),
        ),
        ("Статус", status_map.get(fault.get("status"), fault.get("status") or "—")),
        ("Создана", safe_str(fault.get("created_at"), 0) or "—"),
        ("Закрыта", safe_str(fault.get("resolved_at"), 0) or "Не закрыта"),
    ]

    c.setFont(font_name, 11)

    # Левая колонка
    x_left = 50
    y_left = y_position
    for label, value in fields_left:
        c.setFont(font_name, 11)
        c.drawString(x_left, y_left, f"{label}:")
        c.setFont(font_name, 11)
        c.drawString(x_left + 110, y_left, str(value)[:70])
        y_left -= 20

    # Правая колонка
    x_right = 380
    y_right = y_position
    for label, value in fields_right:
        c.setFont(font_name, 11)
        c.drawString(x_right, y_right, f"{label}:")
        c.setFont(font_name, 11)
        c.drawString(x_right + 100, y_right, str(value)[:50])
        y_right -= 20

    y_position = min(y_left, y_right) - 20

    # Планируемые мероприятия
    if fault.get("planned_actions"):
        y_position -= 10
        c.setFont(font_name, 14)
        c.drawString(50, y_position, "Планируемые мероприятия:")
        y_position -= 25
        c.setFont(font_name, 10)
        lines = fault["planned_actions"].split("\n")
        for line in lines[:10]:
            if y_position < 50:
                c.showPage()
                y_position = page_height - 50
                c.setFont(font_name, 10)
            c.drawString(70, y_position, line[:120])
            y_position -= 16

    # Связанные статьи
    if fault.get("linked_knowledge"):
        y_position -= 10
        c.setFont(font_name, 14)
        c.drawString(50, y_position, "Связанные статьи:")
        y_position -= 25
        c.setFont(font_name, 10)
        for article in fault.get("linked_knowledge", [])[:5]:
            if y_position < 50:
                c.showPage()
                y_position = page_height - 50
                c.setFont(font_name, 10)
            title = safe_str(article.get("title"), 70)
            c.drawString(70, y_position, f"• {title}")
            y_position -= 16

    # Клоны
    if fault.get("clones"):
        y_position -= 10
        c.setFont(font_name, 14)
        c.drawString(50, y_position, "Клоны:")
        y_position -= 25
        c.setFont(font_name, 10)
        for clone in fault.get("clones", [])[:5]:
            if y_position < 50:
                c.showPage()
                y_position = page_height - 50
                c.setFont(font_name, 10)
            clone_title = safe_str(clone.get("title"), 60)
            c.drawString(70, y_position, f"• #{clone.get('id', '')} {clone_title}")
            y_position -= 16

    # Родительская неисправность
    if fault.get("parent_fault"):
        y_position -= 10
        c.setFont(font_name, 14)
        c.drawString(50, y_position, "Родительская неисправность:")
        y_position -= 25
        c.setFont(font_name, 10)
        parent = fault["parent_fault"]
        parent_title = safe_str(parent.get("title"), 70)
        c.drawString(70, y_position, f"#{parent.get('id', '')} {parent_title}")

    # Подвал
    c.setFont(font_name, 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 30, "Система отслеживания неисправностей АСУ ТП")
    c.drawString(page_width - 150, 30, f"Страница {c.getPageNumber()}")

    c.save()
    buffer.seek(0)
    return buffer
