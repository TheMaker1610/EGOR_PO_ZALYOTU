from datetime import datetime
from pydantic import BaseModel, Field


class CalculationInput(BaseModel):
    total_load_mw: float = Field(..., gt=0, description="Электрическая нагрузка ТЭС, МВт")
    num_blocks: int = Field(..., ge=1, le=20, description="Количество работающих блоков")
    temp_c: float = Field(..., ge=-50, le=60, description="Температура наружного воздуха, °C")
    humidity: float = Field(..., ge=0, le=100, description="Влажность, %")
    wind_speed: float = Field(..., ge=0, description="Скорость ветра, м/с")
    wind_dir: float = Field(..., ge=0, le=360, description="Направление ветра, градусы")
    nominal_power_per_block: float = Field(300.0, gt=0, description="Номинальная мощность блока, МВт")
    nominal_efficiency: float = Field(0.38, gt=0, le=1, description="Номинальный КПД (доли единицы)")
    own_needs_coeff: float = Field(0.05, ge=0, le=0.3, description="Коэффициент собственных нужд")
    beta: float = Field(0.4, ge=0, le=1, description="Коэффициент снижения КПД при недогрузке")


class ChartPoint(BaseModel):
    temp_c: float
    efficiency_netto_pct: float
    fuel_consumption: float


class CalculationResult(BaseModel):
    load_per_block: float
    block_efficiency_pct: float
    efficiency_brutto_pct: float
    own_needs_power_mw: float
    own_needs_pct: float
    efficiency_netto_pct: float
    fuel_consumption: float
    chart_data: list[ChartPoint]
    record_id: int


class CalculationHistoryItem(BaseModel):
    id: int
    created_at: datetime
    total_load_mw: float
    num_blocks: int
    temp_c: float
    efficiency_netto_pct: float
    fuel_consumption: float

    class Config:
        from_attributes = True
