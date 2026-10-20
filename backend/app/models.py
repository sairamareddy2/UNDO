import datetime
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class ActionPlan(Base):
    __tablename__ = "action_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prompt = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    actions = relationship("Action", back_populates="plan", cascade="all, delete-orphan", order_by="Action.created_at")


class Action(Base):
    __tablename__ = "actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    plan_id = Column(String(36), ForeignKey("action_plans.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    parameters = Column(JSON, nullable=False, default=dict)

    # Deterministic Policy evaluation
    policy_decision = Column(String(32), nullable=False)  # ALLOW, REQUIRE_APPROVAL, BLOCK
    policy_reason = Column(Text, nullable=False)

    # Lifecycle status: PENDING, APPROVED, REJECTED, EXECUTED, REVERSED, BLOCKED, FAILED
    status = Column(String(32), nullable=False, default="PENDING")
    is_reversible = Column(Boolean, nullable=False, default=False)

    # Human-in-the-loop governance
    approval_decision = Column(String(32), nullable=True)  # APPROVED, REJECTED
    approval_notes = Column(Text, nullable=True)
    approval_decided_at = Column(DateTime(timezone=True), nullable=True)

    # Reversibility & Audit state snapshots
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    execution_result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    reversed_at = Column(DateTime(timezone=True), nullable=True)

    plan = relationship("ActionPlan", back_populates="actions")
    audit_events = relationship("AuditEvent", back_populates="action", cascade="all, delete-orphan")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(String(36), ForeignKey("actions.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(64), nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime(timezone=True), default=utc_now)

    action = relationship("Action", back_populates="audit_events")


# --- Simulated Application State Tables ---

class GroceryItem(Base):
    __tablename__ = "simulated_groceries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    category = Column(String(64), nullable=False, default="General")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class Reminder(Base):
    __tablename__ = "simulated_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    remind_at = Column(String(64), nullable=False)
    priority = Column(String(32), nullable=False, default="medium")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class DoorLock(Base):
    __tablename__ = "simulated_doors"

    id = Column(String(64), primary_key=True)  # e.g., "front_door", "back_door", "garage_entry"
    name = Column(String(128), nullable=False)
    is_locked = Column(Boolean, nullable=False, default=True)
    last_changed_at = Column(DateTime(timezone=True), default=utc_now)
