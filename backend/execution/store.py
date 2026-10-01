import json
import os
import uuid


# Vercel's deployed filesystem is read-only.
# /tmp is writable during a serverless invocation.
RUNTIME_DIR = os.path.join(
    os.environ.get("TMPDIR", "/tmp"),
    "nudge_runtime"
)

os.makedirs(RUNTIME_DIR, exist_ok=True)

STORE_FILE = os.path.join(RUNTIME_DIR, "runs.json")


def _load_runs():
    if not os.path.exists(STORE_FILE):
        return {}

    try:
        with open(STORE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_runs(runs):
    os.makedirs(RUNTIME_DIR, exist_ok=True)

    with open(STORE_FILE, "w", encoding="utf-8") as file:
        json.dump(runs, file, indent=2, ensure_ascii=False)


def create_run(
    goal,
    plan=None,
    analysis=None,
    action=None,
    status="created"
):
    run_id = str(uuid.uuid4())

    runs = _load_runs()

    run = {
        "run_id": run_id,
        "goal": goal,
        "plan": plan,
        "analysis": analysis,
        "action": action,
        "status": status,
    }

    runs[run_id] = run
    _save_runs(runs)

    return run


def get_run(run_id):
    runs = _load_runs()
    return runs.get(run_id)


def update_run(run_id, updates):
    runs = _load_runs()

    if run_id not in runs:
        return None

    runs[run_id].update(updates)
    _save_runs(runs)

    return runs[run_id]


def delete_run(run_id):
    runs = _load_runs()

    if run_id in runs:
        del runs[run_id]
        _save_runs(runs)

    return True