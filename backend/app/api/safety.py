from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import SafetySimulationRequest, SafetyReportResponse
from app.services.safety_simulator import SafetySimulator

router = APIRouter()


@router.post("/safety/simulate", response_model=SafetyReportResponse, status_code=status.HTTP_200_OK)
def simulate_action_safety(
    payload: SafetySimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Test Before Execute: Evaluates a proposed action in an isolated temporary
    SQLite sandbox, projects database changes, runs deterministic failure scenarios,
    tests recovery/rollback, and returns a comprehensive safety report.
    Never modifies production application state or executes external side effects.
    """
    try:
        report = SafetySimulator.simulate_action(
            real_db=db,
            action_id=payload.action_id,
            action_type=payload.action_type,
            parameters=payload.parameters,
            title=payload.title,
        )
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Safety simulation internal error: {str(e)}",
        )
