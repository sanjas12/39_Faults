import os
import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

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
    if value is None:
        result = "—"
    else:
        result = str(value)
    if max_len > 0 and len(result) > max_len:
        return result[:max_len] + "..."
    return result


def safe_project_name(project: Any) -> str:
    """Безопасное получение имени проекта."""
    if project is None:
        return "Без проекта"
    if isinstance(project, dict):
        return project.get('name', 'Без проекта') or 'Без проекта'
    return str(project) or "Без проекта"


def draw_wrapped_lines(
    c: canvas.Canvas,
    text_lines: List[str],
    font_name: str,
    font_size: int,
    x: int,
    y: int,
    max_width: int,
    line_height: int = 18,
    bottom_margin: int = 50,
) -> int:
    """
    Рисует строки текста с переносами по ширине.
    Возвращает текущую координату Y после вывода.
    """
    c.setFont(font_name, font_size)
    page_width, page_height = letter
    for line in text_lines:
        words = line.split(" ")
        buffer = ""
        for word in words:
            test_line = f"{buffer} {word}".strip()
            if c.stringWidth(test_line, font_name, font_size) > max_width:
                c.drawString(x, y, buffer)
                y -= line_height
                buffer = word
            else:
                buffer = test_line
        if buffer:
            c.drawString(x, y, buffer)
            y -= line_height
        y -= 6  # дополнительный отступ между строками

        if y < bottom_margin:
            c.showPage()
            c.setFont(font_name, font_size)
            y = page_height - 50
    return y


def generate_faults_pdf(faults: List[Dict[str, Any]], title: str = "Отчёт по неисправностям") -> BytesIO:
    """Генерация PDF-отчёта по неисправностям"""
    
    buffer = BytesIO()
    font_name = register_font()
    
    c = canvas.Canvas(buffer, pagesize=letter)
    page_width, page_height = letter
    
    # Заголовок
    c.setFont(font_name, 16)
    c.drawString(50, page_height - 50, title)
    
    # Дата отчета
    c.setFont(font_name, 12)
    c.drawString(
        50,
        page_height - 80,
        f"Дата создания отчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )
    c.drawString(50, page_height - 100, f"Всего неисправностей: {len(faults)}")
    
    # Таблица
    y_position = page_height - 130
    c.setFont(font_name, 10)
    
    if faults:
        # Заголовки таблицы
        headers = ['ID', 'Название', 'Проект', 'Категория', 'Важность', 'Статус']
        col_widths = [30, 100, 60, 50, 40, 40]
        
        # Рисуем заголовок
        x_pos = 50
        c.setFont(font_name, 10)
        c.setFillColorRGB(0.05, 0.43, 0.99)  # синий фон
        c.rect(x_pos, y_position - 15, sum(col_widths), 15, fill=1)
        c.setFillColorRGB(1, 1, 1)  # белый текст
        for i, header in enumerate(headers):
            c.drawString(x_pos + 5, y_position - 10, header)
            x_pos += col_widths[i]
        y_position -= 15
        
        # Данные
        c.setFillColorRGB(0, 0, 0)  # чёрный текст
        for i, fault in enumerate(faults[:100]):
            # Чередование цветов строк
            if i % 2 == 0:
                c.setFillColorRGB(0.95, 0.95, 0.95)  # светло-серый
                c.rect(50, y_position - 12, sum(col_widths), 12, fill=1)
                c.setFillColorRGB(0, 0, 0)
            
            # ✅ Безопасное получение значений
            fault_id = safe_str(fault.get('id'), 0)
            fault_title = safe_str(fault.get('title'), 30)
            fault_project = safe_project_name(fault.get('project'))
            fault_category = safe_str(fault.get('category'), 12)
            fault_severity = safe_str(fault.get('severity'), 10)
            fault_status = safe_str(fault.get('status'), 10)
            
            row = [
                fault_id,
                fault_title,
                fault_project[:15] + ('...' if len(fault_project) > 15 else ''),
                fault_category,
                fault_severity,
                fault_status,
            ]
            
            x_pos = 50
            c.setFont(font_name, 8)
            for j, cell in enumerate(row):
                c.drawString(x_pos + 2, y_position - 7, str(cell))
                x_pos += col_widths[j]
            y_position -= 12
            
            if y_position < 50:
                c.showPage()
                y_position = page_height - 50
                c.setFont(font_name, 10)
        
        # Если записей больше 100
        if len(faults) > 100:
            y_position -= 10
            c.setFont(font_name, 8)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(50, y_position, f"* Показано первых 100 записей из {len(faults)}")
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
    
    c = canvas.Canvas(buffer, pagesize=letter)
    page_width, page_height = letter
    
    # Заголовок
    c.setFont(font_name, 16)
    c.drawString(50, page_height - 50, f"Неисправность #{fault.get('id', '')}")
    
    # Дата
    c.setFont(font_name, 12)
    c.drawString(
        50,
        page_height - 80,
        f"Дата создания отчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )
    
    y_position = page_height - 110
    
    # Основная информация
    fields = [
        ('Название', safe_str(fault.get('title'), 0)),
        ('Описание', safe_str(fault.get('description'), 0) or '—'),
        ('Проект', safe_project_name(fault.get('project'))),
        ('Категория', safe_str(fault.get('category'), 0) or '—'),
        ('Важность', safe_str(fault.get('severity'), 0) or '—'),
        ('Статус', safe_str(fault.get('status'), 0) or '—'),
        ('Создана', safe_str(fault.get('created_at'), 0) or '—'),
        ('Изменена', safe_str(fault.get('updated_at'), 0) or 'Не изменялась'),
        ('Закрыта', safe_str(fault.get('resolved_at'), 0) or 'Не закрыта'),
    ]
    
    c.setFont(font_name, 10)
    for label, value in fields:
        c.setFont(font_name, 10)
        c.drawString(50, y_position, f"{label}:")
        c.setFont(font_name, 10)
        c.drawString(150, y_position, str(value)[:80])
        y_position -= 18
    
    # Планируемые мероприятия
    if fault.get('planned_actions'):
        y_position -= 10
        c.setFont(font_name, 12)
        c.drawString(50, y_position, "Планируемые мероприятия:")
        y_position -= 20
        c.setFont(font_name, 10)
        lines = fault['planned_actions'].split('\n')
        for line in lines[:10]:
            if y_position < 50:
                c.showPage()
                y_position = page_height - 50
                c.setFont(font_name, 10)
            c.drawString(70, y_position, line[:80])
            y_position -= 15
    
    # Связанные статьи
    if fault.get('linked_knowledge'):
        y_position -= 10
        c.setFont(font_name, 12)
        c.drawString(50, y_position, "Связанные статьи:")
        y_position -= 20
        c.setFont(font_name, 10)
        for article in fault.get('linked_knowledge', [])[:5]:
            if y_position < 50:
                c.showPage()
                y_position = page_height - 50
                c.setFont(font_name, 10)
            title = safe_str(article.get('title'), 60)
            c.drawString(70, y_position, f"• {title}")
            y_position -= 15
    
    # Клоны
    if fault.get('clones'):
        y_position -= 10
        c.setFont(font_name, 12)
        c.drawString(50, y_position, "Клоны:")
        y_position -= 20
        c.setFont(font_name, 10)
        for clone in fault.get('clones', [])[:5]:
            if y_position < 50:
                c.showPage()
                y_position = page_height - 50
                c.setFont(font_name, 10)
            clone_title = safe_str(clone.get('title'), 50)
            c.drawString(70, y_position, f"• #{clone.get('id', '')} {clone_title}")
            y_position -= 15
    
    # Родительская неисправность
    if fault.get('parent_fault'):
        y_position -= 10
        c.setFont(font_name, 12)
        c.drawString(50, y_position, "Родительская неисправность:")
        y_position -= 20
        c.setFont(font_name, 10)
        parent = fault['parent_fault']
        parent_title = safe_str(parent.get('title'), 60)
        c.drawString(70, y_position, f"#{parent.get('id', '')} {parent_title}")
    
    # Подвал
    c.setFont(font_name, 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 30, "Система отслеживания неисправностей АСУ ТП")
    c.drawString(page_width - 150, 30, f"Страница {c.getPageNumber()}")
    
    c.save()
    buffer.seek(0)
    return buffer