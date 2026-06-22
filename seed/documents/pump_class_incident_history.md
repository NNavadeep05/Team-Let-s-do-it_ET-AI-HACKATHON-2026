# Pump-Class Incident History (Centrifugal Pumps)

**Document ID:** HIST-PUMP-CLASS
**Doc type:** incident_report
**Equipment class:** centrifugal pump
**Effective date:** 2025-01-15
**Plant / Unit:** Riverside Plant

Historical mechanical-seal and bearing failures across centrifugal pumps at the site. Used to establish the failure-mode → cause pattern the RCA agent reasons over.

| Incident | Asset | Date | Failure mode | Symptoms | Root cause (closed) |
|---|---|---|---|---|---|
| INC-1788 | P-103 | 2023-04-11 | seal leakage | vibration 6.8 mm/s, weeping | **shaft misalignment** (coupling) — corrected by laser alignment |
| INC-1902 | P-205 | 2023-11-29 | seal leakage | weeping, bearing temp rise | **shaft misalignment** after motor swap; alignment not re-checked |
| INC-2010 | P-103 | 2024-07-03 | bearing failure | high vibration | **misalignment** + over-tensioned belts |
| INC-1655 | P-410 | 2022-09-18 | seal leakage | weeping | seal face contamination (different cause) |

## Pattern
On this site, **recurring centrifugal-pump seal failures accompanied by elevated vibration and a recent coupling/motor disturbance are predominantly caused by shaft misalignment** that was not formally verified after maintenance. Laser alignment and post-work alignment verification resolved the recurring cases (P-103, P-205).

> **DEMO NOTE:** This is the prior-incident evidence the RCA graph traversal (`06 §6.1`) uses. Because INC-2041 (P-101) shares the failure mode (seal leakage), the symptom (rising vibration), and the precondition (unverified alignment), the agent ranks **shaft misalignment** as the most probable root cause with high confidence, citing INC-1788 and INC-1902.
