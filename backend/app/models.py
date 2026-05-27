import uuid
import enum
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class Api(Base):
    __tablename__ = "apis"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    versions = relationship("SpecificationVersion", back_populates="api", cascade="all, delete-orphan")

class SpecificationVersion(Base):
    __tablename__ = "specification_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_id = Column(UUID(as_uuid=True), ForeignKey("apis.id", ondelete="CASCADE"))
    version = Column(String, nullable=False)
    specification = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    is_deprecated = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)

    api = relationship("Api", back_populates="versions")

# 1. Создаем класс ролей
class UserRole(str, enum.Enum):
    admin = "admin"
    service = "service"  # Для M2M интеграций
    viewer = "viewer"    # Обычный читатель документации

# 2. Создаем модель пользователя
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.viewer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)