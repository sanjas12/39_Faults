from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from io import BytesIO
from typing import List, Dict, Any

def generate_faults_pdf(faults: List[Dict[str, Any]], title: str = "Отчёт по неисправностям") -> BytesIO:
    """Генерация PDF-отчёта по неисправностям"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        title=title
    )
    
    styles = getSampleStyleSheet()
    
    # Стиль для заголовка
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=colors.HexColor('#0d6efd')
    )
    
    # Стиль для подзаголовка
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=colors.grey
    )
    
    # Стиль для заголовков таблицы
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )
    
    # Стиль для ячеек таблицы
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_LEFT
    )
    
    elements = []
    
    # Заголовок
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f"Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
    elements.append(Paragraph(f"Всего неисправностей: {len(faults)}", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    if faults:
        # Подготовка данных для таблицы
        headers = ['ID', 'Название', 'Проект', 'Категория', 'Важность', 'Статус', 'Создана']
        
        # Ограничиваем количество записей для PDF (максимум 100)
        display_faults = faults[:100]
        
        table_data = [headers]
        
        for fault in display_faults:
            row = [
                str(fault.get('id', '')),
                fault.get('title', '')[:50] + ('...' if len(fault.get('title', '')) > 50 else ''),
                fault.get('project', {}).get('name', 'Без проекта') if isinstance(fault.get('project'), dict) else 'Без проекта',
                fault.get('category', '—') or '—',
                fault.get('severity', ''),
                fault.get('status', ''),
                fault.get('created_at', '')[:10] if fault.get('created_at') else '',
            ]
            table_data.append(row)
        
        # Создаём таблицу
        table = Table(table_data, repeatRows=1)
        
        # Стили для таблицы
        style = TableStyle([
            # Заголовок
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            
            # Ячейки
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            
            # Границы
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Чередование цветов строк
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ])
        
        table.setStyle(style)
        
        # Устанавливаем ширину колонок
        col_widths = [0.5*inch, 2.5*inch, 1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch]
        table._argW = col_widths
        
        elements.append(table)
        
        # Если записей больше 100, добавляем примечание
        if len(faults) > 100:
            note_style = ParagraphStyle(
                'Note',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_LEFT
            )
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(f"* Показано первых 100 записей из {len(faults)}", note_style))
    else:
        # Если нет данных
        no_data_style = ParagraphStyle(
            'NoData',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        elements.append(Paragraph("Нет данных для отображения", no_data_style))
    
    # Добавляем подвал
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("Система отслеживания неисправностей АСУ ТП", footer_style))
    
    # Строим PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_single_fault_pdf(fault: Dict[str, Any]) -> BytesIO:
    """Генерация PDF-отчёта по одной неисправности"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.7*inch,
        leftMargin=0.7*inch,
        topMargin=0.7*inch,
        bottomMargin=0.7*inch,
        title=f"Неисправность #{fault.get('id', '')}"
    )
    
    styles = getSampleStyleSheet()
    
    # Стили
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor('#0d6efd')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=12,
        textColor=colors.grey
    )
    
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading3'],
        fontSize=11,
        spaceAfter=4,
        spaceBefore=8,
        textColor=colors.HexColor('#0d6efd')
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        fontName='Helvetica-Bold'
    )
    
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4
    )
    
    elements = []
    
    # Заголовок
    elements.append(Paragraph(f"Неисправность #{fault.get('id', '')}", title_style))
    elements.append(Paragraph(f"Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Основная информация
    elements.append(Paragraph("Основная информация", section_style))
    
    fields = [
        ('Название', fault.get('title', '—')),
        ('Описание', fault.get('description', '—') or '—'),
        ('Проект', fault.get('project', {}).get('name', 'Без проекта') if isinstance(fault.get('project'), dict) else 'Без проекта'),
        ('Категория', fault.get('category', '—') or '—'),
        ('Важность', fault.get('severity', '—')),
        ('Статус', fault.get('status', '—')),
        ('Создана', fault.get('created_at', '—')),
        ('Изменена', fault.get('updated_at', '—') or 'Не изменялась'),
        ('Закрыта', fault.get('resolved_at', '—') or 'Не закрыта'),
    ]
    
    for label, value in fields:
        elements.append(Paragraph(f"<b>{label}:</b> {value}", value_style))
    
    # Планируемые мероприятия
    if fault.get('planned_actions'):
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("Планируемые мероприятия", section_style))
        elements.append(Paragraph(fault['planned_actions'], value_style))
    
    # Связанные статьи
    if fault.get('linked_knowledge'):
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("Связанные статьи", section_style))
        for article in fault.get('linked_knowledge', []):
            elements.append(Paragraph(f"• {article.get('title', '')}", value_style))
    
    # Клоны
    if fault.get('clones'):
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("Клоны", section_style))
        for clone in fault.get('clones', []):
            elements.append(Paragraph(f"• #{clone.get('id', '')} {clone.get('title', '')}", value_style))
    
    # Родительская неисправность
    if fault.get('parent_fault'):
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph("Родительская неисправность", section_style))
        parent = fault['parent_fault']
        elements.append(Paragraph(f"#{parent.get('id', '')} {parent.get('title', '')}", value_style))
    
    # Подвал
    elements.append(Spacer(1, 0.3*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elements.append(Paragraph("Система отслеживания неисправностей АСУ ТП", footer_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer