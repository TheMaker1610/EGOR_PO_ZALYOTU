import json

from sqlalchemy.orm import Session

from core.math_engine import calc_tes_efficiency, analyze_temperature
from database.models import CalculationRecord
from services.audit_service import AuditService


class CalcService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def calculate(self, params: dict, user_id: int, username: str, ip: str = "127.0.0.1") -> dict:
        result = calc_tes_efficiency(
            total_load_mw=params["total_load_mw"],
            num_blocks=params["num_blocks"],
            temp_c=params["temp_c"],
            humidity=params["humidity"],
            wind_speed=params["wind_speed"],
            wind_dir=params["wind_dir"],
            nominal_power_per_block=params.get("nominal_power_per_block", 300.0),
            nominal_efficiency=params.get("nominal_efficiency", 0.38),
            own_needs_coeff=params.get("own_needs_coeff", 0.05),
            beta=params.get("beta", 0.4),
        )
        chart_data = analyze_temperature(
            total_load_mw=params["total_load_mw"],
            num_blocks=params["num_blocks"],
            humidity=params["humidity"],
            wind_speed=params["wind_speed"],
            wind_dir=params["wind_dir"],
            nominal_power_per_block=params.get("nominal_power_per_block", 300.0),
            nominal_efficiency=params.get("nominal_efficiency", 0.38),
            own_needs_coeff=params.get("own_needs_coeff", 0.05),
            beta=params.get("beta", 0.4),
        )

        record = CalculationRecord(
            user_id=user_id,
            input_json=json.dumps(params, ensure_ascii=False),
            result_json=json.dumps(result, ensure_ascii=False),
            chart_data_json=json.dumps(chart_data, ensure_ascii=False),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        self.audit.record(
            "CALCULATION", "calc_engine",
            username=username, user_id=user_id, ip_address=ip,
            details=f"load={params['total_load_mw']}MW blocks={params['num_blocks']} eta_netto={result['efficiency_netto_pct']}%"
        )

        return {"result": result, "chart_data": chart_data, "record_id": record.id}

    def history(self, user_id: int, limit: int = 50) -> list[CalculationRecord]:
        return (
            self.db.query(CalculationRecord)
            .filter_by(user_id=user_id)
            .order_by(CalculationRecord.created_at.desc())
            .limit(limit)
            .all()
        )

    def all_history(self, limit: int = 200) -> list[CalculationRecord]:
        return (
            self.db.query(CalculationRecord)
            .order_by(CalculationRecord.created_at.desc())
            .limit(limit)
            .all()
        )
