# core/models.py

class Project(Base):          # "Проект" из вашего UX
    name: str
    description: str
    client: str
    created_at: datetime

class Unit(Base):             # Система автоматики
    name: str
    project_id: int (FK)      # Связь с проектом
    location: str
    type: str  # PLC, SCADA, CNC, Robot

class Fault(Base):            # Неисправность (Jira issue)
    title: str
    description: str
    severity: str  # Critical, Major, Minor, Trivial
    status: str    # Backlog → InProgress → Review → Done
    unit_id: int (FK)
    assignee_id: int (FK to User)
    reporter_id: int (FK)
    created_at: datetime
    sla_deadline: datetime    # Для автоэскалации
    resolved_at: datetime

class FaultComment(Base):     # Комментарии + история (Jira-лента)
    fault_id: int
    author_id: int
    content: str
    created_at: datetime
    is_internal: bool  # Внутренний комментарий (только инженерам)

class KnowledgeBase(Base):    # ⭐ База знаний (ваше преимущество)
    title: str
    content: str  # Markdown формат
    tags: list[str]  # теги: "PLC-ошибка", "датчик давления"
    related_faults: list[int]  # Связь с реальными неисправностями
    related_units: list[int]   # Для каких систем
    author_id: int
    created_at: datetime
    updated_at: datetime
    is_published: bool

class KBArticleVersion(Base):  # История изменений статьи
    article_id: int
    version: int
    content: str
    changed_by: int
    changed_at: datetime