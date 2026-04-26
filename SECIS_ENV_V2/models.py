# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Secis Env V2 Environment.

The SECIS_ENV_V2 environment is a crisis management environment with
coordinate-based map system, schema drift, and multi-objective rewards.
"""

from openenv.core.env_server.types import Action, Observation
from pydantic import Field
from typing import Dict, Any, Optional


class SecisEnvV2Action(Action):
    """Action for the Secis Env V2 environment - ambulance dispatch action."""

    ambulance_id: str = Field(..., description="ID of the ambulance to dispatch")
    target: str = Field(..., description="ID of the incident to respond to")
    reason: str = Field(..., description="Reason for the action")


class SecisEnvV2Observation(Observation):
    """Observation from the Secis Env V2 environment - full crisis state."""

    state: Dict[str, Any] = Field(default_factory=dict, description="Full environment state including incidents, ambulances, hospitals")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Environment statistics")
    step: int = Field(default=0, description="Current step number")
    done: bool = Field(default=False, description="Whether the episode is done")
    reward: float = Field(default=0.0, description="Reward for this step")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata including reward breakdown")
