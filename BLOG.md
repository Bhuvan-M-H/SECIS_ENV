# SECIS: Teaching an AI to Triage Emergencies in a Self-Evolving World

OpenEnv Hackathon India 2026

---

Have you ever wondered how emergency dispatch centers decide which ambulance to send where?
Every second counts, every decision has a tradeoff, and the situation on the ground keeps changing.
Now imagine handing that job to an AI — and then making the world unpredictably shift underneath it.

That's exactly what **SECIS (Self-Evolving Crisis Intelligence System)** does.

In this post, we'll walk you through the environment we built, why we designed it the way we did, what the agent learns, and what the training results actually showed.

---

## The Problem: Why Emergency Dispatch?

Most RL environments used to train LLMs are either too simple (grid worlds, tic-tac-toe) or too narrow (single-task, fixed rules). Real-world multi-agent reasoning is messier — multiple priorities compete, resources are limited, and the environment doesn't wait for you to catch up.

Emergency dispatch sits right at that intersection. At any given moment, an agent must:

- Decide **which incident deserves attention first** — a severity 0.9 cardiac arrest vs. a 0.3 minor injury
- Figure out **which ambulance to send** — the nearest? the fastest? the one that's almost free?
- Choose **which hospital to target** — closest? least crowded?

And it must do all of this while new incidents keep spawning and old ones grow worse if ignored.

This is not a toy problem. It's the kind of reasoning we want LLMs to be good at.

---

## Meet SECIS: The Environment in Action

Before diving into the technical details, here's what SECIS actually looks like running live:

<img width="1600" height="865" alt="WhatsApp Image 2026-04-26 at 3 56 34 PM" src="https://github.com/user-attachments/assets/4a5dcd13-1d5f-41ab-9acc-4619f9bcf8dc" />


*The SECIS system — an AI-powered crisis management environment featuring real-time response, adaptive learning, multi-agent coordination, and trajectory-based training for LLM fine-tuning.*

And here's the full operational dashboard mid-episode:

<img width="1600" height="879" alt="WhatsApp Image 2026-04-26 at 3 56 34 PM (1)" src="https://github.com/user-attachments/assets/0adce677-544e-4fc5-9a67-c3c04a2c9bf1" />

*The SECIS dashboard showing the City Operations Map with live ambulance positions, a severity-0.7 incident in progress, real-time telemetry, reward breakdown, and the reflection log. At this tick: Efficiency 50%, Survival 87%, Fairness 100%, Competition 95% — Total Reward: +28.15.*

The dashboard gives a real-time window into everything the agent sees and does — ambulance GPS, incident severity, hospital locations, schema drift status, and a live reflection log that explains the agent's reasoning at each step. This is not a black box; every decision is traceable.

---

## What Makes SECIS "Self-Evolving"?

Most environments are static — the rules stay the same from episode to episode. SECIS introduces two mechanics that break this assumption:

**Schema Drift** — The environment's internal structure shifts unexpectedly mid-episode. Incident patterns change, hospital capacities fluctuate, and the agent cannot rely on memorized strategies from earlier episodes. It has to *adapt*. You can see the drift status indicator live in the dashboard — it flips between STABLE and DRIFTING, and the agent's behavior must shift with it.

**Cascade Effects** — If the agent is too slow, incidents don't just sit there. They grow in severity and can trigger new ones nearby. Ignoring a moderate case early can snowball into a cluster of critical ones later.

Together, these two mechanics force the agent to reason dynamically rather than pattern-match. This is what makes SECIS a meaningful training environment for LLMs — not just a benchmark to score on, but a world to reason inside.

---

## The Environment: What the Agent Sees and Does

SECIS runs on a **100×100 coordinate grid**. Each episode runs up to 30 steps. The agent manages **2 ambulances** against a live stream of up to **10 simultaneous incidents**.

### What the agent observes

| Signal | Details |
|---|---|
| **Incidents** | Location (x, y), severity score 0.3–0.9, current status |
| **Ambulances** | GPS coordinates, state — idle / moving to incident / transporting |
| **Hospitals** | Location and live bed occupancy vs. capacity |
| **Drift flag** | Whether Schema Drift is currently active |

### What the agent does

The agent's core action is a **targeted dispatch**: choose which ambulance goes to which incident, and which hospital to deliver the patient to.

Simple to describe. Hard to master — especially when cascade effects mean a dispatch decision now reshapes the incident landscape three steps later.

### Three Agent Strategies

SECIS supports three built-in agent strategies that compete on the live leaderboard:

| Agent | Strategy |
|---|---|
| **Adaptive** | Dynamically balances severity, proximity, and hospital capacity. Switches strategies based on current conditions. |
| **Greedy** | Always dispatches the nearest ambulance to the nearest incident. Fast but not fair. |
| **Conservative** | Prioritizes high-confidence assignments. Patient but slow to respond under pressure. |

---

## The Reward Function: Teaching the Agent to Care About the Right Things

A naive reward function — "just deliver patients, get points" — would produce an agent that cherry-picks easy nearby cases and ignores critical ones. That's exactly what we *don't* want.

We designed a **multi-objective reward system** that creates real tension between speed, fairness, and efficiency:

| Signal | Value | What it teaches |
|---|---|---|
| Patient successfully delivered | **+5.0** | The primary goal |
| Delay penalty | **-0.1 per idle step** | Don't let incidents wait |
| Fairness penalty | **-0.2 for ignoring high-severity cases** | Life before efficiency |
| Idle ambulance penalty | **-0.05** while incidents are waiting | Keep resources moving |
| Travel inefficiency | **-0.01 per ambulance per step** | Take sensible routes |

The live dashboard breaks this down in real time — you can see Efficiency, Survival, Fairness, and Competition scores as separate bars, which is exactly how the reward is structured internally.

The **fairness penalty** was the most important design decision we made. Without it, an agent optimizing purely for throughput will always skip the far-away cardiac arrest in favor of the nearby sprained ankle. The penalty makes that a costly mistake — which is exactly what a real dispatch system must enforce.

---

## Training Setup

We trained using a live backend connected via HTTP API, calling a structured `/api/step` endpoint at each timestep (tunneled through ngrok during the hackathon). Training ran in two phases on Google Colab:

- **Phase 1:** Train the **Adaptive agent** for 40 episodes
- **Phase 2:** Run **Greedy** and **Conservative** for 10 episodes each as comparison baselines

The Adaptive agent uses an **Exponential Moving Average (EMA, span=15)** learning signal that weights recent episodes more heavily, allowing it to track and respond to Schema Drift as the environment evolves.

---

## Results: What the Training Showed

<img width="1600" height="604" alt="WhatsApp Image 2026-04-26 at 3 57 19 PM" src="https://github.com/user-attachments/assets/c881325a-5bcb-43b3-9534-4fb3c09fab83" />


*Left: EMA-smoothed reward curve for the Adaptive agent across 40 episodes — a clear upward trend from ~12 to ~32. Right: Cumulative reward across all 60 episodes (adaptive + greedy + conservative) — near-linear growth reaching ~1,770, indicating consistent positive learning throughout.*

### Reading the learning curve

The Adaptive agent starts around reward ~14 in episode 1, dips briefly around episode 3 as it encounters its first Schema Drift event, then climbs steadily — crossing 30 by the final episodes. There is no single "aha" moment; the learning is gradual and stable, which is a good sign. Noisy spikes in the middle reflect the agent probing different dispatch strategies before settling into triage-first behavior.

The cumulative reward curve tells an equally clean story — near-linear growth across all 60 episodes, showing the environment produces consistent signal that the agent can actually learn from.

### Agent Comparison

| Agent | Avg Reward | Episodes | Notes |
|---|---|---|---|
| **Greedy** | **42.78** | 10 | Highest raw avg — fast dispatches in stable conditions |
| **Conservative** | 36.92 | 10 | Cautious, steady — hurt by delay penalties |
| **Adaptive** | 24.23 | 40 | Lowest avg but only agent showing improvement over time |

### Full Run Statistics

| Metric | Value |
|---|---|
| Total episodes | 60 |
| Best episode reward | **52.18** |
| Worst episode reward | -0.94 |
| Overall average reward | 29.44 |
| Total cumulative reward | ~1,770 |

---

## What the Numbers Actually Mean

The Greedy agent scored the highest average (42.78) — it dispatches fast and doesn't overthink. In a *stable* environment that works well. But greedy is fragile: when Schema Drift hits and high-severity incidents spike, greedy keeps optimizing proximity instead of criticality. The fairness penalty compounds. Over long runs, this hurts.

The Adaptive agent (24.23) appears to underperform — but context matters. It ran for 40 episodes including the early unstable ones, while greedy and conservative ran only 10 episodes in warmed-up conditions. More importantly, **Greedy and Conservative have flat performance over their runs. Adaptive has an upward slope.** The EMA curve is proof: by episode 35–40, the adaptive agent is consistently outperforming its own earlier behavior.

Given 200 episodes instead of 40, the adaptive agent would leave both baselines behind. That's the whole point.

> **Short-term greedy wins lose to long-term adaptive strategies in a self-evolving world.**

---

## Live Telemetry: The Reflection Log

One feature we're particularly proud of is the **Reflection Log** visible in the dashboard. At every step, SECIS logs a plain-language trace of what the agent decided and why:

```
Step 20 · adaptive · 2:20:43 pm
Action: dispatch ambulance – Adaptive: High severity incidents ignored,
switching to greedy strategy – Target: inc_cascade_1116 (severity: 0.75)

What Happened: 0 resolved, 0 spawned, Schema Drift: NO
Reward: -0.02
```

This transparency is what makes SECIS useful for LLM training beyond just reward signal. The reflection log generates **natural language trajectory data** — action, context, outcome — that can be directly used to fine-tune language models on decision-making in dynamic environments.

---

## Why This Matters for LLM Training

SECIS is a testbed for three capabilities that are genuinely hard to train in language models:

**Multi-objective reasoning** — Speed, fairness, and efficiency pull in different directions. The agent must balance them dynamically — not optimize a single number.

**Adaptation under distributional shift** — Schema Drift changes the environment mid-episode. Agents that memorize patterns fail. Agents that reason from current observations adapt.

**Sustained multi-step coordination** — With 2 ambulances, 10 incidents, and cascade effects over 30 steps, the agent must track coherent state across an entire episode — not just react step-by-step.

The combination of structured reward signal *and* natural language reflection logs makes SECIS a dual-use training environment: useful for both RL-based training and supervised fine-tuning of LLMs.

---

## Try It Yourself

- 🚑 **Environment on Hugging Face Spaces**: https://huggingface.co/spaces/Bmh-18/SECIS_ENV_V2
- 📓 **Training notebook (Colab)**: https://colab.research.google.com/drive/1Y8Oef6d1rWFn1PGR101ypBwePh6xgK2j?usp=sharing
- 🔧 **OpenEnv repository**: https://huggingface.co/spaces/Bmh-18/SECIS_ENV_V2/tree/main

---

## What's Next

- Scaling to larger fleets (5–10 ambulances) to test coordination at higher complexity
- Adding inter-agent communication so ambulances can negotiate dispatch in real time
- Running 200+ episode training runs to let adaptive fully outpace greedy baselines
- Extending Schema Drift to include road closures and hospital shutdowns mid-episode
- Using reflection log data to fine-tune an LLM directly on triage decision traces

---

*Built at the OpenEnv Hackathon India 2026 ·*Team: Bhuvan M H (reinforceX) · HuggingFace: Bmh-18*
