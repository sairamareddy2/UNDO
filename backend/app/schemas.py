import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# --- Action & Plan Schemas ---

class PlanCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="Natural language request or voice command")


class ActionApprovalRequest(BaseModel):
    approved: bool = Field(..., description="True to approve execution, False to reject")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes or reason for approval/rejection")


class ActionResponse(BaseModel):
    id: str
    plan_id: str
    action_type: str
    title: str
    parameters: Dict[str, Any]
    policy_decision: str  # ALLOW, REQUIRE_APPROVAL, BLOCK
    policy_reason: str
    status: str          # PENDING, APPROVED, REJECTED, EXECUTED, REVERSED, BLOCKED, FAILED
    is_reversible: bool
    approval_decision: Optional[str] = None
    approval_notes: Optional[str] = None
    approval_decided_at: Optional[datetime.datetime] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime.datetime
    executed_at: Optional[datetime.datetime] = None
    reversed_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ActionPlanResponse(BaseModel):
    id: str
    prompt: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    actions: List[ActionResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Simulated Application State Schemas ---

class GroceryItemSchema(BaseModel):
    id: int
    name: str
    quantity: int
    category: str
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ReminderSchema(BaseModel):
    id: int
    title: str
    remind_at: str
    priority: str
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class DoorLockSchema(BaseModel):
    id: str
    name: str
    is_locked: bool
    last_changed_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationStateResponse(BaseModel):
    groceries: List[GroceryItemSchema]
    reminders: List[ReminderSchema]
    doors: List[DoorLockSchema]


class AuditEventResponse(BaseModel):
    id: int
    action_id: Optional[str]
    event_type: str
    details: Dict[str, Any]
    timestamp: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class HealthCheckResponse(BaseModel):
    status: str
    app: str
    environment: str
    database_connected: bool
    gemini_connected: bool = False
    gemini_model: Optional[str] = None
    timestamp: datetime.datetime
