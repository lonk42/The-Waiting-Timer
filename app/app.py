#!/usr/bin/env python3
import os
import time
import yaml
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DATA_FILE = "data/timers.yaml"
TIMER_NAME = os.getenv("TIMER_NAME", "something")

state = {
    "timers": [],
    "running": None  # {"start_time": float}
}

def load_state():
    """Load state (timers + running timer) from YAML, with defaults."""
    global state
    try:
        with open(DATA_FILE, "r") as f:
            loaded = yaml.safe_load(f) or {}
    except FileNotFoundError:
        loaded = {}

    # normalize structure
    state = {
        "timers": loaded.get("timers", []),
        "running": loaded.get("running", None)
    }

def save_state():
    """Persist state to YAML, ensuring valid structure."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        yaml.safe_dump(state, f, sort_keys=False)

@app.route("/")
def index():
    load_state()
    total_seconds = sum(t["duration"] for t in state["timers"])
    if state["running"]:
        total_seconds += int(time.time() - state["running"]["start_time"])

    return render_template(
        "index.html",
        timers=state["timers"],
        total_seconds=total_seconds,
        running=state["running"],
        timer_name=TIMER_NAME,
    )


@app.route("/start", methods=["POST"])
def start_timer():
    load_state()
    if not state["running"]:
        state["running"] = {"start_time": time.time()}
        save_state()
        return jsonify({"status": "started"})
    return jsonify({"status": "already running"})


@app.route("/stop", methods=["POST"])
def stop_timer():
    load_state()
    if not state["running"]:
        return jsonify({"status": "no timer running"})

    stop_time = time.time()
    duration = int(stop_time - state["running"]["start_time"])

    entry = {
        "id": len(state["timers"]) + 1,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration": duration,
        "description": "",
    }

    state["timers"].append(entry)
    state["running"] = None
    save_state()

    return jsonify(entry)

@app.route("/state")
def get_state():
    load_state()
    total_seconds = sum(t["duration"] for t in state["timers"])
    if state["running"]:
        total_seconds += int(time.time() - state["running"]["start_time"])
    return jsonify({
        "timers": state["timers"],
        "running": state["running"],
        "total": total_seconds
    })

@app.route("/update_description", methods=["POST"])
def update_description():
    load_state()
    data = request.json
    timer_id = data.get("id")
    description = data.get("description", "")

    for t in state["timers"]:
        if t["id"] == timer_id:
            t["description"] = description
            save_state()
            return jsonify({"status": "updated", "timer": t})

    return jsonify({"status": "not found"}), 404


@app.route("/total")
def get_total():
    load_state()
    total_seconds = sum(t["duration"] for t in state["timers"])
    if state["running"]:
        total_seconds += int(time.time() - state["running"]["start_time"])
    return jsonify({"total": total_seconds})


def format_duration(seconds):
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02}:{mins:02}:{secs:02}"


app.jinja_env.globals.update(format_duration=format_duration)

if __name__ == "__main__":
    load_state()
    app.run(debug=True, host="0.0.0.0")

