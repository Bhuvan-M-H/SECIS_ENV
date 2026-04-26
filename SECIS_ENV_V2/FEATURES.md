# SECIS Features

## Core Features

### 1. Coordinate-Based Map System

**Description**: A 100x100 coordinate plane simulating a city layout with hospitals, ambulances, and incidents.

**Implementation Details**:
- Map dimensions: 100×100 units
- Hospital locations: Fixed at (20,20), (80,20), (50,80)
- Ambulance movement: Smooth interpolation at 30 units/tick
- Incident spawning: Random coordinates (10-90, 10-90)
- Path tracking: Records ambulance movement history (max 100 points)

**Key Features**:
- Realistic distance calculations using Euclidean metric
- Nearest hospital selection for delivery
- Visual path rendering in dashboard
- Collision-free movement (no ambulance-ambulance collision logic)

**Use Case**: Provides spatial reasoning challenge for agents to optimize dispatch routes.

### 2. Multi-Agent System

**Description**: Simultaneous execution of three different agent strategies for competitive evaluation.

**Agent Types**:
1. **Greedy Agent**: Always selects highest severity incident
   - Strategy: Sort incidents by severity (descending)
   - Ambulance selection: Nearest to target
   - Best for: Maximizing immediate reward
   - Weakness: May ignore load balancing

2. **Conservative Agent**: Selects last incident (likely lower severity)
   - Strategy: Pick last in list
   - Ambulance selection: Nearest to target
   - Best for: Safer, predictable behavior
   - Weakness: May miss high-priority incidents

3. **Adaptive Agent**: Dynamically switches strategies based on system state
   - Strategy: Contextual switching
   - Conditions:
     - Hospital overflow (>80% capacity) → Conservative
     - High severity ignored (>0.7) → Greedy
     - Default → Greedy
   - Best for: Adapting to changing conditions
   - Weakness: Strategy switching overhead

**Implementation**:
- Each agent has separate environment instance
- Independent ambulance fleets (2 per agent)
- Synchronized step execution
- Shared control parameters
- Leaderboard aggregation

**Dashboard Features**:
- Real-time leaderboard display
- Agent selection dropdown
- Multi-agent toggle switch
- Per-agent reward tracking
- Performance comparison graphs

### 3. Schema Drift

**Description**: Random structural changes to the environment's data representation, testing agent robustness to distribution shift.

**Drift Types**:
1. **Key Renaming**: incidents ↔ incident_list
2. **Field Addition**: Add drift_metadata field
3. **Field Removal**: Remove drift_metadata field

**Probability Calculation**:
```
drift_probability = 0.2 + (adversarial_level × 0.5)
```

**Range**: 0.2 (low adversarial) to 0.7 (high adversarial)

**Implementation Details**:
- Occurs after cascade effects each step
- Random check against probability threshold
- Graceful degradation with fallback keys
- Drift flag indicator in dashboard

**Agent Handling**:
```python
def get_incidents(state):
    return state.get("incidents", state.get("incident_list", []))
```

**Research Value**: Tests agent robustness to non-stationary observation spaces.

### 4. Cascade Effects

**Description**: Dynamic incident spawning that continuously adds new emergencies during simulation.

**Probability Calculation**:
```
cascade_probability = 0.3 + (difficulty × 0.4)
```

**Range**: 0.3 (low difficulty) to 0.7 (high difficulty)

**Spawn Rate**:
- Single-agent mode: 0-1 incidents per step
- Multi-agent mode: 0-2 incidents per step

**Implementation Details**:
- Occurs after ambulance movement each step
- New incidents have random severity (0.4-0.95)
- Random coordinate placement (10-90, 10-90)
- Also affects hospital occupancy randomly (+2 to random hospital)

**Research Value**: Tests agent adaptation to non-stationary environments.

### 5. Adversarial Mode

**Description**: Configurable difficulty and adversarial scenario triggering to stress-test agent performance.

**Control Parameters**:

**Difficulty (0-1)**:
- **Low (0-0.3)**: Fewer incidents, lower severity
  - Initial incidents: 3
  - Severity range: 0.3-0.5
  - Cascade probability: 0.3-0.42
- **Medium (0.3-0.7)**: Balanced scenario
  - Initial incidents: 3-4
  - Severity range: 0.36-0.68
  - Cascade probability: 0.42-0.58
- **High (0.7-1.0)**: Many incidents, high severity
  - Initial incidents: 4-5
  - Severity range: 0.44-0.9
  - Cascade probability: 0.58-0.7

**Adversarial Level (0-1)**:
- **Low (0-0.3)**: Rare schema drift (20-35% probability)
- **Medium (0.3-0.7)**: Moderate drift (35-55% probability)
- **High (0.7-1.0)**: Frequent drift (55-70% probability)

**Tick Interval (100-5000ms)**:
- Controls simulation speed
- Lower = faster ambulance movement
- Higher = slower, more deliberate simulation

**Weakness Tracking**:
```python
weakness_tracker = {
    "prioritization_failures": count(reward < -1.0),
    "delays": count(incidents > 5),
    "ignored_high_severity": sum(inc.severity > 0.7)
}
```

**Research Value**: Systematic stress testing and robustness evaluation.

### 6. Multi-Objective Reward System

**Description**: Complex reward structure balancing competing objectives: efficiency, fairness, survival, and competition.

**Reward Components**:

**Positive Rewards**:
1. **Hospital Delivery Reward**: +5.0 per incident delivered
   - Primary reward signal
   - Only awarded on successful hospital drop-off
   - Encourages incident resolution

**Penalties**:

1. **Travel Efficiency Penalty**: -0.01 × active_ambulances
   - Penalizes ambulances in transit
   - Encourages shorter routes
   - Reduced penalty for smoother gameplay

2. **Resource Penalty**: -0.05 × idle_count
   - Applied only when incidents exist and ambulances idle
   - Encourages resource utilization
   - Prevents hoarding idle resources

3. **Fairness Penalty**: -0.2 × high_severity_ignored
   - Counts incidents with severity > 0.7
   - Encourages prioritizing critical cases
   - Prevents ignoring high-priority emergencies

4. **Hospital Load Balancing Penalty**: -0.2 × load_imbalance
   - load_imbalance = max_occupancy - min_occupancy
   - Encourages even distribution across hospitals
   - Prevents overloading single hospital

5. **Incident Penalty**: -0.05 × waiting_incidents
   - Penalizes backlog of unresolved incidents
   - Encourages timely resolution
   - Global pressure to act

6. **Duplicate Dispatch Penalty**: -0.1 × prioritization_failures
   - Tracks from weakness_tracker
   - Penalizes sending multiple ambulances to same incident
   - Encourages efficient resource allocation

7. **Delay Penalty**: -0.1 × delayed_incidents
   - Counts incidents waiting > 5 ticks after assignment
   - Encourages faster response times
   - Penalizes prolonged transport

**Total Reward Calculation**:
```python
total_reward = (
    base_reward +           # 0.0
    delivery_reward +       # +5.0 × delivered
    travel_penalty +        # -0.01 × active
    resource_penalty +      # -0.05 × idle (when incidents exist)
    fairness_penalty +      # -0.2 × high_severity_ignored
    load_balance_penalty +   # -0.2 × imbalance
    incident_penalty +       # -0.05 × waiting
    duplicate_dispatch_penalty +  # -0.1 × failures
    delay_penalty            # -0.1 × delayed
)
```

**Normalized Scores (0-100%)**:

1. **Efficiency Score**:
   ```python
   efficiency = (active_ambulances / total_ambulances) × 100
   ```
   - Higher = better resource utilization
   - 100% = all ambulances active

2. **Survival Score**:
   ```python
   waiting_ratio = waiting_incidents / total_incidents
   avg_severity = average(severity of waiting)
   survival = 100 - (waiting_ratio × 40) - (avg_severity × 20)
   ```
   - Decreases with waiting incidents
   - Decreases with high severity waiting
   - 100% = no waiting incidents

3. **Fairness Score**:
   ```python
   fairness = (1 - high_severity_ignored / waiting_incidents) × 100
   ```
   - Higher = fewer high-severity ignored
   - 100% = no high-severity ignored

4. **Competition Score**:
   ```python
   competition = (1 - load_imbalance) × 100
   ```
   - Higher = better load balancing
   - 100% = perfectly balanced hospitals

**Research Value**: Multi-objective optimization with sparse primary reward and dense shaping penalties.

### 7. Safety Constraints

**Description**: Pre-action validation to prevent invalid or harmful actions.

**Constraints**:

1. **No Idle Resource Abuse**:
   - Check: Idle ambulances must exist
   - Violation: Return false if no idle ambulances
   - Purpose: Prevent dispatching non-existent resources

2. **No Invalid Dispatch**:
   - Check: Target incident must exist
   - Violation: Return false if target not in incident list
   - Purpose: Prevent dispatching to non-existent incidents

3. **No Repeated Actions**:
   - Check: Action should not be exact repeat
   - Violation: Return false if repeated
   - Purpose: Prevent infinite loops (placeholder implementation)

**Implementation**:
```python
def check_safety_constraints(action, state):
    safety_flags = {
        "no_idle_resource_abuse": True,
        "no_invalid_dispatch": True,
        "no_repeated_actions": True
    }
    
    if action.get("action") == "wait":
        return True, "Wait action is safe", safety_flags
    
    if not idle_ambulances:
        safety_flags["no_idle_resource_abuse"] = False
        return False, "No idle ambulances", safety_flags
    
    if target not in incident_ids:
        safety_flags["no_invalid_dispatch"] = False
        return False, "Invalid target", safety_flags
    
    return True, "Action is safe", safety_flags
```

**Dashboard Display**:
- Safety status indicator (PASS/FAIL)
- Safety checklist with individual flags
- Real-time constraint violation alerts

**Research Value**: Constrained reinforcement learning with action validation.

### 8. Reflection System

**Description**: Action logging with outcome tracking for agent learning and analysis.

**Log Structure**:
```python
reflection_log = {
    "timestamp": ISO_8601_string,
    "action": {
        "type": "dispatch ambulance" or "wait",
        "target": incident_id or None,
        "ambulance_id": ambulance_id or None,
        "reason": text_explanation
    },
    "what_happened": {
        "incidents_resolved": int,
        "incidents_spawned": int,
        "schema_drift": boolean
    },
    "reward": {
        "total": float,
        "breakdown": {
            "delivery_reward": float,
            "travel_penalty": float,
            "resource_penalty": float,
            "fairness_penalty": float,
            "load_balance_penalty": float,
            "incident_penalty": float,
            "duplicate_dispatch_penalty": float,
            "delay_penalty": float
        }
    }
}
```

**Features**:
- Logs every action and outcome
- Stores in memory for analysis
- Displayed in dashboard with scrollable log
- Available for agent learning (LLMAgent)
- Timestamped for temporal analysis

**Dashboard Features**:
- Scrollable reflection log panel
- Color-coded by reward (positive/negative)
- Detailed breakdown display
- Delete button for clearing logs

**Research Value**: Episodic memory, meta-learning, and explainable AI.

### 9. Telemetry System

**Description**: Real-time performance monitoring with metric collection and visualization.

**Metrics Collected**:

1. **Step**: Current simulation step
2. **Reward**: Step reward received
3. **Incident Count**: Number of active incidents
4. **Response Time**: Average time to resolve incidents
5. **Hospital Occupancy**: Percentage of hospital capacity used

**Visualization**:
- **Reward Graph**: Line chart showing reward over steps
- **Incidents Graph**: Line chart showing incident count over steps
- **Response Time Graph**: Line chart showing response time over steps

**Implementation**:
```python
telemetry = {
    "step": current_step,
    "reward": step_reward,
    "incident_count": len(incidents),
    "response_time": average_response_time,
    "hospital_occupancy": occupancy_percentage
}
```

**Dashboard Features**:
- Real-time Chart.js graphs
- Last 20 data points displayed
- Auto-refresh every 2 seconds
- Color-coded lines (cyan, green, orange)

**Research Value**: Performance monitoring, debugging, and analysis.

### 10. Leaderboard System

**Description**: Competitive ranking of agents based on cumulative reward and performance metrics.

**Leaderboard Entries**:
```python
leaderboard_entry = {
    "agent": str,  # "greedy", "conservative", "adaptive"
    "score": float,  # cumulative reward
    "resolved": int,  # incidents resolved
    "avg": float     # average reward per step
}
```

**Ranking Criteria**:
- Primary: Total cumulative reward
- Secondary: Incidents resolved
- Tertiary: Average reward per step

**Dashboard Features**:
- Real-time leaderboard display
- Leading agent highlighted
- Agent badges with colors
- Statistics display (reward, resolved, avg)
- Auto-sort by score

**Research Value**: Multi-agent comparison and competitive evaluation.

### 11. Interactive Dashboard

**Description**: Web-based UI for environment control, visualization, and monitoring.

**UI Components**:

**Header**:
- Logo and title
- Tick counter
- Schema drift status indicator
- Difficulty display
- Demo mode toggle

**Left Panel**:
- Control buttons (Start, Reset)
- Difficulty slider (0-1)
- Adversarial level slider (0-1)
- Tick interval slider (100-5000ms)
- Agent selection dropdown
- Multi-agent toggle

**Center Panel**:
- City operations map (100x100 coordinate plane)
- Hospital markers with occupancy
- Incident markers with severity colors
- Ambulance markers with movement paths
- Learning metrics section (response time, survival, resolved)

**Right Panel**:
- Leaderboard (multi-agent mode)
- Telemetry charts (reward, incidents, response time)
- Reflection log (scrollable)
- Safety checks panel
- Reward breakdown (efficiency, survival, fairness, competition)

**Features**:
- Real-time WebSocket updates
- Responsive design
- Dark theme with blue accents
- Smooth animations
- Error handling

**Technologies**:
- HTML5
- CSS3 with gradients and animations
- Vanilla JavaScript
- Chart.js for graphs
- WebSocket for real-time updates

### 12. Control Parameters

**Description**: Dynamic adjustment of environment parameters during simulation.

**Parameters**:

**Difficulty (0-1)**:
- Affects: Initial incident count, severity range, cascade probability
- Range: 0.0 to 1.0
- Default: 0.5
- Update: Real-time via slider

**Adversarial Level (0-1)**:
- Affects: Schema drift probability
- Range: 0.0 to 1.0
- Default: 0.5
- Update: Real-time via slider

**Tick Interval (100-5000ms)**:
- Affects: Simulation speed
- Range: 100 to 5000
- Default: 200
- Update: Real-time via slider

**API Endpoint**:
```python
POST /api/control-parameters
{
    "difficulty": 0.7,
    "adversarial_level": 0.8,
    "tick_interval": 300
}
```

**Research Value**: Curriculum learning and adaptive difficulty.

### 13. OpenEnv Compatibility

**Description**: Standard RL environment interface for integration with external libraries.

**Interface**:
```python
class CrisisEnv:
    def reset() -> Dict[str, Any]
    def step(action: Dict[str, Any]) -> Tuple[Dict, float, bool, Dict]
    def get_stats() -> Dict[str, Any]
    def get_control_parameters() -> Dict[str, Any]
    def set_control_parameters(**kwargs)
```

**Client**:
- `client.py`: OpenEnv-compatible client
- Supports remote connection via ngrok
- Enables external training (Colab, Jupyter)

**Use Case**: Integration with RL libraries (Stable Baselines, RLlib, etc.)

### 14. REST API

**Description**: HTTP endpoints for environment control and data access.

**Endpoints**:

**Environment Control**:
- `POST /api/step` - Execute single step
- `POST /api/reset` - Reset environment
- `GET /api/state` - Get current state
- `POST /api/control-parameters` - Update parameters

**Data Access**:
- `GET /api/leaderboard` - Get agent rankings
- `GET /api/telemetry` - Get performance metrics
- `GET /api/reflection` - Get reflection logs
- `DELETE /api/reflection` - Clear reflection logs

**Static**:
- `GET /` - Dashboard UI
- `GET /web` - Dashboard UI (alternate)

**Implementation**: FastAPI with async support

### 15. WebSocket Support

**Description**: Real-time bidirectional communication for live updates.

**Features**:
- Automatic state updates
- Leaderboard synchronization
- Telemetry streaming
- Reflection log updates

**Message Format**:
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

**Use Case**: Real-time dashboard updates without polling.

### 16. Ambulance State Machine

**Description**: Finite state machine controlling ambulance behavior.

**States**:
1. **idle**: Waiting for dispatch
2. **to_incident**: Moving toward incident
3. **to_hospital**: Moving toward hospital with incident

**Transitions**:
- idle → to_incident: Dispatch command received
- to_incident → to_hospital: Reached incident, picked up
- to_hospital → idle: Reached hospital, delivered

**State Tracking**:
- Current position (x, y)
- Target (incident or hospital)
- Carrying incident (if any)
- Path history for visualization

**Implementation**: Each ambulance maintains independent state.

### 17. Hospital System

**Description**: Fixed locations with capacity constraints for incident delivery.

**Hospital Locations**:
- Hospital 1: (20, 20), capacity 100
- Hospital 2: (80, 20), capacity 100
- Hospital 3: (50, 80), capacity 100

**Features**:
- Occupancy tracking (0-100)
- Capacity limits
- Load balancing incentives
- Cascade effects affect occupancy

**Delivery Logic**:
- Ambulance chooses nearest hospital
- Occupancy increments on delivery
- Cannot exceed capacity
- Full hospitals penalized in reward

### 18. Incident System

**Description**: Dynamic incident generation with varying severity and locations.

**Incident Properties**:
- ID: Unique identifier
- Severity: 0.3-0.9 (higher = more critical)
- Position: (x, y) coordinates (10-90, 10-90)
- Status: waiting, picked, resolved
- Assigned ambulance: ID or None
- Assigned time: Step when assigned

**Lifecycle**:
1. Spawn: Created by initial setup or cascade
2. Waiting: Available for dispatch
3. Picked: Ambulance assigned and en route
4. Resolved: Delivered to hospital, removed from list

**Severity Impact**:
- Higher severity = higher reward priority
- Ignoring high severity = fairness penalty
- Affects adaptive agent strategy

### 19. Trajectory Collection

**Description**: Data collection for offline RL training.

**Trajectory Structure**:
```python
trajectory = {
    "states": [s1, s2, s3, ...],
    "actions": [a1, a2, a3, ...],
    "rewards": [r1, r2, r3, ...],
    "dones": [d1, d2, d3, ...],
    "metadata": {
        "source": "ui" or "simulated",
        "timestamp": ISO_8601_string
    }
}
```

**Collection Methods**:
- UI-generated: Human decisions via dashboard
- Simulated: Agent decisions in environment

**Storage**: JSON format for easy access

**Use Case**: Offline RL, imitation learning, dataset analysis.

### 20. Hybrid Dataset Support

**Description**: Combining UI and simulated trajectories for balanced training.

**Balancing**:
- 30-50% UI data
- 50-70% simulated data
- Random shuffling
- Return-to-go calculation per trajectory
- Reward normalization across dataset

**Implementation**:
```python
def build_dataset(ui_trajectories, sim_trajectories):
    combined = ui_trajectories + sim_trajectories
    shuffle(combined)
    compute_returns(combined)
    normalize_rewards(combined)
    return combined
```

**Research Value**: Hybrid human-AI training, imitation learning.

## Standout Features

### Schema Drift

**Why It's Unique**:
- Most RL environments assume fixed observation/action spaces
- SECIS explicitly breaks this assumption
- Tests agent robustness to structural changes
- Graceful degradation with fallback keys

**Research Impact**:
- Domain adaptation research
- Robustness to distribution shift
- Real-world scenario: API changes, data format evolution

### Adversarial Mode

**Why It's Unique**:
- Systematic stress testing
- Configurable difficulty and adversarial level
- Weakness tracking for targeted improvement
- Cascade effects + schema drift combination

**Research Impact**:
- Adversarial robustness
- Worst-case scenario analysis
- Curriculum learning

### Multi-Agent Competition

**Why It's Unique**:
- Real-time strategy comparison
- Independent environments prevent interference
- Leaderboard provides clear metrics
- Adaptive agent demonstrates dynamic switching

**Research Impact**:
- Multi-agent RL
- Competitive evaluation
- Strategy comparison

### Multi-Objective Rewards

**Why It's Unique**:
- Sparse primary reward (hospital delivery)
- Dense shaping penalties for behavior guidance
- Normalized scores for telemetry
- Competing objectives (efficiency vs fairness)

**Research Impact**:
- Multi-objective optimization
- Reward shaping
- Pareto frontier exploration

### Coordinate-Based Movement

**Why It's Unique**:
- Spatial reasoning challenge
- Path visualization
- Realistic ambulance behavior
- Distance-based decision making

**Research Impact**:
- Spatial RL
- Path planning
- Realistic simulation

### Reflection System

**Why It's Unique**:
- Action-outcome linkage
- Reward breakdown per step
- Timestamped for temporal analysis
- Available for agent learning

**Research Impact**:
- Explainable AI
- Meta-learning
- Episodic memory

### Real-Time Dashboard

**Why It's Unique**:
- All-in-one visualization
- Real-time updates via WebSocket
- Interactive parameter control
- Comprehensive metrics display

**Research Impact**:
- Human-in-the-loop RL
- Interactive learning
- Real-time debugging

## Feature Comparison Table

| Feature | SECIS | Typical RL Environments |
|---------|-------|-------------------------|
| Schema Drift | ✅ Dynamic structural changes | ❌ Fixed observation space |
| Adversarial Mode | ✅ Configurable difficulty | ❌ Static environment |
| Multi-Agent | ✅ Competitive evaluation | ❌ Usually single agent |
| Multi-Objective | ✅ 8 reward components | ❌ Usually single objective |
| Coordinate System | ✅ 100×100 map | ❌ Grid or abstract |
| Real-Time Dashboard | ✅ Interactive UI | ❌ Usually command-line |
| Reflection System | ✅ Action logging | ❌ Limited logging |
| Safety Constraints | ✅ Pre-action validation | ❌ Rarely implemented |
| Cascade Effects | ✅ Dynamic spawning | ❌ Static episode |
| OpenEnv Compatible | ✅ Standard interface | ❌ Custom interfaces |

## Future Feature Roadmap

### Planned Features

1. **Deep RL Integration**: Train neural network policies
2. **Hierarchical Policies**: Separate high/low-level decisions
3. **Attention Mechanisms**: Focus on relevant incidents
4. **Memory Networks**: Remember past episodes
5. **Meta-Learning**: Learn to adapt quickly
6. **Inverse RL**: Learn reward from demonstrations
7. **Multi-Agent Cooperation**: Collaborative dispatch
8. **Curriculum Learning**: Adaptive difficulty
9. **Self-Play**: Agents compete against each other
10. **Transfer Learning**: Adapt to new cities

### Research Extensions

1. **Causal RL**: Understand causal relationships
2. **Continual Learning**: Adapt over time
3. **Explainable RL**: Decision justification
4. **Human-in-the-Loop**: Interactive learning
5. **Counterfactual Analysis**: What-if scenarios
6. **Multi-City Simulation**: Different city layouts
7. **Time-Varying Severity**: Dynamic incident severity
8. **Resource Constraints**: Limited fuel, maintenance
9. **Weather Effects**: Impact on ambulance speed
10. **Traffic Simulation**: Road network constraints

## Technical Specifications

### Performance Metrics

- **Max Steps**: 20 (configurable)
- **Tick Interval**: 100-5000ms (default 200ms)
- **Ambulance Speed**: 30 units/tick
- **Map Size**: 100×100 units
- **Hospital Capacity**: 100 each
- **Ambulances**: 2 per agent (6 total in multi-agent)
- **Initial Incidents**: 3-5 (based on difficulty)
- **Cascade Spawn Rate**: 0-2 per step (multi-agent)

### System Requirements

- **Python**: 3.12+
- **Dependencies**: FastAPI, uvicorn, websockets
- **Browser**: Modern browser with WebSocket support
- **Memory**: ~100MB for dashboard
- **CPU**: Minimal (simulation is lightweight)

### API Limits

- **Max Concurrent Connections**: 100
- **WebSocket Message Size**: 1MB
- **Telemetry History**: Unlimited (in-memory)
- **Reflection Log History**: Unlimited (in-memory)
