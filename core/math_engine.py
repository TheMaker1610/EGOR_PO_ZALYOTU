"""
Математическое ядро расчёта эффективности ТЭС.
Базируется на методах расчёта из Приложения 1.

Поправочные коэффициенты:
  k_temp   — поправка на температуру воздуха
  k_hum    — поправка на влажность
  k_wind   — поправка на скорость ветра
  k_wdir   — поправка на направление ветра
  k        — суммарный поправочный коэффициент

Выходные показатели:
  load_per_block       — нагрузка на блок, МВт
  block_efficiency     — КПД блока (доли ед.)
  efficiency_brutto    — КПД ТЭС брутто (доли ед.)
  own_needs_percent    — собственные нужды, %
  own_needs_power      — собственные нужды, МВт
  efficiency_netto     — КПД ТЭС нетто (доли ед.)
  fuel_consumption     — удельный расход условного топлива, г у.т./кВт·ч
"""
import numpy as np


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ПОПРАВКИ) — из Приложения 1
# ============================================================================

def temp_correction(temp_c: float) -> float:
    """Поправка на температуру воздуха."""
    if temp_c <= 15:
        return 1.0 + 0.003 * (15 - temp_c)
    return 1.0 - 0.002 * (temp_c - 15)


def humidity_correction(humidity: float) -> float:
    """Поправка на влажность."""
    if humidity <= 60:
        return 1.0
    return 1.0 - 0.0005 * (humidity - 60)


def wind_speed_correction(speed: float) -> float:
    """Поправка на скорость ветра (м/с)."""
    if speed <= 8:
        return 1.0 + 0.002 * speed
    return 1.0 + 0.002 * 8


def wind_direction_correction(direction_deg: float) -> float:
    """Поправка на направление ветра (градусы)."""
    angle = direction_deg % 360
    if 0 <= angle <= 45:       # ветер со стороны трубы (плохо)
        return 0.99
    elif 180 <= angle <= 225:  # встречный (хорошо)
        return 1.01
    return 1.00


def load_correction(current_power: float, nominal_power: float,
                    base_efficiency: float, beta: float = 0.4) -> float:
    """Поправка КПД на частичную нагрузку."""
    load_ratio = current_power / nominal_power
    if load_ratio >= 1:
        return base_efficiency
    return base_efficiency * (1 - beta * (1 - load_ratio) ** 2)


# ============================================================================
# ОСНОВНЫЕ РАСЧЁТНЫЕ ФУНКЦИИ — из Приложения 1
# ============================================================================

def calc_block_efficiency(
    power_mw: float,
    nominal_power: float,
    nominal_efficiency: float,
    temp_c: float,
    humidity: float,
    wind_speed: float,
    wind_dir: float,
    beta: float = 0.4,
) -> float:
    """
    Расчёт КПД одного блока с учётом всех факторов.

    Параметры:
      power_mw          — текущая нагрузка блока, МВт
      nominal_power     — номинальная мощность, МВт
      nominal_efficiency — номинальный КПД (0.38 = 38%)
      temp_c            — температура воздуха, °C
      humidity          — влажность, %
      wind_speed        — скорость ветра, м/с
      wind_dir          — направление ветра, градусы
      beta              — коэффициент снижения КПД при недогрузке (0.3–0.5)

    Возвращает: фактический КПД блока (доли единицы)
    """
    k = (temp_correction(temp_c) *
         humidity_correction(humidity) *
         wind_speed_correction(wind_speed) *
         wind_direction_correction(wind_dir))

    efficiency_at_nominal = nominal_efficiency * k
    return load_correction(power_mw, nominal_power, efficiency_at_nominal, beta)


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
    """
    Расчёт эффективности ТЭС.

    Возвращает словарь с результатами (все КПД в % для отображения).
    """
    load_per_block = total_load_mw / num_blocks

    overload_warning = None
    if load_per_block > nominal_power_per_block:
        overload_warning = (f"Блок перегружен: {load_per_block:.1f} > "
                            f"{nominal_power_per_block} МВт")
        load_per_block = nominal_power_per_block

    block_eff = calc_block_efficiency(
        load_per_block, nominal_power_per_block, nominal_efficiency,
        temp_c, humidity, wind_speed, wind_dir, beta,
    )

    total_power_brutto = num_blocks * load_per_block
    efficiency_brutto = block_eff

    # Собственные нужды с температурной поправкой
    own_needs = own_needs_coeff
    if temp_c > 25:
        own_needs += 0.005 * (temp_c - 25)
    elif temp_c < 0:
        own_needs += 0.003 * abs(temp_c)
    own_needs = min(own_needs, 0.30)

    own_needs_power = total_power_brutto * own_needs
    total_power_netto = total_power_brutto - own_needs_power
    efficiency_netto = efficiency_brutto * (1 - own_needs)
    efficiency_netto = max(efficiency_netto, 0.001)

    # Удельный расход условного топлива, г у.т./кВт·ч
    fuel_consumption = 123.0 / efficiency_netto

    result = {
        "load_per_block":        round(load_per_block, 2),
        "block_efficiency_pct":  round(block_eff * 100, 2),
        "efficiency_brutto_pct": round(efficiency_brutto * 100, 2),
        "own_needs_pct":         round(own_needs * 100, 2),
        "own_needs_power_mw":    round(own_needs_power, 2),
        "efficiency_netto_pct":  round(efficiency_netto * 100, 2),
        "fuel_consumption":      round(fuel_consumption, 2),
        "total_power_brutto_mw": round(total_power_brutto, 2),
        "total_power_netto_mw":  round(total_power_netto, 2),
    }
    if overload_warning:
        result["warning"] = overload_warning
    return result


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
    """
    Зависимость КПД нетто и расхода топлива от температуры (−20…+40 °C, шаг 5).
    """
    temps = np.arange(-20, 41, 5)
    points = []
    for t in temps:
        r = calc_tes_efficiency(
            total_load_mw, num_blocks, float(t), humidity,
            wind_speed, wind_dir,
            nominal_power_per_block, nominal_efficiency, own_needs_coeff, beta,
        )
        points.append({
            "temp_c": int(t),
            "efficiency_netto_pct": r["efficiency_netto_pct"],
            "fuel_consumption": r["fuel_consumption"],
        })
    return points


def analyze_load_distribution(
    total_load_mw: float,
    temp_c: float,
    humidity: float,
    wind_speed: float,
    wind_dir: float,
    nominal_power_per_block: float = 300.0,
    nominal_efficiency: float = 0.38,
    own_needs_coeff: float = 0.05,
    beta: float = 0.4,
    max_blocks: int = 6,
) -> list[dict]:
    """
    Анализ эффективности при разном количестве блоков (от 1 до max_blocks).
    Возвращает только варианты, при которых блоки не перегружены.
    """
    results = []
    for n in range(1, max_blocks + 1):
        load_per_block = total_load_mw / n
        if load_per_block > nominal_power_per_block:
            continue  # блок перегружен — пропускаем
        r = calc_tes_efficiency(
            total_load_mw, n, temp_c, humidity,
            wind_speed, wind_dir,
            nominal_power_per_block, nominal_efficiency, own_needs_coeff, beta,
        )
        results.append({
            "blocks":             n,
            "load_per_block_mw":  r["load_per_block"],
            "load_percent":       round(load_per_block / nominal_power_per_block * 100, 1),
            "efficiency_netto_pct": r["efficiency_netto_pct"],
            "fuel_consumption":   r["fuel_consumption"],
        })
    return results
