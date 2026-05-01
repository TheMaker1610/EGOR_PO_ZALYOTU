"""
Математическое ядро расчёта эффективности ТЭС.

Формулы:
  k_temp   — поправка на температуру воздуха
  k_hum    — поправка на влажность
  k_wind   — поправка на скорость ветра
  k_wdir   — поправка на направление ветра
  k        — суммарный поправочный коэффициент
  η_block  — КПД блока с учётом нагрузки и поправок
  η_brutto — КПД ТЭС брутто
  α_own    — коэффициент собственных нужд с температурной поправкой
  η_netto  — КПД ТЭС нетто
  b        — удельный расход условного топлива, г у.т./кВт·ч
"""


def _k_temp(temp_c: float) -> float:
    if temp_c <= 15:
        return 1.0 + 0.003 * (15 - temp_c)
    return 1.0 - 0.002 * (temp_c - 15)


def _k_hum(humidity: float) -> float:
    if humidity <= 60:
        return 1.0
    return 1.0 - 0.0005 * (humidity - 60)


def _k_wind_speed(wind_speed: float) -> float:
    return 1.0 + 0.002 * min(wind_speed, 8.0)


def _k_wind_dir(wind_dir: float) -> float:
    if 0 <= wind_dir <= 45 or 315 < wind_dir <= 360:
        return 0.99
    if 180 <= wind_dir <= 225:
        return 1.01
    return 1.00


def calc_tes_efficiency(
    total_load_mw: float,
    num_blocks: int,
    temp_c: float,
    humidity: float,
    wind_speed: float,
    wind_dir: float,
    nominal_power_per_block: float = 300.0,
    nominal_efficiency: float = 0.38,
    own_needs_coeff: float = 0.05,
    beta: float = 0.4,
) -> dict:
    load_per_block = total_load_mw / num_blocks

    k = _k_temp(temp_c) * _k_hum(humidity) * _k_wind_speed(wind_speed) * _k_wind_dir(wind_dir)

    eta_nominal_corrected = nominal_efficiency * k

    rel_load = load_per_block / nominal_power_per_block
    rel_load = min(rel_load, 1.0)
    eta_block = eta_nominal_corrected * (1.0 - beta * (1.0 - rel_load) ** 2)
    eta_block = max(eta_block, 0.01)

    eta_brutto = eta_block

    # Собственные нужды с температурной поправкой
    if temp_c > 25:
        alpha_own = own_needs_coeff + 0.005 * (temp_c - 25)
    elif temp_c < 0:
        alpha_own = own_needs_coeff + 0.003 * abs(temp_c)
    else:
        alpha_own = own_needs_coeff
    alpha_own = min(alpha_own, 0.30)

    p_brutto = total_load_mw
    p_own = p_brutto * alpha_own
    p_netto = p_brutto - p_own

    eta_netto = eta_brutto * (1.0 - alpha_own)
    eta_netto = max(eta_netto, 0.01)

    fuel_consumption = 123.0 / eta_netto

    return {
        "load_per_block": round(load_per_block, 2),
        "block_efficiency_pct": round(eta_block * 100, 2),
        "efficiency_brutto_pct": round(eta_brutto * 100, 2),
        "own_needs_power_mw": round(p_own, 2),
        "own_needs_pct": round(alpha_own * 100, 2),
        "efficiency_netto_pct": round(eta_netto * 100, 2),
        "fuel_consumption": round(fuel_consumption, 2),
    }


def analyze_temperature(
    total_load_mw: float,
    num_blocks: int,
    humidity: float,
    wind_speed: float,
    wind_dir: float,
    nominal_power_per_block: float = 300.0,
    nominal_efficiency: float = 0.38,
    own_needs_coeff: float = 0.05,
    beta: float = 0.4,
) -> list[dict]:
    """Строит зависимость КПД нетто и расхода топлива от температуры (-20..+40 °C)."""
    points = []
    for t in range(-20, 45, 5):
        r = calc_tes_efficiency(
            total_load_mw, num_blocks, float(t), humidity,
            wind_speed, wind_dir,
            nominal_power_per_block, nominal_efficiency, own_needs_coeff, beta,
        )
        points.append({
            "temp_c": t,
            "efficiency_netto_pct": r["efficiency_netto_pct"],
            "fuel_consumption": r["fuel_consumption"],
        })
    return points
