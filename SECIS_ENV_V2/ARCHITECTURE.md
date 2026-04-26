# SECIS Architecture

## System Architecture Overview

SECIS follows a modular architecture designed for flexibility, extensibility, and research experimentation. The system is built around a core reinforcement learning environment with multiple supporting modules for agents, training, evaluation, and visualization.

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                          │
│  (app.py) - HTTP/WebSocket endpoints, Dashboard UI, State Mgmt   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Environment Manager                          │
│  (multi_agent_env.py) - Coordinates 3 agent environments         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Crisis Environment                            │
│  (crisis_env.py) - Core simulation logic, coordinate system     │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Agents     │    │   Training   │    │   Effects    │
│              │    │              │    │              │
│ - Greedy     │    │ - Reward     │    │ - Cascade    │
│ - Conservative│    │ - Safety     │    │ - Schema     │
│ - Adaptive   │    │ - Adversarial│    │   Drift      │
└──────────────┘    └──────────────┘    └──────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Evaluation & Logging                         │
│  (metrics_calculator.py, reflection_logger.py)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. FastAPI Server (server/app.py)

**Purpose**: HTTP/WebSocket server providing REST API and interactive dashboard

**Responsibilities**:
- Serve HTML/CSS/JS dashboard UI
- Expose REST endpoints for environment control
- Manage WebSocket connections for real-time updates
- Coordinate between frontend and backend modules
- Handle multi-agent mode switching
- Maintain simulation state

**Key Endpoints**:
- `GET /` - Dashboard UI
- `POST /api/step` - Execute single step
- `POST /api/reset` - Reset environment
- `GET /api/state` - Get current state
- `POST /api/control-parameters` - Update difficulty/adversarial level
- `GET /api/leaderboard` - Get agent scores
- `GET /api/telemetry` - Get performance metrics
- `GET /api/reflection` - Get reflection logs

### 2. Multi-Agent Environment Manager (backend/env/multi_agent_env.py)

**Purpose**: Coordinate multiple agent environments for competitive evaluation

**Responsibilities**:
- Create and manage 3 separate CrisisEnv instances
- Synchronize step execution across all agents
- Aggregate results from all environments
- Maintain global step counter
- Compute leaderboard rankings
- Apply control parameters uniformly

**Architecture**:
```python
MultiAgentEnv
├── environments (Dict)
│   ├── "greedy" → CrisisEnv(agent_name="greedy")
│   ├── "conservative" → CrisisEnv(agent_name="conservative")
│   └── "adaptive" → CrisisEnv(agent_name="adaptive")
├── current_step (int)
├── max_steps (int)
├── difficulty (float)
├── adversarial_level (float)
└── tick_interval (int)
```

### 3. Crisis Environment (backend/env/crisis_env.py)

**Purpose**: Core simulation engine with coordinate-based map system

**Responsibilities**:
- Initialize map (100x100 coordinate plane)
- Manage ambulance state machine (idle → to_incident → to_hospital → idle)
- Execute ambulance movement with smooth interpolation
- Handle incident pickup and hospital delivery
- Apply cascade effects and schema drift
- Compute multi-objective rewards
- Track weakness metrics

**State Machine**:
```
┌─────────┐
│  idle   │
└────┬────┘
     │ dispatch ambulance
     ▼
┌─────────────┐
│ to_incident │
└──────┬──────┘
       │ reached incident
       ▼
┌─────────────┐
│ to_hospital │
└──────┬──────┘
       │ reached hospital
       ▼
┌─────────┐
│  idle   │
└─────────┘
```

**Coordinate System**:
- Map size: 100x100 units
- Hospitals: Fixed at (20,20), (80,20), (50,80)
- Ambulances: Start at (50,50), move at 30 units/tick
- Incidents: Spawn at random (10-90, 10-90)

### 4. Agent Implementations (backend/agent/)

**Purpose**: Implement different decision-making strategies

**GreedyAgent**:
- Strategy: Always select highest severity incident
- Selection: Sort incidents by severity (descending)
- Ambulance: Choose nearest idle ambulance
- Best for: Maximizing immediate reward

**ConservativeAgent**:
- Strategy: Select last incident (likely lower severity)
- Selection: Pick last in list
- Ambulance: Choose nearest idle ambulance
- Best for: Safer, more predictable behavior

**LLMAgent** (Adaptive):
- Strategy: Dynamically switch based on system state
- Conditions:
  - Hospital overflow (>80% capacity) → Conservative
  - High severity ignored (>0.7) → Greedy
  - Default → Greedy
- Best for: Adaptive to changing conditions

### 5. Training Module (backend/training/)

**Reward System (reward.py)**:
- Multi-objective reward calculation
- Components:
  - Delivery reward: +5.0 per hospital delivery
  - Travel penalty: -0.01 per active ambulance
  - Resource penalty: -0.05 per idle ambulance (when incidents exist)
  - Fairness penalty: -0.2 per ignored high-severity incident
  - Load balance penalty: -0.2 × occupancy imbalance
  - Incident penalty: -0.05 per waiting incident
  - Duplicate dispatch penalty: -0.1 × prioritization failures
  - Delay penalty: -0.1 per delayed incident (>5 ticks)

**Safety System (safety.py)**:
- Validate agent actions before execution
- Constraints:
  - No idle resource abuse
  - No invalid dispatch (non-existent incident)
  - No repeated actions
- Returns: (is_safe, reason, safety_flags)

**Adversarial System (adversarial.py)**:
- Track agent weaknesses over time
- Metrics:
  - Prioritization failures (reward < -1.0)
  - Delays (incidents > 5)
  - Ignored high severity incidents
- Used for: Difficulty adjustment and agent evaluation

### 6. Environmental Effects (backend/env/)

**Cascade Effects (cascade.py)**:
- Dynamically spawn new incidents during simulation
- Probability: 0.3 + (difficulty × 0.4)
- Spawn rate: 0-2 incidents per step (multi-agent), 0-1 (single-agent)
- Also affects hospital occupancy randomly

**Schema Drift (schema_drift.py)**:
- Randomly change data structure
- Probability: 0.2 + (adversarial_level × 0.5)
- Drift types:
  - incidents ↔ incident_list
  - Add/remove drift_metadata field
- Purpose: Test agent robustness to structural changes

### 7. Evaluation Module (backend/evaluation/)

**Metrics Calculator (metrics_calculator.py)**:
- Compute performance metrics
- Metrics: response time, survival rate, hospital efficiency
- Used for: Leaderboard and telemetry

**Counterfactual Analyzer (counterfactual_analyzer.py)**:
- Analyze what-if scenarios
- Compare different agent strategies
- Used for: Research and improvement

**Reflection Logger (reflection_logger.py)**:
- Log agent decisions and outcomes
- Track: action, what happened, reward
- Used for: Agent learning and analysis

### 8. OpenEnv Interface (backend/openenv_interface.py)

**Purpose**: Provide OpenEnv-compatible API for external training

**Responsibilities**:
- Wrap CrisisEnv in OpenEnv format
- Standardize action/observation spaces
- Enable integration with external RL libraries
- Support remote training via ngrok

## Data Flow

### Single-Agent Mode

```
User Action (Dashboard)
    ↓
FastAPI Server (/api/step)
    ↓
CrisisEnv.step(action)
    ↓
├─ Apply action (dispatch ambulance)
├─ Move ambulances
├─ Apply cascade effects
├─ Apply schema drift
├─ Compute reward
└─ Update adversarial tracker
    ↓
Return (state, reward, done, metadata)
    ↓
FastAPI Server
    ↓
Dashboard Update (WebSocket)
```

### Multi-Agent Mode

```
User Action (Dashboard)
    ↓
FastAPI Server (/api/step-all)
    ↓
MultiAgentEnv.step_all(actions)
    ↓
├─ greedy_env.step(greedy_action)
├─ conservative_env.step(conservative_action)
└─ adaptive_env.step(adaptive_action)
    ↓
Aggregate results
    ↓
Compute leaderboard
    ↓
Return (step, done, agents)
    ↓
FastAPI Server
    ↓
Dashboard Update (WebSocket)
```

## State Management

### Global State (Server)

```python
{
    "running": bool,
    "tick": int,
    "drift_flag": bool,
    "difficulty": float,
    "adversarial_level": float,
    "tick_interval": int,
    "totalReward": float,
    "rewardBreakdown": dict,
    "safetyFlags": dict,
    "currentStep": int,
    "telemetry": list,
    "leaderboard": list,
    "reflectionLogs": list,
    "mapState": dict
}
```

### Environment State (CrisisEnv)

```python
{
    "incidents": list,  # or "incident_list" (schema drift)
    "ambulances": list,
    "hospitals": list,
    "map_size": int,
    "resources": dict,
    "system_state": dict
}
```

### Incident State

```python
{
    "id": str,
    "severity": float,  # 0.3-0.9
    "x": float,  # 0-100
    "y": float,  # 0-100
    "status": str,  # waiting, picked, resolved
    "assigned_ambulance": str or None,
    "assigned_time": int
}
```

### Ambulance State

```python
{
    "id": str,
    "x": float,
    "y": float,
    "state": str,  # idle, to_incident, to_hospital
    "target_incident": dict or None,
    "target_hospital": dict or None,
    "carrying_incident": dict or None,
    "path": list  # [(x, y), ...]
}
```

### Hospital State

```python
{
    "id": str,
    "x": float,
    "y": float,
    "capacity": int,
    "occupied": int
}
```

## Control Parameters

### Difficulty (0-1)

- **Low (0-0.3)**: Fewer incidents, lower severity
- **Medium (0.3-0.7)**: Balanced scenario
- **High (0.7-1.0)**: Many incidents, high severity

**Effects**:
- Initial incident count: 3 + int(difficulty × 2)
- Incident severity: 0.3 + difficulty × 0.2 to 0.9
- Cascade probability: 0.3 + difficulty × 0.4

### Adversarial Level (0-1)

- **Low (0-0.3)**: Rare schema drift
- **Medium (0.3-0.7)**: Moderate structural changes
- **High (0.7-1.0)**: Frequent schema drift

**Effects**:
- Schema drift probability: 0.2 + adversarial_level × 0.5

### Tick Interval (100-5000ms)

- Controls simulation speed
- Lower = faster ambulance movement
- Higher = slower, more deliberate simulation

## Communication Protocols

### REST API

**Request/Response Format**:
```json
// Request
{
    "ambulance_id": "agent_amb_1",
    "target": "inc_init_1234",
    "reason": "High severity incident"
}

// Response
{
    "state": {...},
    "reward": 5.0,
    "done": false,
    "metadata": {
        "reward_breakdown": {...},
        "resolved_incidents": 1,
        "new_incidents": 0,
        "drift_flag": false,
        "step": 5
    }
}
```

### WebSocket

**Real-time Updates**:
```json
{
    "type": "state_update",
    "data": {
        "state": {...},
        "reward": 5.0,
        "telemetry": [...],
        "leaderboard": [...]
    }
}
```

## Deployment Architecture

### Development Mode

```
Browser → FastAPI Server (localhost:8000)
                ↓
         Python Backend (in-memory)
```

### Production Mode

```
Browser → Nginx → FastAPI Server (Docker)
                ↓
         Python Backend (Docker container)
                ↓
         Redis (optional, for state persistence)
```

### External Training

```
Colab/Jupyter → ngrok → FastAPI Server → CrisisEnv
                ↓
         Download trajectories → Train model
```

## Extensibility Points

### Adding New Agents

1. Create new agent class in `backend/agent/`
2. Implement `act(state)` method
3. Add to `MultiAgentEnv` initialization
4. Update dashboard UI for selection

### Adding New Effects

1. Create new module in `backend/env/`
2. Implement effect function with `state` input
3. Call from `CrisisEnv.step()`
4. Add control parameter if needed

### Adding New Reward Components

1. Modify `compute_multi_objective_reward()` in `reward.py`
2. Add penalty/reward calculation
3. Update `reward_breakdown` dictionary
4. Add to telemetry display if needed

### Adding New Metrics

1. Add metric calculation in `metrics_calculator.py`
2. Update dashboard UI to display
3. Add to reflection logging if needed

## Performance Considerations

### Optimizations

- **Ambulance Path Tracking**: Limited to 100 points to prevent memory bloat
- **Incident Cleanup**: Removed from list after hospital delivery
- **Efficient Distance Calculations**: Euclidean distance with caching
- **Batch Processing**: Multi-agent mode processes all agents in single step

### Scalability

- **Single Agent**: Handles 2 ambulances, ~10 incidents
- **Multi Agent**: Handles 6 ambulances (3 agents × 2), ~30 incidents
- **Maximum Steps**: 20 steps (configurable)
- **Tick Rate**: 200ms default (100-5000ms range)

## Security Considerations

### Safety Constraints

- Action validation before execution
- Resource abuse prevention
- Invalid dispatch blocking
- Repeated action detection

### Input Validation

- Parameter range checking (0-1 for difficulty/adversarial)
- Tick interval bounds (100-5000ms)
- Coordinate bounds (0-100)
- ID format validation

### Error Handling

- Graceful degradation on schema drift
- Fallback to default keys on missing fields
- Exception catching in reward calculation
- Safe default returns on invalid inputs
