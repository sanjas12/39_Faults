from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

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
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связь с проектом (много неисправностей → один проект)
    project = relationship("Project", back_populates="faults")
    comments = relationship("FaultComment", back_populates="fault", cascade="all, delete-orphan")
    
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
    field = Column(String(50), nullable=False)  # status, severity, project_id
    old_value = Column(String(200), nullable=True)
    new_value = Column(String(200), nullable=True)
    author = Column(String(100), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), server_default=func.now())