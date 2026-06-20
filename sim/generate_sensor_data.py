"""
Digital Twin - Synthetic Sensor Data Generator

Runs the transient plant model over a long simulated period with realistic
operating variation (load changes, slow drift, sensor noise) and periodic
injected faults. Produces a labeled time-series dataset used to:
  1. Drive the "replay" feel of dashboards/demos
  2. Train the ML anomaly detection model (Week 4)

Output: CSV with columns:
  time_s, load_fraction, rpm, boiler_pressure_bar, electrical_kW,
  boiler_duty_kW, cycle_efficiency_pct, vibration_mm_s, bearing_temp_C,
  fault_label
"""

import csv
import random
import numpy as np
from transient_model import PlantState

random.seed(42)
np.random.seed(42)

DT = 1.0                # seconds per simulation step
DURATION_S = 3600 * 6    # 6 hours of simulated operation
SENSOR_NOISE_STD = {
    "rpm": 3.0,
    "boiler_pressure_bar": 0.05,
    "vibration_mm_s": 0.15,
    "bearing_temp_C": 0.8,
}

# Baseline healthy values for sensors not derived from the thermo model
BASE_VIBRATION_MM_S = 1.8   # typical healthy small-turbine vibration velocity
BASE_BEARING_TEMP_C = 65.0


def random_load_profile(t):
    """Simulate realistic daily load variation (e.g. evening peak) plus noise."""
    hour = (t / 3600.0) % 24
    daily_curve = 0.65 + 0.35 * np.sin((hour - 6) / 24 * 2 * np.pi - np.pi / 2) ** 2
    noise = np.random.normal(0, 0.02)
    return float(np.clip(daily_curve + noise, 0.3, 1.1))


FAULT_SCHEDULE = [
    # (start_s, duration_s, fault_name)
    (3600, 180, "low_boiler_pressure"),
    (7200, 90, "turbine_trip"),
    (14400, 240, "overload"),
]


def active_fault(t):
    for start, dur, name in FAULT_SCHEDULE:
        if start <= t < start + dur:
            return name
    return None


def generate_dataset(path="plant_sensor_data.csv"):
    plant = PlantState()
    rows = []

    fault_end_times = {start + dur: True for start, dur, _ in FAULT_SCHEDULE}

    t = 0.0
    while t < DURATION_S:
        fault = active_fault(t)

        if fault and plant.fault != fault:
            plant.trigger_fault(fault)
        elif not fault and plant.fault is not None:
            plant.trigger_fault("clear")
        elif not fault:
            plant.set_load_target(random_load_profile(t))

        plant.step(dt=DT)

        # Derive electrical output etc. only every 5s to keep runtime fast,
        # then hold value between samples (sensors don't need sub-5s thermo resolution)
        if int(t) % 5 == 0:
            snap = plant.snapshot(with_heat_balance=True)
        else:
            snap = plant.snapshot(with_heat_balance=False)
            snap["electrical_kW"] = rows[-1]["electrical_kW"] if rows else 0.0
            snap["boiler_duty_kW"] = rows[-1]["boiler_duty_kW"] if rows else 0.0
            snap["cycle_efficiency_pct"] = rows[-1]["cycle_efficiency_pct"] if rows else 0.0

        # Add sensor noise
        rpm_noisy = snap["rpm"] + np.random.normal(0, SENSOR_NOISE_STD["rpm"])
        pressure_noisy = snap["boiler_pressure_bar"] + np.random.normal(0, SENSOR_NOISE_STD["boiler_pressure_bar"])

        # Vibration and bearing temp: correlate with load + fault state, not derived from thermo model
        vib_base = BASE_VIBRATION_MM_S + 0.6 * (snap["load_fraction"] - 1.0)
        if fault == "overload":
            vib_base += 1.2
        if fault == "turbine_trip":
            vib_base += 0.5
        vibration = max(0.1, vib_base + np.random.normal(0, SENSOR_NOISE_STD["vibration_mm_s"]))

        temp_base = BASE_BEARING_TEMP_C + 8 * (snap["load_fraction"] - 1.0)
        if fault == "overload":
            temp_base += 6
        bearing_temp = temp_base + np.random.normal(0, SENSOR_NOISE_STD["bearing_temp_C"])

        rows.append({
            "time_s": round(t, 1),
            "load_fraction": snap["load_fraction"],
            "rpm": round(rpm_noisy, 1),
            "boiler_pressure_bar": round(pressure_noisy, 3),
            "electrical_kW": snap["electrical_kW"],
            "boiler_duty_kW": snap["boiler_duty_kW"],
            "cycle_efficiency_pct": snap["cycle_efficiency_pct"],
            "vibration_mm_s": round(vibration, 3),
            "bearing_temp_C": round(bearing_temp, 2),
            "fault_label": fault if fault else "normal",
        })

        t += DT

    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} rows -> {path}")
    fault_counts = {}
    for r in rows:
        fault_counts[r["fault_label"]] = fault_counts.get(r["fault_label"], 0) + 1
    print("Label distribution:", fault_counts)
    return path


if __name__ == "__main__":
    generate_dataset()
