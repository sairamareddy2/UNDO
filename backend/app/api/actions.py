from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.models import utc_now
from app.schemas import ActionResponse, ActionApprovalRequest
from app.executor.executor import ActionExecutor, ActionExecutionError
from app.executor.undo import UndoManager, UndoError

router = APIRouter()


@router.get("/actions", response_model=List[ActionResponse])
def list_actions(
    plan_id: Optional[str] = Query(None, description="Filter actions by plan ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by action status"),
    policy_filter: Optional[str] = Query(None, alias="policy", description="Filter by policy decision"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Action)

    if plan_id:
        query = query.filter(models.Action.plan_id == plan_id)
    if status_filter:
        query = query.filter(models.Action.status == status_filter)
    if policy_filter:
        query = query.filter(models.Action.policy_decision == policy_filter)

    actions = query.order_by(models.Action.created_at.desc()).limit(100).all()
    return actions


@router.get("/actions/{action_id}", response_model=ActionResponse)
def get_action(action_id: str, db: Session = Depends(get_db)):
    action = db.query(models.Action).filter(models.Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action '{action_id}' not found.")
    return action


@router.post("/actions/{action_id}/approve", response_model=ActionResponse)
def approve_action(
    action_id: str,
    payload: Optional[ActionApprovalRequest] = None,
    db: Session = Depends(get_db)
):
    action = db.query(models.Action).filter(models.Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action '{action_id}' not found.")

    if action.policy_decision == "BLOCK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve blocked action. Policy violation: {action.policy_reason}"
        )

    if action.status in ("EXECUTED", "REVERSED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve action already in '{action.status}' state."
        )

    is_approved = payload.approved if payload else True
    notes = payload.notes if payload else None

    if is_approved:
        action.approval_decision = "APPROVED"
        action.status = "APPROVED"
        action.approval_notes = notes
        action.approval_decided_at = utc_now()

        audit = models.AuditEvent(
            action_id=action.id,
            event_type="ACTION_APPROVED",
            details={"approved_by": "user", "notes": notes},
            timestamp=action.approval_decided_at,
        )
        db.add(audit)
    else:
        action.approval_decision = "REJECTED"
        action.status = "REJECTED"
        action.approval_notes = notes
        action.approval_decided_at = utc_now()

        audit = models.AuditEvent(
            action_id=action.id,
            event_type="ACTION_REJECTED",
            details={"rejected_by": "user", "notes": notes},
            timestamp=action.approval_decided_at,
        )
        db.add(audit)

    db.commit()
    db.refresh(action)
    return action


@router.post("/actions/{action_id}/reject", response_model=ActionResponse)
def reject_action(
    action_id: str,
    payload: Optional[ActionApprovalRequest] = None,
    db: Session = Depends(get_db)
):
    rejection_notes = payload.notes if payload and payload.notes else "User manually rejected action."
    approval_payload = ActionApprovalRequest(approved=False, notes=rejection_notes)
    return approve_action(action_id=action_id, payload=approval_payload, db=db)


@router.post("/actions/{action_id}/execute", response_model=ActionResponse)
def execute_action(action_id: str, db: Session = Depends(get_db)):
    action = db.query(models.Action).filter(models.Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action '{action_id}' not found.")

    if action.status == "EXECUTED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action is already executed.")

    if action.policy_decision == "BLOCK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action is blocked by security policy: {action.policy_reason}"
        )

    if action.policy_decision == "REQUIRE_APPROVAL" and action.approval_decision != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action requires human approval before execution."
        )

    try:
        executed_action = ActionExecutor.execute_action(db, action)
        return executed_action
    except ActionExecutionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/actions/{action_id}/undo", response_model=ActionResponse)
def undo_action(action_id: str, db: Session = Depends(get_db)):
    action = db.query(models.Action).filter(models.Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action '{action_id}' not found.")

    try:
        reversed_action = UndoManager.undo_action(db, action)
        return reversed_action
    except UndoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
