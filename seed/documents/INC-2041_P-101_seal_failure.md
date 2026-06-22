# Incident Report — INC-2041

**Document ID:** INC-2041
**Doc type:** incident_report
**Asset tag:** P-101
**Severity:** high
**Occurred:** 2025-09-20 02:40
**Plant / Unit:** Riverside Plant / Cooling Water Unit
**Status at load time:** OPEN — not yet diagnosed (RCA is run live in the demo)

## Summary
P-101 mechanical seal failed during night shift, releasing cooling water to the bund and forcing a switch to standby pump P-103. This is the **third mechanical-seal failure on P-101 in 14 months**.

## Observations
- Seal weeping observed ~6 days prior to failure (night-shift log).
- Vibration at last inspection (WO-3355) was 7.1 mm/s RMS — elevated and trending up over two quarters.
- Bearing temperature (TT-209) reached 78 °C before trip.
- Alignment had not been formally verified after the previous seal replacement (WO-3299).
- Flange bolts had been torqued to 140 Nm (field practice), above the manufacturer value.

## Immediate action
Switched to P-103; isolated P-101 via V-12; seal replaced under WO-3402.

## For analysis
Recurring seal failures with rising vibration and unverified alignment on a centrifugal pump. Compare against prior cooling-water pump seal failures (see pump-class incident history).

> **DEMO NOTE:** Loaded as an **open** incident. During the demo you click *Run* and the RCA agent traverses the graph — P-101's symptoms (vibration, repeat seal failure) plus prior centrifugal-pump seal failures root-caused to misalignment — and returns **shaft/coupling misalignment** as the top-ranked cause, with the evidence trail and citations, then auto-generates a Lessons Learned entry for the pump class.
