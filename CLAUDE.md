# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Waiting Timer is a Flask-based web application for tracking time intervals with persistent storage. It allows users to start/stop timers, view a running total, and add descriptions to saved timer entries. State is persisted in YAML format and can be deployed via Docker or Kubernetes.

## Architecture

### Application Structure

- **`app/app.py`**: Main Flask application (3 key components)
  - State management: In-memory dict with `timers` (list of completed timers) and `running` (current timer state)
  - Persistence: YAML-based storage in `data/timers.yaml` with load/save on each request
  - RESTful endpoints: `/start`, `/stop`, `/state`, `/update_description`, `/total`

- **`app/templates/index.html`**: Single-page application with:
  - TailwindCSS styling (loaded via CDN)
  - JavaScript client that polls `/state` every 2 seconds
  - Live subtimer display (updates every 50ms when timer is running)
  - Inline description editing with blur-to-save

- **`app/data/`**: Runtime data directory for `timers.yaml` persistence

### State Management

The application maintains state in a simple structure:
```python
{
    "timers": [{"id": int, "datetime": str, "duration": int, "description": str}, ...],
    "running": {"start_time": float} | None
}
```

- State is loaded from YAML at the start of every request
- State is saved to YAML after mutations (start, stop, update_description)
- Timer IDs are sequential (len(timers) + 1)
- Duration is always stored in seconds

### Configuration

- **Environment variable**: `TIMER_NAME` - Customizes the display name shown in the UI (default: "something")
- This is set via Helm values (`timerName`) or directly in the container

## Development Commands

### Local Development

Run the Flask development server:
```bash
cd app
python app.py
```
The app runs on `http://0.0.0.0:5000` with debug mode enabled.

### Docker

Build the Docker image:
```bash
docker build -t the-waiting-timer:latest .
```

Run the container:
```bash
docker run -p 5000:5000 -v $(pwd)/data:/app/data -e TIMER_NAME="your-thing" the-waiting-timer:latest
```

The Dockerfile uses gunicorn for production deployment.

### Kubernetes/Helm

Install the Helm chart:
```bash
helm install my-timer ./the-waiting-timer
```

Customize timer name:
```bash
helm install my-timer ./the-waiting-timer --set timerName="deployment"
```

Helm chart components:
- **Deployment**: Single replica Flask app with PVC mount at `/app/data`
- **Service**: ClusterIP on port 80 → 5000
- **Ingress**: Optional (disabled by default), supports TLS
- **PVC**: 1Gi persistent storage for timer data (can be disabled via `persistence.enabled=false`)

## Key Implementation Details

### Timer Calculation

Total time is calculated on-demand:
- Sum all completed timer durations
- If a timer is running, add `current_time - start_time` to the total
- This happens on every page load and `/state` call

### API Endpoints

- `GET /`: Renders the main page with initial state
- `POST /start`: Starts a timer (records current timestamp)
- `POST /stop`: Stops timer, calculates duration, creates new timer entry
- `GET /state`: Returns current state (timers, running status, total)
- `POST /update_description`: Updates description for a specific timer ID
- `GET /total`: Returns only the total seconds

### Frontend Behavior

- Auto-refreshes every 2 seconds via `/state` endpoint
- Running timer shows real-time countdown with centisecond precision
- Description changes are saved on blur (losing focus)
- Timer list is dynamically rebuilt on each state fetch

## Important Notes

- **No authentication**: This is a single-user application
- **File locking**: No file locking on `timers.yaml` - not designed for concurrent access
- **Data directory**: Must exist or be created before first write (handled by `os.makedirs` in `save_state()`)
- **Volume persistence**: In Kubernetes, timer data persists across pod restarts via PVC
