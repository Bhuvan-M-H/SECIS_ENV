# SECIS Implementation Details

## Reinforcement Learning Integration

SECIS is designed as a reinforcement learning (RL) environment that follows the standard OpenAI Gym/OpenEnv interface, making it compatible with various RL algorithms and libraries.

### RL Environment Interface

The environment implements the standard RL API:

```python
class CrisisEnv:
    def reset() -> state: Dict[str, Any]
    def step(action: Dict[str, Any]) -> Tuple[state, reward, done, info]
```

**State Space**: Dictionary containing:
- `incidents`: List of incident objects with coordinates and severity
- `ambulances`: List of ambulance objects with positions and states
- `hospitals`: List of hospital objects with coordinates and occupancy
- `map_size`: Integer (100x100 coordinate plane)
- `resources`: Resource availability
- `system_state`: System-level metrics

**Action Space**: Dictionary containing:
- `ambulance_id`: ID of ambulance to dispatch
- `target`: ID of incident to respond to
- `reason`: Text explanation of decision

**Reward Space**: Continuous float value (multi-objective reward)

**Done Signal**: Boolean indicating episode termination

## Markov Decision Process (MDP) Formulation

### State Representation

SECIS implements a partially observable MDP where the state includes:

1. **Observable State**: Positions, statuses, counts
2. **Hidden State**: Future incident spawns, schema drift timing
3. **Dynamic State**: Changes over time with cascade effects

### Transition Function

The transition function `T(s'|s,a)` models:
- Deterministic ambulance movement (physics-based)
- Stochastic incident spawning (cascade effects)
- Stochastic schema drift (structural changes)
- Deterministic hospital delivery

Mathematical representation:
```
s' = T(s,a) = move_ambulances(s,a) + cascade(s) + drift(s) + deliver(s)
```

### Reward Function

The reward function `R(s,a)` implements multi-objective optimization:
```
R(s,a) = w1·R_delivery + w2·R_efficiency + w3·R_fairness + w4·R_survival + penalties
```

Where:
- `R_delivery = 5.0 × delivered_incidents`
- `R_efficiency = -0.01 × active_ambulances`
- `R_fairness = -0.2 × ignored_high_severity`
- `R_survival = derived from response_time`
- `penalties` include resource, load balance, delay, duplicate dispatch

### Policy

Agents implement policies `π(a|s)`:

1. **Greedy Policy**: `π_greedy(a|s) = argmax_a severity(a)`
2. **Conservative Policy**: `π_conservative(a|s) = last_incident(s)`
3. **Adaptive Policy**: `π_adaptive(a|s) = switch(s) × π_greedy + (1-switch(s)) × π_conservative`

## Implementation Details

### Coordinate-Based Movement System

**Implementation**: Euclidean distance-based movement with smooth interpolation

```python
def _move_towards_target(ambulance, target_x, target_y):
    dx = target_x - ambulance["x"]
    dy = target_y - ambulance["y"]
    distance = sqrt(dx² + dy²)
    
    speed = 30.0  # units per tick
    move_x = (dx / distance) * min(speed, distance)
    move_y = (dy / distance) * min(speed, distance)
    
    ambulance["x"] += move_x
    ambulance["y"] += move_y
```

**Design Rationale**: Smooth movement provides realistic ambulance behavior and enables path visualization.

### State Machine Implementation

**Ambulance State Machine**:
```python
states = ["idle", "to_incident", "to_hospital"]

transitions = {
    "idle": {"dispatch": "to_incident"},
    "to_incident": {"reached": "to_hospital"},
    "to_hospital": {"delivered": "idle"}
}
```

**Implementation**: Each ambulance maintains its state, target, and path history for visualization.

### Schema Drift Implementation

**Challenge**: RL agents typically assume fixed observation/action spaces. Schema drift breaks this assumption.

**Solution**: Graceful degradation with fallback keys:
```python
def get_incidents(state):
    return state.get("incidents", state.get("incident_list", []))
```

**Implementation Details**:
- Random probability check each step
- Toggle between key names
- Add/remove optional fields
- Agents must handle both structures

**RL Implication**: Tests agent robustness to distribution shift and structural changes.

### Cascade Effects Implementation

**Challenge**: Non-stationary environment where incident count changes dynamically.

**Solution**: Probabilistic incident spawning:
```python
if random.random() < cascade_probability:
    num_new = random.randint(0, 2)
    for _ in range(num_new):
        incidents.append(create_new_incident())
```

**Implementation Details**:
- Probability scales with difficulty parameter
- Spawn rate differs for single vs multi-agent mode
- New incidents have random coordinates and severity
- Also affects hospital occupancy randomly

**RL Implication**: Tests agent adaptation to non-stationary environments.

### Multi-Objective Reward Implementation

**Challenge**: Balancing competing objectives (efficiency, fairness, survival, competition).

**Solution**: Weighted sum with normalized scores:
```python
total_reward = (
    delivery_reward +
    travel_penalty +
    resource_penalty +
    fairness_penalty +
    load_balance_penalty +
    incident_penalty +
    duplicate_dispatch_penalty +
    delay_penalty
)
```

**Implementation Details**:
- Primary reward: hospital delivery (+5.0)
- Penalties: small negative values to shape behavior
- Normalized scores (0-100%) for telemetry
- Weakness tracking for adversarial mode

**RL Implication**: Multi-objective optimization with sparse primary reward and dense shaping penalties.

### Adversarial Training Implementation

**Challenge**: Training agents that can handle worst-case scenarios.

**Solution**: Weakness tracking and adversarial parameter adjustment:
```python
weakness_tracker = {
    "prioritization_failures": count(reward < -1.0),
    "delays": count(incidents > 5),
    "ignored_high_severity": sum(inc.severity > 0.7)
}
```

**Implementation Details**:
- Track failures over episode
- Use for difficulty adjustment
- Influence schema drift probability
- Reflect in reflection logs

**RL Implication**: Adversarial training for robustness.

### Safety Constraint Implementation

**Challenge**: Prevent invalid or harmful actions.

**Solution**: Pre-action validation:
```python
def check_safety_constraints(action, state):
    # Check for idle ambulances
    if not idle_ambulances:
        return False, "No idle ambulances"
    
    # Check for valid target
    if target not in incident_ids:
        return False, "Invalid target"
    
    # Check for repeated actions
    if is_repeat(action):
        return False, "Repeated action"
    
    return True, "Action safe"
```

**Implementation Details**:
- Three safety constraints
- Returns boolean, reason, and flags
- Integrated into step function
- Displayed in dashboard

**RL Implication**: Constrained RL with action validation.

### Multi-Agent Implementation

**Challenge**: Evaluating multiple strategies simultaneously.

**Solution**: Parallel environment management:
```python
class MultiAgentEnv:
    def __init__(self):
        self.environments = {
            "greedy": CrisisEnv(agent_name="greedy"),
            "conservative": CrisisEnv(agent_name="conservative"),
            "adaptive": CrisisEnv(agent_name="adaptive")
        }
    
    def step_all(self, actions):
        results = {}
        for agent_name, env in self.environments.items():
            state, reward, done, info = env.step(actions[agent_name])
            results[agent_name] = {...}
        return results
```

**Implementation Details**:
- 3 separate environment instances
- Shared control parameters
- Synchronized step execution
- Independent ambulance fleets
- Leaderboard aggregation

**RL Implication**: Multi-agent RL with competitive evaluation.

### Reflection System Implementation

**Challenge**: Enabling agents to learn from past decisions.

**Solution**: Action logging with outcome tracking:
```python
reflection_log = {
    "timestamp": current_time,
    "action": {
        "type": action_type,
        "target": target_id,
        "reason": explanation
    },
    "what_happened": {
        "incidents_resolved": count,
        "incidents_spawned": count,
        "schema_drift": bool
    },
    "reward": {
        "total": total_reward,
        "breakdown": {...}
    }
}
```

**Implementation Details**:
- Log every action and outcome
- Store in memory for analysis
- Display in dashboard
- Available for agent learning

**RL Implication**: Episodic memory and meta-learning.

### Telemetry Implementation

**Challenge**: Real-time performance monitoring.

**Solution**: Metric collection and visualization:
```python
telemetry = {
    "step": current_step,
    "reward": step_reward,
    "incident_count": len(incidents),
    "response_time": average_response_time,
    "hospital_occupancy": occupancy_percentage
}
```

**Implementation Details**:
- Collect metrics each step
- Store in list for history
- Display in Chart.js graphs
- Export for analysis

**RL Implication**: Performance monitoring and debugging.

## RL Concepts Applied

### 1. Exploration vs Exploitation

**Implementation**: 
- Greedy agent: Pure exploitation (always highest severity)
- Conservative agent: Safe exploration (last incident)
- Adaptive agent: Contextual switching

**Trade-off**: 
- Greedy maximizes immediate reward
- Conservative provides safety margin
- Adaptive balances both based on state

### 2. Sparse vs Dense Rewards

**Implementation**:
- Sparse: Hospital delivery (+5.0) - only on successful completion
- Dense: Small penalties for suboptimal behavior (-0.01 to -0.2)

**Design Rationale**: 
- Sparse reward guides primary objective
- Dense rewards shape intermediate behavior

### 3. Credit Assignment

**Challenge**: Which action deserves credit for hospital delivery?

**Implementation**:
- Reward assigned on hospital delivery step
- Weakness tracking assigns blame for failures
- Reflection logs link actions to outcomes

### 4. Temporal Credit Assignment

**Challenge**: Actions taken earlier affect future rewards.

**Implementation**:
- Return-to-go calculation (for trajectory training)
- Delay penalty for long response times
- Cumulative reward tracking

### 5. Partial Observability

**Implementation**:
- Observable: Current positions, counts, statuses
- Hidden: Future spawns, drift timing
- Agents must infer from patterns

### 6. Non-Stationarity

**Implementation**:
- Cascade effects: Incident count changes
- Schema drift: Observation space changes
- Difficulty: Dynamic parameter adjustment

**Challenge**: Standard RL assumes stationarity.

**Solution**: Robust agent design with graceful degradation.

### 7. Multi-Agent RL

**Implementation**:
- Cooperative: Not implemented (agents compete)
- Competitive: Leaderboard comparison
- Independent: Each agent has own environment

**Design Choice**: Competitive evaluation for research, not cooperative MARL.

### 8. Hierarchical RL

**Potential Application**:
- High-level: Which incident to prioritize
- Low-level: Which ambulance to dispatch
- Currently: Flattened to single action

### 9. Curriculum Learning

**Implementation**:
- Difficulty parameter (0-1)
- Start low, increase gradually
- Adaptive: Adjust based on performance

### 10. Imitation Learning

**Potential Application**:
- Collect human trajectories via UI
- Train model on human demonstrations
- Hybrid with RL for fine-tuning

## Training Pipeline Integration

### Trajectory Collection

**Implementation**:
```python
trajectory = {
    "states": [s1, s2, s3, ...],
    "actions": [a1, a2, a3, ...],
    "rewards": [r1, r2, r3, ...],
    "dones": [d1, d2, d3, ...],
    "metadata": {
        "source": "ui" or "simulated",
        "timestamp": ...
    }
}
```

**Purpose**: Collect data for offline RL training.

### Return-to-Go Calculation

**Implementation**:
```python
def compute_returns(rewards, gamma=0.99):
    returns = []
    R = 0
    for r in reversed(rewards):
        R = r + gamma * R
        returns.insert(0, R)
    return returns
```

**Purpose**: Value-based RL methods.

### Dataset Building

**Implementation**:
- Combine UI and simulated trajectories
- Balance sources (30-50% UI, 50-70% simulated)
- Normalize rewards across dataset
- Shuffle for training

### Model Training

**Integration**: Compatible with:
- Decision Transformer (sequence learning)
- PPO (policy gradient)
- DQN (value-based)
- Offline RL (CQL, IQL)

**Notebook**: `secis_training_colab.ipynb` provides example training pipeline.

## Performance Optimization

### Efficient Distance Calculations

**Optimization**: Euclidean distance with early exit
```python
def distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) < 0.1 and abs(dy) < 0.1:
        return 0  # Early exit
    return sqrt(dx² + dy²)
```

### Path Tracking Limit

**Optimization**: Limit path history to 100 points
```python
if len(ambulance["path"]) > 100:
    ambulance["path"] = ambulance["path"][-100:]
```

### Incident Cleanup

**Optimization**: Remove incidents after delivery
```python
if incident in incidents:
    incidents.remove(incident)
```

### Batch Processing

**Optimization**: Process all agents in single step
```python
for agent_name, env in self.environments.items():
    env.step(actions[agent_name])
```

## Testing and Validation

### Unit Tests

**Components to test**:
- Distance calculations
- State transitions
- Reward calculations
- Safety constraints
- Schema drift logic

### Integration Tests

**Scenarios**:
- Full episode execution
- Multi-agent mode
- Schema drift handling
- Cascade effects

### Validation Metrics

**Metrics**:
- Episode reward
- Incidents resolved
- Response time
- Hospital utilization
- Agent comparison

## Debugging Tools

### Reflection Logs

**Purpose**: Trace decision-making process
```python
log = {
    "action": {...},
    "what_happened": {...},
    "reward": {...}
}
```

### Telemetry Graphs

**Purpose**: Visualize performance over time
- Reward vs step
- Incidents vs step
- Response time vs step

### Safety Flags

**Purpose**: Identify constraint violations
- No idle resource abuse
- No invalid dispatch
- No repeated actions

## Future RL Enhancements

### Potential Improvements

1. **Deep RL Integration**: Train neural network policies
2. **Hierarchical Policies**: Separate high/low-level decisions
3. **Attention Mechanisms**: Focus on relevant incidents
4. **Memory Networks**: Remember past episodes
5. **Meta-Learning**: Learn to adapt quickly
6. **Inverse RL**: Learn reward from demonstrations
7. **Multi-Objective RL**: Pareto optimization
8. **Curriculum Learning**: Adaptive difficulty
9. **Self-Play**: Agents compete against each other
10. **Transfer Learning**: Adapt to new cities

### Research Directions

1. **Robustness to Schema Drift**: Formal analysis
2. **Adversarial Training**: Systematic weakness exploitation
3. **Multi-Agent Cooperation**: Collaborative dispatch
4. **Human-in-the-Loop**: Interactive learning
5. **Explainable RL**: Decision justification
6. **Causal RL**: Understand causal relationships
7. **Continual Learning**: Adapt over time
