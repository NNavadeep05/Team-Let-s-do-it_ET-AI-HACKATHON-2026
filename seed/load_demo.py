#!/usr/bin/env python3
"""
NEURON IQ — demo dataset loader (TASK-035).

Primes a fresh environment with the curated demo dataset so every moment in
docs/15-demo-script.md lands. API-driven: talks to the running backend
(docs/13-api-spec.md). Run as part of `make bootstrap` AFTER migrations,
constraints, ontology seed, Qdrant init, and MinIO bucket creation.

Prerequisites
-------------
- Backend API reachable at $NEURON_API (default http://localhost:8000/api).
- An initial admin exists (create via `make createadmin` or the app's first-run
  seed). Provide ADMIN_EMAIL / ADMIN_PASSWORD in the environment.
- Admin user-create endpoint POST /admin/users (built in TASK-033).

Behavior
--------
1. Log in as admin.
2. Create the demo plant + one user per role (idempotent: ignores 409s).
3. Upload every document in ./documents EXCEPT the held-back SOP-12 rev3
   (dragged in live during the demo). Pass --load-all to include it.
4. Create the OPEN seal-failure incident INC-2041 (RCA is run live).
5. Print the expected post-load state for a sanity check.

Usage
-----
    python seed/load_demo.py                 # demo mode (holds back SOP-12 rev3)
    python seed/load_demo.py --load-all      # load everything (e.g. for tests)
"""
from __future__ import annotations
import os, sys, time, argparse, pathlib
import requests

API = os.environ.get("NEURON_API", "http://localhost:8000/api")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@riverside.plant")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")
DOCS_DIR = pathlib.Path(__file__).parent / "documents"

# filename -> (doc_type, mime). Markdown sources; export to PDF if you want the
# full OCR path on the live-dragged SOP (see README "Converting to PDF").
MANIFEST = {
    "EQ-MAN-P-101_pump_manual.md":            ("equipment_manual", "text/markdown"),
    "WO_P-101_work_order_log.md":             ("maintenance_log",  "text/markdown"),
    "PID-CWS-01_cooling_water_system.md":     ("pid",              "text/markdown"),
    "pump_class_incident_history.md":         ("incident_report",  "text/markdown"),
    "REG-OSHA-1910.119_PSM.md":               ("regulatory",       "text/markdown"),
    "tribal_voice_note_P-101.md":             ("email",            "text/markdown"),  # captured note, treated as text
    "INC-2041_P-101_seal_failure.md":         ("incident_report",  "text/markdown"),
    # held back from demo load:
    "SOP-12_rev3_flange_maintenance.md":      ("sop",              "text/markdown"),
}
HELD_BACK = {"SOP-12_rev3_flange_maintenance.md"}

DEMO_USERS = [
    ("plant.head@riverside.plant",       "Dana Okafor",   "plant_head"),
    ("manager@riverside.plant",          "Sam Whitfield", "manager"),
    ("compliance@riverside.plant",       "Priya Nair",    "compliance_officer"),
    ("tech@riverside.plant",             "R. Mendez",     "technician"),
]
DEFAULT_USER_PW = os.environ.get("DEMO_USER_PASSWORD", "neuron-demo")


def login(email: str, password: str) -> str:
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_plant(token: str) -> str:
    # admin endpoint; ignore if it already exists
    r = requests.post(f"{API}/admin/plants", headers=h(token),
                      json={"name": "Riverside Plant", "location": "Riverside, USA"}, timeout=30)
    if r.status_code == 409:
        plants = requests.get(f"{API}/admin/plants", headers=h(token), timeout=30).json()["items"]
        return next(p["id"] for p in plants if p["name"] == "Riverside Plant")
    r.raise_for_status()
    return r.json()["id"]


def create_users(token: str, plant_id: str) -> None:
    for email, name, role in DEMO_USERS:
        r = requests.post(f"{API}/admin/users", headers=h(token), json={
            "email": email, "full_name": name, "role": role,
            "plant_id": plant_id, "password": DEFAULT_USER_PW,
        }, timeout=30)
        if r.status_code not in (200, 201, 409):
            r.raise_for_status()
        print(f"  user {email:32s} [{role}] -> {r.status_code}")


def upload_docs(token: str, load_all: bool) -> dict[str, str]:
    ids: dict[str, str] = {}
    for fname, (doc_type, mime) in MANIFEST.items():
        if fname in HELD_BACK and not load_all:
            print(f"  HOLD BACK (drag live): {fname}")
            continue
        path = DOCS_DIR / fname
        with path.open("rb") as fh:
            r = requests.post(
                f"{API}/documents", headers=h(token),
                files={"file": (fname, fh, mime)},
                data={"doc_type": doc_type}, timeout=120,
            )
        r.raise_for_status()
        doc_id = r.json()["id"]
        ids[fname] = doc_id
        print(f"  uploaded {fname:42s} type={doc_type:16s} id={doc_id}")
    return ids


def wait_processed(token: str, doc_ids: list[str], timeout_s: int = 300) -> None:
    print("  waiting for ingestion to complete ...")
    deadline = time.time() + timeout_s
    pending = set(doc_ids)
    while pending and time.time() < deadline:
        for did in list(pending):
            job = requests.get(f"{API}/documents/{did}/job", headers=h(token), timeout=30).json()
            if job.get("stage") == "done" and job.get("status") in ("done", "completed"):
                pending.discard(did)
        if pending:
            time.sleep(3)
    if pending:
        print(f"  WARNING: {len(pending)} docs still processing after {timeout_s}s")
    else:
        print("  all documents processed.")


def create_open_incident(token: str) -> None:
    # logged-in user must be technician+; reuse admin (admin bypasses role checks)
    r = requests.post(f"{API}/rca/incidents", headers=h(token), json={
        "asset_tag": "P-101",
        "description": ("P-101 mechanical seal failed during night shift; third seal "
                        "failure in 14 months. Rising vibration; alignment unverified."),
        "severity": "high",
        "occurred_at": "2025-09-20T02:40:00Z",
    }, timeout=30)
    # Note: this fires incident.created -> auto-RCA chain. For the demo we want it
    # OPEN/un-run, so the backend should support deferring auto-RCA when a
    # `defer_rca: true` flag is set, OR simply create the incident here and run
    # RCA live from the UI. Pass defer if supported:
    if r.status_code == 422:
        r = requests.post(f"{API}/rca/incidents", headers=h(token), json={
            "asset_tag": "P-101", "description": "P-101 repeated mechanical seal failure.",
            "severity": "high", "occurred_at": "2025-09-20T02:40:00Z", "defer_rca": True,
        }, timeout=30)
    r.raise_for_status()
    print(f"  created OPEN incident INC-2041 -> {r.json().get('incident_id')}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--load-all", action="store_true",
                    help="also load the held-back SOP-12 rev3 (skips the live-drag moment)")
    args = ap.parse_args()

    print(f"NEURON IQ demo loader -> {API}")
    token = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    print("logged in as admin.")

    print("creating plant + users ...")
    plant_id = create_plant(token)
    create_users(token, plant_id)

    print("uploading documents ...")
    ids = upload_docs(token, args.load_all)
    wait_processed(token, list(ids.values()))

    print("seeding open incident ...")
    create_open_incident(token)

    print("\nExpected post-load state (demo mode):")
    print("  - Plant 'Riverside Plant' with 5 role users")
    print("  - Knowledge coverage ~50-55% (P-101 documented, gaps elsewhere)")
    print("  - 2 OPEN contradictions on P-101:")
    print("      * torque: 95 Nm (manual) vs 140 Nm (work orders)")
    print("      * lubricant: ISO VG 68 (manual) vs ISO VG 46 (maintenance log)")
    print("  - 1 OPEN incident INC-2041 (seal failure), not yet diagnosed")
    print("  - SOP-12 rev3 held back -> drag in live to make torque a 3-way (95/120/140)")
    print("\nReady. Follow docs/15-demo-script.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
