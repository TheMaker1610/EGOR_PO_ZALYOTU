import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_password_changed
from core.math_engine import analyze_load_distribution
from database.engine import get_db
from database.models import User
from schemas.calculation import CalculationInput, CalculationResult, CalculationHistoryItem, ChartPoint
from services.calc_service import CalcService
from ё.middleware import limiter, extract_headers

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
    hdrs = extract_headers(request)
    svc = CalcService(db)
    data = svc.calculate(body.model_dump(), user_id=current_user.id,
                         username=current_user.username, ip=ip, headers=hdrs)
    result = data["result"]
    chart_raw = data["chart_data"]
    return CalculationResult(
        **result,
        chart_data=[ChartPoint(**p) for p in chart_raw],
        record_id=data["record_id"],
    )


@router.post("/blocks-analysis")
def blocks_analysis(
    body: CalculationInput,
    current_user: User = Depends(require_password_changed),
):
    rows = analyze_load_distribution(
        total_load_mw=body.total_load_mw,
        temp_c=body.temp_c,
        humidity=body.humidity,
        wind_speed=body.wind_speed,
        wind_dir=body.wind_dir,
        nominal_power_per_block=body.nominal_power_per_block,
        nominal_efficiency=body.nominal_efficiency,
        own_needs_coeff=body.own_needs_coeff,
        beta=body.beta,
    )
    return rows


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
