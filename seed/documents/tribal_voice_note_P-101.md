# Tribal Knowledge — Voice Note Transcript (P-101)

**Document ID:** TRIBAL-P-101-001
**Capture type:** voice
**Author:** R. Mendez (Senior Maintenance Technician, 31 years)
**Asset hint:** P-101
**Effective date:** 2025-09-22

## Raw transcript
> "Quick note on the cooling water pump, P-101. The east-side mechanical seal gives you a warning — it starts to whine, kind of a high pitch, usually about a week, ten days before it actually lets go. Soon as you hear that whine, pull the seal kit from stores and schedule the swap, because if you wait for the weeping you're already into an emergency. We've been caught out twice. Also — and this isn't in the book — check the coupling alignment every time you touch that pump. On these pumps the seals don't really die from age, they die from being a hair out of line. Get the laser on it, don't eyeball it."

## Structured (expected agent output, `12 §Tribal`)
```json
{
  "symptom": "high-pitched whine from the east-side mechanical seal ~7-10 days before failure",
  "action": "on hearing the whine, pull the seal kit from stores and schedule a planned seal swap; always verify coupling alignment with a laser tool after any work on the pump",
  "rationale": "early warning avoids an emergency wet failure; seals on these pumps fail from misalignment, not age",
  "asset_hint": "P-101",
  "tags": ["mechanical seal", "early warning", "alignment", "preventive"]
}
```

> **DEMO NOTE:** This is recorded live on the phone during Moment 4. The technician's experience corroborates the RCA finding (misalignment) and the early-warning behavior — the kind of knowledge that walks out the door when an expert retires. After capture it links as a `TribalNote-[:ABOUT]->P-101` node and appears in the web Graph and the asset's mobile detail.
