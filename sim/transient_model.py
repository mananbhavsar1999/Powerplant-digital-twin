"""
Digital Twin - Transient Response Model

Adds first-order dynamic behavior on top of the steady-state Rankine cycle
solution: turbine RPM, boiler pressure, and load respond to setpoint changes
with realistic time lags instead of jumping instantly. This is what makes
fault-injection / load-change demos look like a real plant instead of a
slideshow of steady states.

Approach: each state variable (RPM, boiler pressure, load) chases its
steady-state target via a first-order lag:
    dx/dt = (x_target - x) / tau
discretized with simple Euler integration at a fixed timestep.
"""

import numpy as np
from rankine_cycle import solve_cycle_at_load, TARGET_ELEC_KW

# Design-point reference values (100% load)
DESIGN_RPM = 3000.0          # rev/min, typical small turbine-generator direct coupled at 50Hz
DESIGN_BOILER_PRESSURE = 15.0  # bar

# Time constants (seconds) - how fast each variable settles toward target
TAU_RPM = 4.0          # turbine/generator inertia - spins up/down over a few seconds
TAU_PRESSURE = 12.0    # boiler thermal mass - pressure changes are slower
TAU_LOAD = 2.0         # electrical load follows grid demand fairly quickly


class PlantState:
    """Holds the live, evolving state of the plant for the dynamic simulation."""

    def __init__(self):
        self.time_s = 0.0
        self.load_fraction = 1.0        # 0.0 - 1.2, fraction of design electrical output
        self.load_fraction_target = 1.0

        self.rpm = DESIGN_RPM
        self.rpm_target = DESIGN_RPM

        self.boiler_pressure = DESIGN_BOILER_PRESSURE
        self.boiler_pressure_target = DESIGN_BOILER_PRESSURE

        self.fault = None  # e.g. "turbine_trip", "low_boiler_pressure"

    def set_load_target(self, fraction):
        self.load_fraction_target = max(0.0, min(1.2, fraction))
        self.rpm_target = DESIGN_RPM * (0.97 + 0.03 * self.load_fraction_target)
        self.boiler_pressure_target = DESIGN_BOILER_PRESSURE * (0.95 + 0.05 * self.load_fraction_target)

    def trigger_fault(self, fault_name):
        """Simulate common fault scenarios for demo / ML training purposes."""
        self.fault = fault_name
        if fault_name == "turbine_trip":
            self.set_load_target(0.0)
        elif fault_name == "low_boiler_pressure":
            self.boiler_pressure_target = DESIGN_BOILER_PRESSURE * 0.6
        elif fault_name == "overload":
            self.set_load_target(1.15)
        elif fault_name == "clear":
            self.fault = None
            self.set_load_target(1.0)

    def step(self, dt=1.0):
        """Advance the plant state by dt seconds using first-order lag dynamics."""
        self.load_fraction += (self.load_fraction_target - self.load_fraction) * (dt / TAU_LOAD)
        self.rpm += (self.rpm_target - self.rpm) * (dt / TAU_RPM)
        self.boiler_pressure += (self.boiler_pressure_target - self.boiler_pressure) * (dt / TAU_PRESSURE)
        self.time_s += dt

    def snapshot(self, with_heat_balance=False):
        data = {
            "time_s": round(self.time_s, 1),
            "load_fraction": round(self.load_fraction, 4),
            "rpm": round(self.rpm, 1),
            "boiler_pressure_bar": round(self.boiler_pressure, 3),
            "fault": self.fault,
        }
        if with_heat_balance:
            hb = solve_cycle_at_load(max(self.load_fraction, 0.01))
            data["electrical_kW"] = hb["power_kW"]["electrical_output"]
            data["boiler_duty_kW"] = hb["boiler_duty_kW"]
            data["cycle_efficiency_pct"] = hb["cycle_efficiency_pct"]
        return data


if __name__ == "__main__":
    # Demo: step load down to 50%, hold, then trigger a turbine trip
    plant = PlantState()
    plant.set_load_target(1.0)

    print("t=0s   -> steady at 100% load")
    for _ in range(10):
        plant.step(dt=1.0)

    print("t=10s  -> ramping load down to 50%")
    plant.set_load_target(0.5)
    for _ in range(15):
        plant.step(dt=1.0)
        print(plant.snapshot())

    print("t=25s  -> TURBINE TRIP triggered")
    plant.trigger_fault("turbine_trip")
    for _ in range(10):
        plant.step(dt=1.0)
        print(plant.snapshot())
