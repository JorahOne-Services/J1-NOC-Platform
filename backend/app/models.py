from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.sql import func

from ..app.database import Base


class Role(Base):
    __tablename__ = "roles"
    id = Integer(primary_key=True)
    name = String(255), nullable=False, unique=True
    slug = String(255), nullable=False, unique=True
    description = Text
    permissions = JSON, nullable=False, default={}
    is_system = Boolean, nullable=False, server_default="false"
    created_at = DateTime, server_default=func.now()
    updated_at = DateTime, server_default=func.now(), onupdate=func.now()


class Customer(Base):
    __tablename__ = "customers"
    id = Integer(primary_key=True)
    name = String(255), nullable=False
    slug = String(255), nullable=False, unique=True
    contact_email = String(255)
    contact_phone = String(255)
    address = Text
    tenant_id = String(255), nullable=False, server_default="default"
    is_active = Boolean, nullable=False, server_default="true"
    metadata = JSON, nullable=False, default={}
    created_at = DateTime, server_default=func.now()
    updated_at = DateTime, server_default=func.now(), onupdate=func.now()


class Site(Base):
    __tablename__ = "sites"
    id = Integer(primary_key=True)
    customer_id = Integer, nullable=False
    name = String(255), nullable=False
    location = Text
    timezone = String(64), nullable=False, server_default="UTC"
    metadata = JSON, nullable=False, default={}
    created_at = DateTime, server_default=func.now()
    updated_at = DateTime, server_default=func.now(), onupdate=func.now()


class User(Base):
    __tablename__ = "users"
    id = Integer(primary_key=True)
    email = String(255), unique=True
    username = String(255), unique=True
    hashed_password = String(255)
    full_name = String(255)
    role_id = Integer, nullable=False
    customer_id = Integer
    site_id = Integer
    is_active = Boolean, nullable=False, server_default="true"
    is_locked = Boolean, nullable=False, server_default="false"
    last_login_at = DateTime
    metadata = JSON, nullable=False, default={}
    created_at = DateTime, server_default=func.now()
    updated_at = DateTime, server_default=func.now(), onupdate=func.now()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Integer, primary_key=True, autoincrement=True
    actor_id = Integer
    actor_email = String(255)
    action = String(255), nullable=False
    target_type = String(255)
    target_id = Integer
    payload = JSON, default={}
    ip_address = String(64)
    user_agent = Text
    created_at = DateTime, server_default=func.now()
