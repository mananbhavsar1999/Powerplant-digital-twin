"""
Digital Twin - 100-House Steam Power Plant
Steady-state Rankine cycle heat balance model.

Cycle: Boiler -> Turbine -> Condenser -> Feedwater Pump -> (back to Boiler)
Uses IAPWS-IF97 steam tables (industry standard) via the `iapws` library.
"""

from iapws import IAPWS97

# ---------------------------------------------------------------
# DESIGN BASIS (inputs)
# ---------------------------------------------------------------
P_BOILER = 15.0        # bar(a) - boiler/turbine inlet pressure
T_BOILER = 250.0 + 273.15   # K - turbine inlet temperature (slight superheat)
P_COND = 0.2           # bar(a) - condenser pressure

ETA_TURBINE = 0.65     # isentropic efficiency, small single-stage turbine
ETA_GEN = 0.92         # generator efficiency
ETA_PUMP = 0.75        # feed pump isentropic efficiency

TARGET_ELEC_KW = 75.0  # target electrical output


def solve_cycle(target_elec_kw=TARGET_ELEC_KW):
    # --- State 1: Turbine inlet (boiler outlet) ---
    s1 = IAPWS97(P=P_BOILER / 10, T=T_BOILER)  # iapws uses MPa
    h1 = s1.h        # kJ/kg
    s1_entropy = s1.s  # kJ/kg-K

    # --- State 2s: Isentropic expansion to condenser pressure ---
    s2s = IAPWS97(P=P_COND / 10, s=s1_entropy)
    h2s = s2s.h

    # --- State 2: Actual turbine outlet (accounting for isentropic eff.) ---
    h2 = h1 - ETA_TURBINE * (h1 - h2s)
    s2 = IAPWS97(P=P_COND / 10, h=h2)

    # --- State 3: Condenser outlet (saturated liquid at P_COND) ---
    s3 = IAPWS97(P=P_COND / 10, x=0)  # saturated liquid
    h3 = s3.h

    # --- State 4: Feedwater pump outlet (back to boiler pressure) ---
    v3 = s3.v  # specific volume, m3/kg
    # ideal pump work (incompressible liquid approx)
    wp_ideal = v3 * (P_BOILER - P_COND) * 100  # kJ/kg (bar*m3/kg *100 = kJ/kg)
    wp_actual = wp_ideal / ETA_PUMP
    h4 = h3 + wp_actual

    # --- Specific work & heat ---
    w_turbine = h1 - h2          # kJ/kg, turbine specific work
    w_pump = wp_actual           # kJ/kg, pump specific work (consumed)
    w_net = w_turbine - w_pump   # kJ/kg, net cycle work
    q_boiler = h1 - h4           # kJ/kg, heat added in boiler
    q_condenser = h2 - h3        # kJ/kg, heat rejected in condenser

    # --- Solve mass flow for target electrical output ---
    # electrical_kW = mdot * w_turbine * eta_gen - pump_power
    # pump_power = mdot * w_pump  (driven off same shaft/motor, small)
    # => mdot * (w_turbine*eta_gen - w_pump) = target_elec_kw
    mdot = target_elec_kw / (w_turbine * ETA_GEN - w_pump)  # kg/s

    turbine_shaft_kw = mdot * w_turbine
    pump_power_kw = mdot * w_pump
    elec_kw = turbine_shaft_kw * ETA_GEN - pump_power_kw
    boiler_duty_kw = mdot * q_boiler
    condenser_duty_kw = mdot * q_condenser

    cycle_efficiency = elec_kw / boiler_duty_kw

    results = {
        "state_points": {
            "1_turbine_inlet": {"P_bar": P_BOILER, "T_C": T_BOILER - 273.15, "h_kJ/kg": round(h1, 1), "s_kJ/kgK": round(s1_entropy, 4)},
            "2_turbine_outlet": {"P_bar": P_COND, "h_kJ/kg": round(h2, 1), "x_quality": round(s2.x, 3)},
            "3_condenser_outlet": {"P_bar": P_COND, "h_kJ/kg": round(h3, 1), "T_C": round(s3.T - 273.15, 1)},
            "4_pump_outlet": {"P_bar": P_BOILER, "h_kJ/kg": round(h4, 1)},
        },
        "specific_energy_kJ_per_kg": {
            "turbine_work": round(w_turbine, 1),
            "pump_work": round(w_pump, 2),
            "net_work": round(w_net, 1),
            "boiler_heat": round(q_boiler, 1),
            "condenser_heat": round(q_condenser, 1),
        },
        "mass_flow_kg_s": round(mdot, 3),
        "power_kW": {
            "turbine_shaft": round(turbine_shaft_kw, 1),
            "pump_consumption": round(pump_power_kw, 2),
            "electrical_output": round(elec_kw, 1),
        },
        "boiler_duty_kW": round(boiler_duty_kw, 1),
        "boiler_duty_MW": round(boiler_duty_kw / 1000, 3),
        "condenser_duty_kW": round(condenser_duty_kw, 1),
        "cycle_efficiency_pct": round(cycle_efficiency * 100, 2),
    }
    return results


def print_heat_balance(results):
    print("=" * 60)
    print("  STEAM PLANT HEAT BALANCE - 100 HOUSE DIGITAL TWIN")
    print("=" * 60)
    print("\n-- State Points --")
    for name, sp in results["state_points"].items():
        print(f"  {name}: {sp}")

    print("\n-- Specific Energy (per kg steam) --")
    for k, v in results["specific_energy_kJ_per_kg"].items():
        print(f"  {k}: {v} kJ/kg")

    print(f"\n-- Mass Flow Rate: {results['mass_flow_kg_s']} kg/s --")

    print("\n-- Power --")
    for k, v in results["power_kW"].items():
        print(f"  {k}: {v} kW")

    print(f"\n-- Boiler Duty: {results['boiler_duty_kW']} kW ({results['boiler_duty_MW']} MW) --")
    print(f"-- Condenser Duty: {results['condenser_duty_kW']} kW --")
    print(f"\n>>> Overall Cycle Efficiency: {results['cycle_efficiency_pct']}% <<<")
    print("=" * 60)


def solve_cycle_at_load(load_fraction):
    """Solve cycle at a given fraction of design electrical output (0.0-1.2)."""
    target_kw = TARGET_ELEC_KW * max(load_fraction, 0.01)
    return solve_cycle(target_elec_kw=target_kw)


if __name__ == "__main__":
    results = solve_cycle()
    print_heat_balance(results)
