---
title: SECIS Crisis Management Environment
emoji: 🚨
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
  - crisis-management
  - reinforcement-learning
---

# SECIS Crisis Management Environment

A crisis management simulation environment with coordinate-based map system, schema drift, cascade effects, and multi-objective rewards. Simulates emergency response scenarios with ambulances, hospitals, and dynamic incident spawning.

## Quick Start

The simplest way to use the SECIS environment is through the `SecisEnvV2Env` class:

```python
from SECIS_ENV_V2 import SecisEnvV2Action, SecisEnvV2Env

try:
    # Create environment from Docker image
    secis_env = SecisEnvV2Env.from_docker_image("SECIS_ENV_V2-env:latest")

    # Reset
    result = secis_env.reset()
    print(f"Step: {result.observation.step}")
    print(f"Active incidents: {result.observation.stats['active_incidents']}")

    # Dispatch ambulance to incident
    action = SecisEnvV2Action(
        ambulance_id="agent_amb_1",
        target=result.observation.state['incidents'][0]['id'],
        reason="Responding to highest severity incident"
    )
    result = secis_env.step(action)
    print(f"Reward: {result.reward}")
    print(f"Resolved incidents: {result.metadata['resolved_incidents']}")

finally:
    # Always clean up
    secis_env.close()
```

## Building the Docker Image

Before using the environment, you need to build the Docker image:

```bash
# From project root
docker build -t SECIS_ENV_V2-env:latest -f server/Dockerfile .
```

## Deploying to Hugging Face Spaces

You can easily deploy your OpenEnv environment to Hugging Face Spaces using the `openenv push` command:

```bash
# From the environment directory (where openenv.yaml is located)
openenv push

# Or specify options
openenv push --namespace my-org --private
```

## Environment Details

### Action
**SecisEnvV2Action**: Ambulance dispatch action
- `ambulance_id` (str) - ID of the ambulance to dispatch
- `target` (str) - ID of the incident to respond to
- `reason` (str) - Reason for the action

### Observation
**SecisEnvV2Observation**: Full crisis environment state
- `state` (dict) - Full environment state including incidents, ambulances, hospitals
- `stats` (dict) - Environment statistics (active incidents, ambulances, hospital occupancy)
- `step` (int) - Current step number
- `done` (bool) - Whether the episode is done (max_steps reached)
- `reward` (float) - Multi-objective reward for this step
- `metadata` (dict) - Additional info including reward breakdown, drift flag

### Reward System
Multi-objective reward with components:
- **Delivery reward** - +5.0 per incident delivered to hospital
- **Travel penalty** - Small penalty for active ambulances
- **Resource penalty** - Penalty for idle ambulances when incidents exist
- **Fairness penalty** - Penalty for ignoring high-severity incidents
- **Load balance penalty** - Penalty for hospital load imbalance
- **Delay penalty** - Penalty for incidents waiting too long

### Features
- **Coordinate-based map** - 100x100 coordinate plane with hospitals at fixed positions
- **Dynamic incidents** - Cascade effects spawn new incidents based on difficulty
- **Schema drift** - Random structure mutations (incidents ↔ incident_list)
- **Multi-objective rewards** - Balance efficiency, survival, fairness, competition
- **Safety constraints** - Validates actions before execution
- **Adversarial tracking** - Monitors agent weaknesses

## Development & Testing

### Running Locally

Run the server locally for development:

```bash
uvicorn server.app:app --reload
```

### Direct Environment Testing

Test the environment logic directly without starting the HTTP server:

```bash
# From the server directory
python3 server/SECIS_ENV_V2_environment.py
```

## Project Structure

```
SECIS_ENV_V2/
├── .dockerignore         # Docker build exclusions
├── __init__.py            # Module exports
├── README.md              # This file
├── openenv.yaml           # OpenEnv manifest
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependencies (generated)
├── client.py              # SecisEnvV2Env client
├── models.py              # Action and Observation models
└── server/
    ├── __init__.py        # Server module exports
    ├── SECIS_ENV_V2_environment.py  # Core environment logic with crisis simulation
    ├── app.py             # FastAPI application (HTTP + WebSocket endpoints)
    ├── Dockerfile         # Container image definition
    └── requirements.txt   # Python dependencies
```
