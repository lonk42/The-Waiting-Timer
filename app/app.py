#!/usr/bin/env python3
import os
import time
import yaml
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DATA_FILE = "data/timers.yaml"
TIMER_NAME = os.getenv("TIMER_NAME", "something")

timers = []
running_timer = None


def load_timers():
    global timers
    try:
        with open(DATA_FILE, "r") as f:
            timers = yaml.safe_load(f) or []
    except FileNotFoundError:
        timers = []


def save_timers():
    with open(DATA_FILE, "w") as f:
        yaml.safe_dump(timers, f)


@app.route("/")
def index():
    total_seconds = sum(t["duration"] for t in timers)
    return render_template(
        "index.html",
        timers=timers,
        total_seconds=total_seconds,
        running=running_timer,
        timer_name=TIMER_NAME,
    )


@app.route("/start", methods=["POST"])
def start_timer():
    global running_timer
    if running_timer is None:
        running_timer = time.time()
        return jsonify({"status": "started"})
    return jsonify({"status": "already running"})


@app.route("/stop", methods=["POST"])
def stop_timer():
    global running_timer
    if running_timer is None:
        return jsonify({"status": "no timer running"})

    stop_time = time.time()
    duration = int(stop_time - running_timer)
    running_timer = None

    entry = {
        "id": len(timers) + 1,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration": duration,
        "description": "",
    }
    timers.append(entry)
    save_timers()
    return jsonify(entry)


@app.route("/update_description", methods=["POST"])
def update_description():
    data = request.json
    timer_id = data.get("id")
    description = data.get("description", "")

    for t in timers:
        if t["id"] == timer_id:
            t["description"] = description
            save_timers()
            return jsonify({"status": "updated", "timer": t})

    return jsonify({"status": "not found"}), 404


@app.route("/total")
def get_total():
    total_seconds = sum(t["duration"] for t in timers)
    if running_timer:
        total_seconds += int(time.time() - running_timer)
    return jsonify({"total": total_seconds})


def format_duration(seconds):
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02}:{mins:02}:{secs:02}"


app.jinja_env.globals.update(format_duration=format_duration)

if __name__ == "__main__":
    load_timers()
    app.run(debug=True, host="0.0.0.0")

