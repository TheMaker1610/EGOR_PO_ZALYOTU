import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_password_changed
from database.engine import get_db
from database.models import User
from schemas.calculation import CalculationInput, CalculationResult, CalculationHistoryItem, ChartPoint
from services.calc_service import CalcService
from ё.middleware import limiter

router = APIRouter(prefix="/calc", tags=["calc"])


@router.post("/run", response_model=CalculationResult)
@limiter.limit("60/minute")
def run_calculation(
    request: Request,
    body: CalculationInput,
    current_user: User = Depends(require_password_changed),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    svc = CalcService(db)
    data = svc.calculate(body.model_dump(), user_id=current_user.id,
                         username=current_user.username, ip=ip)
    result = data["result"]
    chart_raw = data["chart_data"]
    return CalculationResult(
        **result,
        chart_data=[ChartPoint(**p) for p in chart_raw],
        record_id=data["record_id"],
    )


@router.get("/history", response_model=list[CalculationHistoryItem])
def get_history(
    current_user: User = Depends(require_password_changed),
    db: Session = Depends(get_db),
):
    svc = CalcService(db)
    records = svc.history(current_user.id)
    result = []
    for r in records:
        inp = json.loads(r.input_json)
        res = json.loads(r.result_json)
        result.append(CalculationHistoryItem(
            id=r.id,
            created_at=r.created_at,
            total_load_mw=inp["total_load_mw"],
            num_blocks=inp["num_blocks"],
            temp_c=inp["temp_c"],
            efficiency_netto_pct=res["efficiency_netto_pct"],
            fuel_consumption=res["fuel_consumption"],
        ))
    return result
