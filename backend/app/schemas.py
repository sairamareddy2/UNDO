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


# --- Safety Simulator Schemas ---

class SafetySimulationRequest(BaseModel):
    action_id: Optional[str] = Field(None, description="ID of an existing planned action to simulate")
    action_type: Optional[str] = Field(None, description="Action type if simulating an ad-hoc action")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parameters for the action")
    title: Optional[str] = Field(None, description="Optional title or display name for the action")


class FailureScenarioResult(BaseModel):
    name: str
    category: str
    status: str  # "PASSED", "FAILED", "WARNING", "UNSUPPORTED"
    expected: str
    observed: str


class ProposedChange(BaseModel):
    target: str
    change_type: str  # "INSERT", "UPDATE", "DELETE", "BLOCKED", "NONE"
    description: str
    affected_records: int
    details: Dict[str, Any] = Field(default_factory=dict)


class ReversibilityReport(BaseModel):
    result: str  # "VERIFIED_REVERSIBLE", "NOT_REVERSIBLE", "ROLLBACK_FAILED", "NOT_TESTED"
    rollback_tested: bool
    state_restored: bool
    recovery_method: str
    unverified_fields: List[str] = Field(default_factory=list)


class SafetyReportResponse(BaseModel):
    simulation_id: str
    action_id: Optional[str] = None
    action_type: str
    title: str
    parameters: Dict[str, Any]
    overall_status: str  # "SAFE IN SIMULATION", "WARNINGS FOUND", "BLOCKED BY POLICY", "SIMULATION FAILED", "ROLLBACK UNVERIFIED"
    risk_level: str      # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    risk_rationale: str
    policy_decision: str # "ALLOW", "REQUIRE_APPROVAL", "BLOCK"
    policy_reason: str
    requires_approval: bool
    initial_state_summary: Dict[str, Any]
    proposed_changes: List[ProposedChange]
    validation_results: Dict[str, Any]
    failure_scenarios: List[FailureScenarioResult]
    reversibility: ReversibilityReport
    warnings: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    timestamp: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
