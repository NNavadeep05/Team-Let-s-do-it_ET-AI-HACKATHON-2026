# P&ID — Cooling Water System (CWS-01)

**Document ID:** PID-CWS-01
**Doc type:** pid
**Effective date:** 2020-01-20
**Plant / Unit:** Riverside Plant / Cooling Water Unit

> This is a text proxy for the P&ID drawing used in the demo. In production the actual PNG/PDF is parsed by the vision model (`12 §P&ID`). The equipment, instruments, and connections below are what that extractor should return, so the graph topology supports the impact/blast-radius demo.

## Equipment
| Tag | Type | Label |
|---|---|---|
| P-101 | pump | Cooling Water Pump A (primary) |
| P-103 | pump | Cooling Water Pump B (standby) |
| V-12 | valve | P-101 discharge isolation |
| V-14 | valve | P-103 discharge isolation |
| HX-3 | heat_exchanger | Process cooler |
| TK-1 | tank | Cooling water sump |
| CT-1 | cooling_tower | Cooling tower |

## Instruments
| Tag | Type | On |
|---|---|---|
| PT-204 | pressure_transmitter | P-101 discharge (line L-12) |
| TT-209 | temperature_transmitter | P-101 bearing |
| FT-220 | flow_transmitter | line L-30 to HX-3 |
| LIC-101 | level_controller | TK-1 |

## Connections (process flow)
| From | To | Line | Flow |
|---|---|---|---|
| TK-1 | P-101 | L-10 | suction |
| TK-1 | P-103 | L-11 | suction |
| P-101 | V-12 | L-12 | process |
| P-103 | V-14 | L-13 | process |
| V-12 | HX-3 | L-30 | process |
| V-14 | HX-3 | L-30 | process |
| HX-3 | CT-1 | L-40 | return |
| CT-1 | TK-1 | L-50 | return |

> **DEMO NOTE:** P-101 → V-12 → HX-3 is the critical path. Taking P-101 down affects HX-3 (and any process the cooler serves) unless standby P-103 picks up the load — exactly what the Maintenance agent's impact/blast-radius analysis should surface. P-101 also scores high on GDS betweenness (it sits on the main flow path), so it appears in the dashboard "critical hubs" card.
