import enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    MANAGER = "manager"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.MANAGER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    client = Column(String(200), nullable=True)
    station = Column(String(200), nullable=True)
    type = Column(String(200), nullable=True)
    unit = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связь с неисправностями (один проект → много неисправностей)
    faults = relationship("Fault", back_populates="project", cascade="all, delete-orphan")
    # Связь с историей
    history = relationship("ProjectHistory", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class ProjectHistory(Base):
    __tablename__ = "project_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    event_type = Column(String(50), nullable=False, default="field_change")  # creation, field_change, fault_added, fault_closed
    field = Column(String(50), nullable=True)
    old_value = Column(String(500), nullable=True)
    new_value = Column(String(500), nullable=True)
    author = Column(String(100), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="history")

    def __repr__(self):
        return f"<ProjectHistory(id={self.id}, project_id={self.project_id}, type='{self.event_type}')>"


class Fault(Base):
    __tablename__ = "faults"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), default="minor")
    status = Column(String(50), default="open")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    parent_fault_id = Column(Integer, ForeignKey("faults.id"), nullable=True)
    linked_knowledge_ids = Column(String(500), nullable=True, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связанные статьи базы знаний (ID через запятую)
    linked_knowledge_ids = Column(String(500), nullable=True, default="")

    # Связь с проектом (много неисправностей → один проект)
    project = relationship("Project", back_populates="faults")
    comments = relationship("FaultComment", back_populates="fault", cascade="all, delete-orphan")
    history = relationship("FaultHistory", back_populates="fault", cascade="all, delete-orphan")
    attachments = relationship("FaultAttachment", back_populates="fault", cascade="all, delete-orphan")
    
    # ✅ Связь с родительской неисправностью
    parent_fault = relationship("Fault", remote_side=[id], backref="clones")

    def __repr__(self):
            return f"<Fault(id={self.id}, title='{self.title[:30]}...')>"


class FaultComment(Base):
    __tablename__ = "fault_comments"

    id = Column(Integer, primary_key=True, index=True)
    fault_id = Column(Integer, ForeignKey("faults.id"), nullable=False)
    author = Column(String(100), nullable=False, default="system")
    content = Column(Text, nullable=False)
    is_internal = Column(Integer, default=0)  # 0 - публичный, 1 - внутренний
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    fault = relationship("Fault", back_populates="comments")

    def __repr__(self):
        return f"<FaultComment(id={self.id}, fault_id={self.fault_id})>"


class FaultHistory(Base):
    __tablename__ = "fault_history"

    id = Column(Integer, primary_key=True, index=True)
    fault_id = Column(Integer, ForeignKey("faults.id"), nullable=False)
    event_type = Column(String(50), nullable=False, default="field_change")  # field_change, creation, comment
    field = Column(String(50), nullable=True)  # status, severity, project_id, title, description
    old_value = Column(String(500), nullable=True)
    new_value = Column(String(500), nullable=True)
    author = Column(String(100), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    fault = relationship("Fault", back_populates="history")

    def __repr__(self):
        return f"<FaultHistory(id={self.id}, fault_id={self.fault_id}, type='{self.event_type}')>"


class FaultAttachment(Base):
    __tablename__ = "fault_attachments"

    id = Column(Integer, primary_key=True, index=True)
    fault_id = Column(Integer, ForeignKey("faults.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # размер в байтах
    file_type = Column(String(100), nullable=True)  # mime type
    description = Column(String(500), nullable=True)
    uploaded_by = Column(String(100), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    fault = relationship("Fault", back_populates="attachments")

    def __repr__(self):
        return f"<FaultAttachment(id={self.id}, filename='{self.filename}')>"


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)  # Markdown формат
    tags = Column(String(200), nullable=True)  # Теги через запятую
    category = Column(String(100), nullable=True)  # Категория: инструкция, решение, документация
    author = Column(String(100), nullable=False, default="system")
    related_faults = Column(String(500), nullable=True)  # ID неисправностей через запятую
    is_published = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, title='{self.title[:30]}...')>"