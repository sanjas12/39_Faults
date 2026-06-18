from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship  # Добавляем для связей
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
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связь с неисправностями (один проект → много неисправностей)
    faults = relationship("Fault", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"

class Fault(Base):
    __tablename__ = "faults"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), default="minor")  # critical, major, minor, trivial
    status = Column(String(50), default="open")    # open, in_progress, review, closed
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # Связь с проектом
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # Когда закрыта
    
    # Связь с проектом (много неисправностей → один проект)
    project = relationship("Project", back_populates="faults")
    
    def __repr__(self):
        return f"<Fault(id={self.id}, title='{self.title[:30]}...')>"