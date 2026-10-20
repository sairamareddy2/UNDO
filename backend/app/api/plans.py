from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.models import utc_now
from app.schemas import PlanCreateRequest, ActionPlanResponse, ActionResponse
from app.planner.parser import ActionIntentParser
from app.policy.engine import PolicyEngine, PolicyDecision
from app.executor.executor import ActionExecutor, ActionExecutionError

router = APIRouter()


@router.post("/plans", response_model=ActionPlanResponse, status_code=status.HTTP_201_CREATED)
def create_action_plan(payload: PlanCreateRequest, db: Session = Depends(get_db)):
    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prompt cannot be empty."
        )

    # 1. Parse prompt into proposed action items
    candidates = ActionIntentParser.parse_prompt(prompt)

    # 2. Create the plan record
    plan = models.ActionPlan(prompt=prompt, status="PENDING")
    db.add(plan)
    db.flush()

    # 3. Deterministically evaluate each proposed action against security policy
    for action_type, title, raw_params in candidates:
        evaluation = PolicyEngine.evaluate(action_type, raw_params)

        final_params = evaluation.validated_params if evaluation.validated_params is not None else raw_params
        action_status = "BLOCKED" if evaluation.decision == PolicyDecision.BLOCK else "PENDING"

        action = models.Action(
            plan_id=plan.id,
            action_type=action_type,
            title=title,
            parameters=final_params,
            policy_decision=evaluation.decision,
            policy_reason=evaluation.reason,
            status=action_status,
            is_reversible=evaluation.is_reversible,
            created_at=utc_now(),
        )
        db.add(action)
        db.flush()

        # Audit event for policy evaluation
        audit = models.AuditEvent(
            action_id=action.id,
            event_type="POLICY_EVALUATED",
            details={
                "action_type": action_type,
                "decision": evaluation.decision,
                "reason": evaluation.reason,
                "parameters": final_params,
            },
            timestamp=utc_now(),
        )
        db.add(audit)

    db.commit()
    db.refresh(plan)
    return plan


@router.get("/plans", response_model=List[ActionPlanResponse])
def list_action_plans(db: Session = Depends(get_db)):
    plans = db.query(models.ActionPlan).order_by(models.ActionPlan.created_at.desc()).limit(50).all()
    return plans


@router.get("/plans/{plan_id}", response_model=ActionPlanResponse)
def get_action_plan(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(models.ActionPlan).filter(models.ActionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found.")
    return plan


@router.post("/plans/{plan_id}/execute", response_model=ActionPlanResponse)
def execute_eligible_plan_actions(plan_id: str, db: Session = Depends(get_db)):
    plan = db.query(models.ActionPlan).filter(models.ActionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found.")

    for action in plan.actions:
        # Eligible if ALLOW policy and PENDING, or REQUIRE_APPROVAL and APPROVED
        is_eligible = (
            (action.policy_decision == "ALLOW" and action.status == "PENDING") or
            (action.policy_decision == "REQUIRE_APPROVAL" and action.approval_decision == "APPROVED" and action.status == "APPROVED")
        )
        if is_eligible:
            try:
                ActionExecutor.execute_action(db, action)
            except ActionExecutionError:
                pass  # Error is tracked on action model

    db.commit()
    db.refresh(plan)
    return plan
