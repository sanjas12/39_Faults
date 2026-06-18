from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    client = Column(String(200), nullable=True)
    type = Column(String(200), nullable=True)
    unit = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # Добавили
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class Fault(Base):
    __tablename__ = "faults"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    # Добавляем значения по умолчанию прямо в модель
    severity = Column(String(50), nullable=False, server_default="minor")
    status = Column(String(50), nullable=False, server_default="open")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())