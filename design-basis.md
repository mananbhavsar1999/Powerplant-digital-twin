# Design Basis — 100-House Steam Power Plant Digital Twin

## 1. Project Intent
A digital twin of a small, simple condensing steam power plant sized to supply
electricity to approximately 100 residential houses. The project combines a
validated thermodynamic simulation, a 3D model of the plant, and a live
interactive dashboard with anomaly detection — built as an engineering
portfolio piece demonstrating end-to-end system thinking from first-principles
thermodynamics through to deployment.

## 2. Plant Sizing Logic
Average household electrical demand (with diversity factor applied across
appliances, lighting, fans) is taken as ~0.5–1 kW continuous. For 100 houses,
applying a diversity factor of ~0.6–0.7 to peak demand gives a target
continuous electrical output of:

**Target electrical output: 75 kW**

This sits at the small end of where simple (non-combined-cycle) steam turbines
are commercially used — single-stage industrial steam turbines are produced
from as low as ~50 kW up to several hundred MW for utility-scale plants.

## 3. Cycle Selection
**Simple condensing Rankine cycle** (no reheat, no feedwater heating):

```
Boiler → Turbine → Condenser → Feedwater Pump → (back to Boiler)
```

Rejected alternatives:
- **Back-pressure / cogeneration turbine** — only makes sense with a co-located
  process heat user (e.g. industrial process steam demand). Adds complexity
  with no benefit for a pure-electricity case.
- **Combined cycle (gas turbine + HRSG + steam turbine)** — requires a gas
  turbine and compressor, unnecessary at this scale and outside the project's
  steam-plant focus.

**No compressor is used.** Compressors belong to gas turbine (Brayton) cycles.
The equivalent component in this cycle is the **feedwater pump**, which
re-pressurizes the condensate (liquid) back to boiler pressure — requiring far
less power than gas compression would.

## 4. Design Point Assumptions

| Parameter | Value | Basis |
|---|---|---|
| Electrical output | 75 kW | Sized for 100 houses (Section 2) |
| Boiler pressure | 15 bar(a) | Typical small industrial boiler pressure |
| Turbine inlet temperature | 250°C | Slight superheat, protects turbine blades from wet-steam erosion |
| Condenser pressure | 0.2 bar(a) | Achievable with air-cooled or small cooling tower condenser (~60°C) |
| Turbine isentropic efficiency | 65% | Realistic for small single-stage turbines; reference data shows small single-stage units can run as low as 50% |
| Generator efficiency | 92% | Typical small synchronous generator |
| Feed pump isentropic efficiency | 75% | Typical small centrifugal feed pump |

## 5. Validated Heat Balance Results
Calculated using IAPWS-IF97 steam tables (`iapws` Python library) — see
`/sim/rankine_cycle.py`.

| Parameter | Value |
|---|---|
| Steam mass flow rate | 0.177 kg/s (~637 kg/hr) |
| Turbine shaft output | 81.9 kW |
| Feed pump power consumption | 0.35 kW |
| Net electrical output | 75.0 kW |
| Boiler thermal duty | 471.6 kW (0.472 MW) |
| Condenser heat rejection | 390.0 kW |
| **Overall cycle efficiency** | **15.9%** |

### Efficiency sanity check
This efficiency may look low compared to large utility steam plants
(30–45%+), but it is realistic for this scale:
- Large industrial steam turbines (Siemens Energy range: 2–250 MW) achieve
  30%+ overall efficiency, but only with reheat, multi-stage expansion, and
  feedwater heating — none of which is economical at 75 kW.
- Steam turbines below ~500 kW are rarely used in simple cycle form at all;
  single-stage units in this range can have isentropic efficiencies as low as
  50%, meaning our 65% assumption is on the optimistic side, not pessimistic.
- The result is consistent with the well-documented penalty of scaling steam
  turbines down — losses (windage, leakage, wet-steam exhaust) that are
  negligible in large turbines dominate at small scale.

### Documented improvement paths (not implemented in v1, noted for credibility)
- Adding a single open feedwater heater would recover some condensate
  preheating loss, raising efficiency by a few percentage points.
- Increasing boiler pressure/superheat (with matched turbine blade design)
  would increase the enthalpy drop available per kg of steam.
- A multi-stage turbine would improve isentropic efficiency at the cost of
  capital complexity — not justified at 75 kW.

## 6. Equipment List

| Equipment | Function |
|---|---|
| Boiler / steam generator | Converts feedwater to superheated steam at 15 bar / 250°C |
| Single-stage condensing turbine | Expands steam, drives generator via direct coupling |
| Generator | Converts turbine shaft work to electrical output (92% efficiency) |
| Condenser | Condenses turbine exhaust steam to liquid at 0.2 bar / ~60°C |
| Feedwater pump | Returns condensate to boiler pressure (15 bar) |
| Piping & valves | Interconnects all equipment, includes isolation/control valves |

## 7. Dynamic Behavior Assumptions
See `/sim/transient_model.py`. State variables (RPM, boiler pressure, load)
follow first-order lag dynamics rather than instantaneous steady-state jumps:

| Variable | Time constant (τ) | Rationale |
|---|---|---|
| Turbine/generator RPM | 4 s | Rotating inertia of turbine-generator shaft |
| Boiler pressure | 12 s | Thermal mass of boiler water/steam inventory |
| Electrical load | 2 s | Grid demand response, faster than mechanical/thermal lags |

## 8. Fault Scenarios Modeled
Used for dashboard fault-injection demos and ML training data
(`/sim/generate_sensor_data.py`):

| Fault | Description |
|---|---|
| `low_boiler_pressure` | Boiler pressure setpoint drops to 60% of design |
| `turbine_trip` | Load setpoint drops to 0% (simulated turbine/generator trip) |
| `overload` | Load setpoint rises to 115% of design (sustained overload) |

## 9. Validation Method
The browser-based JavaScript physics model (Week 3) will be cross-validated
against this Python reference model by running identical inputs through both
and comparing outputs — results and deviation will be documented in
`/web/VALIDATION.md` once built.

## 10. Sources
- Industry data on small steam turbine efficiency ranges referenced from
  UnderstandingCHP.com (CHP applications guide) and Siemens Energy steam
  turbine product documentation, accessed June 2026.
