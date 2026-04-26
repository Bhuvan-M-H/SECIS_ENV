# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Secis Env V2 Environment.

This module creates an HTTP server that exposes the SecisEnvV2Environment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - GET /: Custom dashboard UI
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

# ============================================================================
# STANDALONE FASTAPI APP (without OpenEnv create_app to avoid conflicts)
# ============================================================================

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime
import random
import json
import os

app = FastAPI(title="SECIS Crisis Management Environment")

# Landing page HTML
LANDING_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SECIS - Crisis Management System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #e2e8f0;
            overflow-x: hidden;
            position: relative;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 50%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
            animation: pulse 8s ease-in-out infinite;
            z-index: 0;
        }
        @keyframes pulse {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }
        .particle {
            position: fixed;
            width: 4px;
            height: 4px;
            background: rgba(59, 130, 246, 0.5);
            border-radius: 50%;
            animation: float 15s infinite;
            z-index: 0;
        }
        @keyframes float {
            0%, 100% {
                transform: translateY(0) translateX(0);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(-100vh) translateX(100px);
                opacity: 0;
            }
        }
        .container {
            max-width: 1200px;
            padding: 40px;
            text-align: center;
            position: relative;
            z-index: 1;
        }
        h1 {
            font-size: 64px;
            font-weight: 800;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradient-shift 3s ease infinite;
            opacity: 0;
            animation: fadeInUp 1s ease forwards, gradient-shift 3s ease infinite;
        }
        @keyframes gradient-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .subtitle {
            font-size: 28px;
            color: #94a3b8;
            margin-bottom: 40px;
            opacity: 0;
            animation: fadeInUp 1s ease 0.2s forwards;
        }
        .description {
            font-size: 18px;
            color: #cbd5e1;
            line-height: 1.8;
            max-width: 800px;
            margin: 0 auto 40px;
            opacity: 0;
            animation: fadeInUp 1s ease 0.4s forwards;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin: 40px 0;
            opacity: 0;
            animation: fadeInUp 1s ease 0.6s forwards;
        }
        .feature {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 16px;
            padding: 32px 24px;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
        }
        .feature::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, transparent 50%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .feature:hover::before {
            opacity: 1;
        }
        .feature:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: rgba(59, 130, 246, 0.5);
            box-shadow: 0 20px 40px rgba(59, 130, 246, 0.2);
        }
        .feature-icon {
            font-size: 48px;
            margin-bottom: 20px;
            display: inline-block;
            animation: bounce 2s ease infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        .feature-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #e2e8f0;
            position: relative;
            z-index: 1;
        }
        .feature-desc {
            font-size: 15px;
            color: #94a3b8;
            line-height: 1.6;
            position: relative;
            z-index: 1;
        }
        .cta-button {
            display: inline-block;
            padding: 20px 48px;
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
            background-size: 200% 200%;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.4s ease;
            box-shadow: 0 8px 30px rgba(59, 130, 246, 0.4);
            position: relative;
            overflow: hidden;
            opacity: 0;
            animation: fadeInUp 1s ease 0.8s forwards;
        }
        .cta-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            animation: shine 3s infinite;
        }
        @keyframes shine {
            0% { left: -100%; }
            50%, 100% { left: 100%; }
        }
        .cta-button:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(59, 130, 246, 0.5);
            background-position: 100% 50%;
        }
        .footer {
            margin-top: 80px;
            padding-top: 24px;
            border-top: 1px solid rgba(59, 130, 246, 0.2);
            color: #64748b;
            font-size: 14px;
            opacity: 0;
            animation: fadeInUp 1s ease 1s forwards;
        }
        .glow-text {
            text-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        }
    </style>
</head>
<body>
    <div class="particles">
        <div class="particle" style="left: 10%; animation-delay: 0s;"></div>
        <div class="particle" style="left: 20%; animation-delay: 2s;"></div>
        <div class="particle" style="left: 30%; animation-delay: 4s;"></div>
        <div class="particle" style="left: 40%; animation-delay: 6s;"></div>
        <div class="particle" style="left: 50%; animation-delay: 8s;"></div>
        <div class="particle" style="left: 60%; animation-delay: 10s;"></div>
        <div class="particle" style="left: 70%; animation-delay: 12s;"></div>
        <div class="particle" style="left: 80%; animation-delay: 14s;"></div>
        <div class="particle" style="left: 90%; animation-delay: 16s;"></div>
    </div>
    
    <div class="container">
        <h1 class="glow-text">SECIS</h1>
        <p class="subtitle">Self-Adaptive Crisis Management System</p>
        <p class="description">
            An AI-powered crisis management system that adapts to real-time emergencies, 
            optimizes resource allocation, and learns from experience to improve response strategies.
        </p>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🚑</div>
                <div class="feature-title">Real-time Response</div>
                <div class="feature-desc">Dynamic ambulance dispatch and incident management with intelligent routing</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🧠</div>
                <div class="feature-title">Adaptive Learning</div>
                <div class="feature-desc">AI agents that learn and improve from experience using trajectory-based training</div>
            </div>
            <div class="feature">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Multi-Agent Coordination</div>
                <div class="feature-desc">Greedy, Conservative, and Adaptive agents working together seamlessly</div>
            </div>
            <div class="feature">
                <div class="feature-icon">📈</div>
                <div class="feature-title">Trajectory Training</div>
                <div class="feature-desc">Generate training data for advanced language model fine-tuning</div>
            </div>
        </div>
        
        <a href="/web" class="cta-button">Launch Dashboard</a>
        
        <div class="footer">
            SECIS Crisis Management System • Built for Emergency Response Optimization
        </div>
    </div>
</body>
</html>
"""

# Add custom dashboard UI route
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Serve the landing page"""
    return HTMLResponse(content=LANDING_HTML)

@app.get("/web", response_class=HTMLResponse)
async def dashboard():
    """Serve the custom dashboard UI"""
    return HTMLResponse(content=FRONTEND_HTML)


# ============================================================================
# CUSTOM DASHBOARD UI (HTML/CSS/JS)
# ============================================================================

FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SECIS Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        .dashboard-container {
            min-height: 100vh;
            background: linear-gradient(135deg, #0a0e1a 0%, #0f172a 50%, #0a0e1a 100%);
            color: #e2e8f0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
        }

        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 24px;
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(10, 14, 26, 0.98) 100%);
            border-bottom: 2px solid rgba(59, 130, 246, 0.3);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
        }

        .header-left {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .logo {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: 2px;
            background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 50%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            text-shadow: 0 0 30px rgba(59, 130, 246, 0.5);
        }

        .subtitle {
            font-size: 12px;
            color: #64748b;
            margin: 0;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .header-right {
            display: flex;
            gap: 24px;
            align-items: center;
        }

        .header-metric {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            padding: 8px 16px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 8px;
            min-width: 80px;
        }

        .metric-label {
            font-size: 10px;
            color: #64748b;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .metric-value {
            font-size: 14px;
            font-weight: 700;
            color: #e2e8f0;
        }

        .status-stable {
            color: #10b981;
            text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        }

        .status-active {
            color: #ef4444;
            text-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
        }

        .toggle-on {
            color: #06b6d4;
            text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
        }

        .dashboard-main {
            display: grid;
            grid-template-columns: 320px 1fr 320px;
            gap: 0;
            height: calc(100vh - 80px);
            overflow: hidden;
        }

        .left-panel {
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.9) 0%, rgba(10, 14, 26, 0.95) 100%);
            border-right: 2px solid rgba(59, 130, 246, 0.2);
            padding: 20px;
            overflow-y: auto;
            overflow-x: hidden;
            display: flex;
            flex-direction: column;
            gap: 16px;
            height: calc(100vh - 80px);
        }

        .center-panel {
            display: flex;
            flex-direction: column;
            gap: 16px;
            padding: 20px;
            background: linear-gradient(180deg, rgba(10, 14, 26, 0.95) 0%, rgba(15, 23, 42, 0.9) 100%);
            overflow-y: auto;
        }

        .map-section {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .section-header h2 {
            font-size: 18px;
            font-weight: 700;
            color: #e2e8f0;
            margin: 0;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .learning-metrics {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }

        .metrics-title {
            font-size: 14px;
            font-weight: 600;
            color: #94a3b8;
            margin: 0 0 12px 0;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }

        .metric-box {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }

        .metric-box-label {
            font-size: 11px;
            color: #64748b;
            display: block;
            margin-bottom: 8px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .metric-comparison {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-size: 16px;
            font-weight: 700;
        }

        .metric-after {
            color: #06b6d4;
            text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
        }

        .right-panel {
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.9) 0%, rgba(10, 14, 26, 0.95) 100%);
            border-left: 2px solid rgba(59, 130, 246, 0.2);
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .panel-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }

        .panel-card h3 {
            font-size: 14px;
            font-weight: 700;
            color: #e2e8f0;
            margin: 0 0 16px 0;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .control-buttons {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }

        .control-btn {
            flex: 1;
            min-width: 120px;
            padding: 10px 16px;
            border: none;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            letter-spacing: 1px;
        }

        .start-btn {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            border: 1px solid rgba(34, 197, 94, 0.5);
        }

        .start-btn:hover {
            background: rgba(34, 197, 94, 0.3);
            box-shadow: 0 0 15px rgba(34, 197, 94, 0.3);
        }

        .pause-btn {
            background: rgba(234, 179, 8, 0.2);
            color: #eab308;
            border: 1px solid rgba(234, 179, 8, 0.5);
        }

        .pause-btn:hover {
            background: rgba(234, 179, 8, 0.3);
            box-shadow: 0 0 15px rgba(234, 179, 8, 0.3);
        }

        .reset-btn {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.5);
        }

        .reset-btn:hover {
            background: rgba(239, 68, 68, 0.3);
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
        }

        .control-sliders {
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin-bottom: 16px;
        }

        .slider-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .slider-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: #94a3b8;
        }

        .slider-value {
            font-weight: 700;
            color: #06b6d4;
        }

        .slider-input {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: rgba(59, 130, 246, 0.2);
            outline: none;
            -webkit-appearance: none;
        }

        .slider-input::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #06b6d4;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
        }

        .agent-selection {
            margin-bottom: 16px;
        }

        .selection-label {
            font-size: 11px;
            color: #64748b;
            display: block;
            margin-bottom: 8px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .agent-buttons {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .agent-btn {
            flex: 1;
            min-width: 80px;
            padding: 8px 8px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 6px;
            font-size: 10px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            background: rgba(30, 41, 59, 0.6);
            color: #94a3b8;
            white-space: nowrap;
        }

        .agent-btn:hover {
            border-color: rgba(59, 130, 246, 0.5);
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
        }

        .agent-btn.active {
            background: rgba(6, 182, 212, 0.2);
            color: #06b6d4;
            border-color: rgba(6, 182, 212, 0.5);
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.2);
        }

        .multi-agent-toggle {
            margin-bottom: 8px;
        }

        .toggle-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: #94a3b8;
        }

        .toggle-switch {
            width: 44px;
            height: 24px;
            border-radius: 12px;
            border: none;
            cursor: pointer;
            position: relative;
            transition: all 0.3s ease;
            background: rgba(59, 130, 246, 0.2);
            border: 1px solid rgba(59, 130, 246, 0.3);
        }

        .toggle-switch.on {
            background: rgba(6, 182, 212, 0.3);
            border-color: rgba(6, 182, 212, 0.5);
        }

        .toggle-switch.off {
            background: rgba(71, 85, 105, 0.3);
            border-color: rgba(71, 85, 105, 0.5);
        }

        .toggle-slider {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #94a3b8;
            transition: all 0.3s ease;
        }

        .toggle-switch.on .toggle-slider {
            left: 22px;
            background: #06b6d4;
            box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
        }

        .drift-status {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
        }

        .drift-status.stable {
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .drift-status.active {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: blink 2s ease-in-out infinite;
        }

        .status-indicator.stable {
            background: #10b981;
        }

        .status-indicator.active {
            background: #ef4444;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .drift-message {
            margin-top: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            color: #ef4444;
        }

        .metrics-progress {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 16px;
        }

        .metric-progress-item {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
        }

        .metric-name {
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .metric-percent {
            font-weight: 700;
            color: #e2e8f0;
        }

        .progress-bar {
            height: 6px;
            background: rgba(59, 130, 246, 0.2);
            border-radius: 3px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }

        .total-reward-box {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }

        .total-reward-label {
            font-size: 11px;
            color: #64748b;
            display: block;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .total-reward-value {
            font-size: 24px;
            font-weight: 800;
            display: block;
        }

        .total-reward-value.positive {
            color: #22c55e;
            text-shadow: 0 0 20px rgba(34, 197, 94, 0.5);
        }

        .total-reward-value.negative {
            color: #ef4444;
            text-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
        }

        .safety-status {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 14px;
            font-weight: 800;
        }

        .safety-status.pass {
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .safety-status.fail {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .status-icon {
            font-size: 18px;
        }

        .safety-checklist {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .check-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: rgba(30, 41, 59, 0.6);
            border-radius: 6px;
            font-size: 11px;
        }

        .check-icon {
            font-size: 12px;
            font-weight: 800;
        }

        .check-icon.pass {
            color: #10b981;
        }

        .check-icon.fail {
            color: #ef4444;
        }

        .check-label {
            color: #94a3b8;
        }

        .map-container {
            flex: 1;
            background: rgba(10, 14, 26, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 12px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            min-height: 400px;
        }

        .road-background {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            pointer-events: none;
        }

        .map-entity {
            position: absolute;
            transform: translate(-50%, -50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .map-entity:hover {
            z-index: 100;
            transform: translate(-50%, -50%) scale(1.1);
        }

        .entity-icon {
            font-size: 24px;
            filter: drop-shadow(0 0 10px rgba(59, 130, 246, 0.5));
        }

        .entity-icon.pulse {
            animation: pulse 2s ease-in-out infinite;
        }

        .entity-label {
            font-size: 9px;
            color: #e2e8f0;
            background: rgba(15, 23, 42, 0.9);
            padding: 2px 6px;
            border-radius: 4px;
            white-space: nowrap;
        }

        .hospital .entity-icon {
            font-size: 32px;
        }

        .incident .entity-icon {
            font-size: 36px;
            filter: drop-shadow(0 0 15px rgba(239, 68, 68, 0.7));
        }

        .ambulance .entity-icon {
            font-size: 32px;
            transition: all 0.3s ease-out;
        }

        .ambulance-icon {
            filter: drop-shadow(0 0 10px rgba(59, 130, 246, 0.5));
        }

        .ambulance-icon.greedy {
            filter: drop-shadow(0 0 10px rgba(234, 179, 8, 0.7));
        }

        .ambulance-icon.conservative {
            filter: drop-shadow(0 0 10px rgba(168, 85, 247, 0.7));
        }

        .ambulance-icon.adaptive {
            filter: drop-shadow(0 0 10px rgba(6, 182, 212, 0.7));
        }

        .leaderboard-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .leaderboard-item {
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding: 8px;
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 6px;
            transition: all 0.3s ease;
        }

        .leaderboard-item:hover {
            border-color: rgba(59, 130, 246, 0.5);
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
        }

        .leaderboard-item.leading {
            border-color: rgba(6, 182, 212, 0.5);
            box-shadow: 0 0 12px rgba(6, 182, 212, 0.2);
        }

        .agent-badge {
            font-size: 10px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .agent-badge.adaptive {
            background: rgba(6, 182, 212, 0.2);
            color: #06b6d4;
            border: 1px solid rgba(6, 182, 212, 0.5);
        }

        .agent-badge.conservative {
            background: rgba(168, 85, 247, 0.2);
            color: #a855f7;
            border: 1px solid rgba(168, 85, 247, 0.5);
        }

        .agent-badge.greedy {
            background: rgba(234, 179, 8, 0.2);
            color: #eab308;
            border: 1px solid rgba(234, 179, 8, 0.5);
        }

        .agent-stats {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .stat {
            font-size: 9px;
            color: #94a3b8;
        }

        .reflection-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: 200px;
            max-height: 400px;
        }

        .reflection-log {
            flex: 1;
            overflow-y: auto;
            padding-right: 8px;
            min-height: 200px;
            max-height: calc(100vh - 200px);
        }

        .reflection-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .reflection-item {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 8px;
            padding: 12px;
        }

        .reflection-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
            font-size: 10px;
        }

        .reflection-step {
            color: #06b6d4;
            font-weight: 700;
        }

        .reflection-agent {
            color: #94a3b8;
        }

        .reflection-timestamp {
            color: #64748b;
            margin-left: auto;
        }

        .reflection-details {
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 11px;
        }

        .reflection-details p {
            margin: 0;
            color: #e2e8f0;
        }

        .reflection-details strong {
            color: #94a3b8;
        }

        .no-data {
            text-align: center;
            color: #64748b;
            font-size: 12px;
            padding: 20px;
        }

        .telemetry-card {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            max-height: 400px;
            overflow-y: auto;
        }

        .telemetry-charts-container {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .telemetry-chart {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(59, 130, 246, 0.1);
            border-radius: 8px;
            padding: 12px;
        }

        .chart-title {
            margin: 0 0 8px 0;
            font-size: 11px;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .chart-canvas {
            width: 100%;
            height: 100px;
        }

        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.5);
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(59, 130, 246, 0.3);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(59, 130, 246, 0.5);
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <div class="header-left">
                <h1 class="logo">SECIS</h1>
                <p class="subtitle">Self-Evolving Adaptive Crisis Agent</p>
            </div>
            <div class="header-right">
                <div class="header-metric">
                    <span class="metric-label">TICK</span>
                    <span class="metric-value" id="tick-counter">0000</span>
                </div>
                <div class="header-metric">
                    <span class="metric-label">SCHEMA DRIFT</span>
                    <span class="metric-value status-stable" id="schema-drift-status">STABLE</span>
                </div>
                <div class="header-metric">
                    <span class="metric-label">DIFFICULTY</span>
                    <span class="metric-value" id="difficulty-value">0.50</span>
                </div>
                <div class="header-metric">
                    <span class="metric-label">DEMO MODE</span>
                    <span class="metric-value toggle-on">ON</span>
                </div>
            </div>
        </header>

        <div class="dashboard-main">
            <aside class="left-panel">
                <div class="panel-card controls-card">
                    <h3>Controls</h3>
                    <div class="control-buttons">
                        <button class="control-btn start-btn" id="start-btn">▶ Start</button>
                        <button class="control-btn reset-btn" id="reset-btn">↻ Reset</button>
                    </div>
                    <div class="control-sliders">
                        <div class="slider-group">
                            <label class="slider-label">
                                <span>Difficulty</span>
                                <span class="slider-value" id="slider-difficulty-value">0.50</span>
                            </label>
                            <input type="range" class="slider-input" id="difficulty-slider" min="0" max="1" step="0.1" value="0.5">
                        </div>
                        <div class="slider-group">
                            <label class="slider-label">
                                <span>Adversarial Level</span>
                                <span class="slider-value" id="slider-adversarial-value">0.50</span>
                            </label>
                            <input type="range" class="slider-input" id="adversarial-slider" min="0" max="1" step="0.1" value="0.5">
                        </div>
                        <div class="slider-group">
                            <label class="slider-label">
                                <span>Tick Interval (ms)</span>
                                <span class="slider-value" id="slider-tick-value">1000</span>
                            </label>
                            <input type="range" class="slider-input" id="tick-slider" min="100" max="5000" step="100" value="1000">
                        </div>
                    </div>
                    <div class="agent-selection" id="agent-selection">
                        <label class="selection-label">Agent Type</label>
                        <div class="agent-buttons">
                            <button class="agent-btn active" data-agent="adaptive">Adaptive</button>
                            <button class="agent-btn" data-agent="greedy">Greedy</button>
                            <button class="agent-btn" data-agent="conservative">Conservative</button>
                        </div>
                    </div>
                    <div class="multi-agent-toggle">
                        <label class="toggle-label">
                            <span>Multi-Agent Mode</span>
                            <button class="toggle-switch off" id="multi-agent-toggle">
                                <span class="toggle-slider"></span>
                            </button>
                        </label>
                    </div>
                </div>

                <div class="panel-card schema-drift-card">
                    <h3>Schema Drift</h3>
                    <div class="drift-status stable" id="drift-status">
                        <span class="status-indicator stable" id="drift-indicator"></span>
                        <span class="status-text" id="drift-text">STABLE</span>
                    </div>
                    <div class="drift-message" id="drift-message" style="display: none;">
                        <span class="drift-icon">⚠️</span>
                        <span>Schema structure has shifted</span>
                    </div>
                </div>

                <div class="panel-card reward-breakdown-card">
                    <h3>Reward Breakdown · <span id="reward-agent-type">Adaptive</span></h3>
                    <div class="metrics-progress">
                        <div class="metric-progress-item">
                            <div class="metric-header">
                                <span class="metric-name">Efficiency</span>
                                <span class="metric-percent" id="efficiency-percent">0%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" id="efficiency-bar" style="width: 0%; background-color: #06b6d4; box-shadow: 0 0 10px rgba(6, 182, 212, 0.25);"></div>
                            </div>
                        </div>
                        <div class="metric-progress-item">
                            <div class="metric-header">
                                <span class="metric-name">Survival</span>
                                <span class="metric-percent" id="survival-percent">0%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" id="survival-bar" style="width: 0%; background-color: #22c55e; box-shadow: 0 0 10px rgba(34, 197, 94, 0.25);"></div>
                            </div>
                        </div>
                        <div class="metric-progress-item">
                            <div class="metric-header">
                                <span class="metric-name">Fairness</span>
                                <span class="metric-percent" id="fairness-percent">0%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" id="fairness-bar" style="width: 0%; background-color: #a855f7; box-shadow: 0 0 10px rgba(168, 85, 247, 0.25);"></div>
                            </div>
                        </div>
                        <div class="metric-progress-item">
                            <div class="metric-header">
                                <span class="metric-name">Competition</span>
                                <span class="metric-percent" id="competition-percent">0%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" id="competition-bar" style="width: 0%; background-color: #eab308; box-shadow: 0 0 10px rgba(234, 179, 8, 0.25);"></div>
                            </div>
                        </div>
                    </div>
                    <div class="total-reward-box">
                        <span class="total-reward-label">Total Reward</span>
                        <span class="total-reward-value positive" id="total-reward">+0.00</span>
                    </div>
                </div>

                <div class="panel-card safety-card">
                    <h3>Safety Checks</h3>
                    <div class="safety-status pass" id="safety-status">
                        <span class="status-icon">✓</span>
                        <span class="status-text" id="safety-text">PASS</span>
                    </div>
                    <div class="safety-checklist">
                        <div class="check-item">
                            <span class="check-icon pass" id="check-idle">✓</span>
                            <span class="check-label">No Idle Resource Abuse</span>
                        </div>
                        <div class="check-item">
                            <span class="check-icon pass" id="check-invalid">✓</span>
                            <span class="check-label">No Invalid Dispatch</span>
                        </div>
                        <div class="check-item">
                            <span class="check-icon pass" id="check-repeated">✓</span>
                            <span class="check-label">No Repeated Actions</span>
                        </div>
                    </div>
                </div>
            </aside>

            <main class="center-panel">
                <div class="map-section">
                    <div class="section-header">
                        <h2>City Operations Map</h2>
                    </div>
                    <div class="map-container" id="map-container">
                        <svg class="road-background" viewBox="0 0 100 100" preserveAspectRatio="none">
                            <line x1="0" y1="20" x2="100" y2="20" stroke="rgba(100, 116, 139, 0.15)" stroke-width="0.8" />
                            <line x1="0" y1="40" x2="100" y2="40" stroke="rgba(100, 116, 139, 0.15)" stroke-width="0.8" />
                            <line x1="0" y1="60" x2="100" y2="60" stroke="rgba(100, 116, 139, 0.15)" stroke-width="0.8" />
                            <line x1="0" y1="80" x2="100" y2="80" stroke="rgba(100, 116, 139, 0.15)" stroke-width="0.8" />
                            <line x1="20" y1="0" x2="20" y2="100" stroke="rgba(100, 116, 139, 0.15)" stroke-width="0.8" />
                            <line x1="40" y1="0" x2="40" y2="100" stroke="rgba(100, 116, 139, 0.15)" stroke-width="0.8" />
                            <line x1="60" y1="0" x2="60" y2="100" stroke="rgba(100, 116, 139, 0.15)" stroke-width="0.8" />
                            <line x1="80" y1="0" x2="80" y2="100" stroke="rgba(100, 116, 139, 0.15)" stroke-width="0.8" />
                        </svg>
                        <div id="map-entities"></div>
                    </div>
                </div>

                <div class="learning-metrics">
                    <h3 class="metrics-title">Adaptive · Learning Progress</h3>
                    <div class="metrics-grid">
                        <div class="metric-box">
                            <span class="metric-box-label">Avg Response Time</span>
                            <div class="metric-comparison">
                                <span class="metric-after" id="avg-response-time">0.0s</span>
                            </div>
                        </div>
                        <div class="metric-box">
                            <span class="metric-box-label">Avg Survival Rate</span>
                            <div class="metric-comparison">
                                <span class="metric-after" id="avg-survival-rate">0%</span>
                            </div>
                        </div>
                        <div class="metric-box">
                            <span class="metric-box-label">Total Incidents Resolved</span>
                            <div class="metric-comparison">
                                <span class="metric-after" id="total-resolved">0</span>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <aside class="right-panel">
                <div class="panel-card leaderboard-card">
                    <h3>Leaderboard</h3>
                    <div class="leaderboard-list" id="leaderboard-list">
                        <div class="no-data">No leaderboard data available</div>
                    </div>
                </div>

                <div class="panel-card telemetry-card">
                    <h3>Telemetry · Last 20 Steps</h3>
                    <div class="telemetry-charts-container" id="telemetry-charts">
                        <div class="no-data">No telemetry data available</div>
                    </div>
                </div>

                <div class="panel-card reflection-card">
                    <h3>Reflection Log</h3>
                    <div class="reflection-log" id="reflection-log">
                        <div class="no-data">No reflection logs available</div>
                    </div>
                </div>
            </aside>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        let state = {
            running: false,
            agentType: 'adaptive',
            multiAgentMode: false,
            tick: 0,
            driftFlag: false,
            difficulty: 0.5,
            adversarialLevel: 0.5,
            tickInterval: 1000,
            totalReward: 0,
            rewardBreakdown: { efficiency: 0, survival: 0, fairness: 0, competition: 0 },
            safetyFlags: { no_idle_resource_abuse: true, no_invalid_dispatch: true, no_repeated_actions: true },
            currentStep: 0,
            telemetry: [],
            leaderboard: [],
            reflectionLogs: [],
            mapState: null
        };

        let intervalId = null;
        let refreshIntervalId = null;
        let rewardChart = null;
        let incidentsChart = null;
        let responseChart = null;

        const API_BASE = '';

        async function fetchState() {
            try {
                const response = await fetch(`${API_BASE}/api/state`);
                const data = await response.json();
                state.mapState = data.state;
                state.driftFlag = data.drift_flag || false;
                updateUI();
            } catch (error) {
                console.error('Error fetching state:', error);
            }
        }

        async function fetchControlParameters() {
            try {
                const response = await fetch(`${API_BASE}/api/control-parameters`);
                const data = await response.json();
                state.difficulty = data.control_parameters.difficulty || 0.5;
                state.adversarialLevel = data.control_parameters.adversarial_level || 0.5;
                state.tickInterval = data.control_parameters.tick_interval || 1000;
                updateControlSliders();
            } catch (error) {
                console.error('Error fetching control parameters:', error);
            }
        }

        async function updateControlParameters(params) {
            try {
                await fetch(`${API_BASE}/api/control-parameters`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params)
                });
            } catch (error) {
                console.error('Error updating control parameters:', error);
            }
        }

        async function step() {
            try {
                const response = await fetch(`${API_BASE}/api/step`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ agent_type: state.agentType, multi_agent: state.multiAgentMode })
                });
                const data = await response.json();
                
                if (!data) {
                    console.error('Received null response from server');
                    return;
                }
                
                if (data.multi_agent) {
                    state.currentStep = data.step || 0;
                    const allAmbulances = [];
                    const allHospitals = data.agents.adaptive?.state?.hospitals || [];
                    const allIncidents = data.agents.adaptive?.state?.incidents || [];
                    
                    Object.keys(data.agents).forEach(agentName => {
                        const agentState = data.agents[agentName].state;
                        if (agentState && agentState.ambulances) {
                            const agentAmbulances = agentState.ambulances.map(amb => ({
                                ...amb,
                                id: `${agentName}_${amb.id}`,
                                agentName: agentName
                            }));
                            allAmbulances.push(...agentAmbulances);
                        }
                    });
                    
                    state.mapState = {
                        hospitals: allHospitals,
                        incidents: allIncidents,
                        ambulances: allAmbulances,
                        map_size: 100
                    };
                    state.driftFlag = data.agents.adaptive?.drift_flag || false;
                    
                    if (data.done) {
                        toggleRunning();
                    }
                } else {
                    state.mapState = data.state;
                    state.currentStep = data.step || 0;
                    const reward = data.reward || 0;
                    state.totalReward += reward;
                    state.driftFlag = data.drift_flag || false;
                    
                    if (data.safety_flags) {
                        state.safetyFlags = data.safety_flags;
                    }
                    
                    if (data.metadata?.reward_breakdown) {
                        const breakdown = data.metadata.reward_breakdown;
                        state.rewardBreakdown = {
                            efficiency: breakdown.efficiency_score || 0,
                            fairness: breakdown.fairness_score || 0,
                            survival: breakdown.survival_score || 0,
                            competition: breakdown.competition_score || 0
                        };
                    }
                    
                    if (data.done) {
                        toggleRunning();
                    }
                }
                
                state.tick = state.currentStep;
                updateUI();
            } catch (error) {
                console.error('Error stepping:', error);
            }
        }

        async function reset() {
            try {
                await fetch(`${API_BASE}/api/reset`, { method: 'POST' });
                await fetch(`${API_BASE}/api/reflection`, { method: 'DELETE' });
                
                state.running = false;
                state.tick = 0;
                state.totalReward = 0;
                
                if (state.multiAgentMode) {
                    state.agentScores = { greedy: 0, conservative: 0, adaptive: 0 };
                }
                
                state.currentStep = 0;
                state.mapState = null;
                
                if (intervalId) {
                    clearInterval(intervalId);
                    intervalId = null;
                }
                
                await fetchState();
                updateUI();
            } catch (error) {
                console.error('Error resetting:', error);
            }
        }

        async function fetchTelemetry() {
            try {
                const response = await fetch(`${API_BASE}/api/telemetry`);
                const data = await response.json();
                state.telemetry = data.telemetry || [];
                updateTelemetry();
                updateLearningMetrics();
            } catch (error) {
                console.error('Error fetching telemetry:', error);
            }
        }

        async function fetchLeaderboard() {
            try {
                const response = await fetch(`${API_BASE}/api/leaderboard`);
                const data = await response.json();
                state.leaderboard = data.leaderboard || [];
                updateLeaderboard();
            } catch (error) {
                console.error('Error fetching leaderboard:', error);
            }
        }

        async function fetchReflectionLogs() {
            try {
                const response = await fetch(`${API_BASE}/api/reflection`);
                const data = await response.json();
                state.reflectionLogs = data.reflections || [];
                updateReflectionLog();
            } catch (error) {
                console.error('Error fetching reflection logs:', error);
            }
        }

        function toggleRunning() {
            state.running = !state.running;
            const btn = document.getElementById('start-btn');
            
            if (state.running) {
                btn.textContent = '⏸ Pause';
                btn.classList.remove('start-btn');
                btn.classList.add('pause-btn');
                intervalId = setInterval(step, state.tickInterval);
            } else {
                btn.textContent = '▶ Start';
                btn.classList.remove('pause-btn');
                btn.classList.add('start-btn');
                if (intervalId) {
                    clearInterval(intervalId);
                    intervalId = null;
                }
            }
        }

        function updateControlSliders() {
            document.getElementById('difficulty-slider').value = state.difficulty;
            document.getElementById('slider-difficulty-value').textContent = state.difficulty.toFixed(2);
            document.getElementById('difficulty-value').textContent = state.difficulty.toFixed(2);
            
            document.getElementById('adversarial-slider').value = state.adversarialLevel;
            document.getElementById('slider-adversarial-value').textContent = state.adversarialLevel.toFixed(2);
            
            document.getElementById('tick-slider').value = state.tickInterval;
            document.getElementById('slider-tick-value').textContent = state.tickInterval;
        }

        function updateUI() {
            document.getElementById('tick-counter').textContent = String(state.tick).padStart(4, '0');
            
            const driftStatus = document.getElementById('schema-drift-status');
            const driftIndicator = document.getElementById('drift-indicator');
            const driftText = document.getElementById('drift-text');
            const driftStatusCard = document.getElementById('drift-status');
            const driftMessage = document.getElementById('drift-message');
            
            if (state.driftFlag) {
                driftStatus.textContent = 'ACTIVE';
                driftStatus.classList.remove('status-stable');
                driftStatus.classList.add('status-active');
                driftIndicator.classList.remove('stable');
                driftIndicator.classList.add('active');
                driftText.textContent = 'ACTIVE';
                driftStatusCard.classList.remove('stable');
                driftStatusCard.classList.add('active');
                driftMessage.style.display = 'flex';
            } else {
                driftStatus.textContent = 'STABLE';
                driftStatus.classList.remove('status-active');
                driftStatus.classList.add('status-stable');
                driftIndicator.classList.remove('active');
                driftIndicator.classList.add('stable');
                driftText.textContent = 'STABLE';
                driftStatusCard.classList.remove('active');
                driftStatusCard.classList.add('stable');
                driftMessage.style.display = 'none';
            }
            
            document.getElementById('total-reward').textContent = (state.totalReward >= 0 ? '+' : '') + state.totalReward.toFixed(2);
            document.getElementById('total-reward').className = 'total-reward-value ' + (state.totalReward >= 0 ? 'positive' : 'negative');
            
            document.getElementById('efficiency-percent').textContent = state.rewardBreakdown.efficiency.toFixed(0) + '%';
            document.getElementById('efficiency-bar').style.width = state.rewardBreakdown.efficiency + '%';
            
            document.getElementById('survival-percent').textContent = state.rewardBreakdown.survival.toFixed(0) + '%';
            document.getElementById('survival-bar').style.width = state.rewardBreakdown.survival + '%';
            
            document.getElementById('fairness-percent').textContent = state.rewardBreakdown.fairness.toFixed(0) + '%';
            document.getElementById('fairness-bar').style.width = state.rewardBreakdown.fairness + '%';
            
            document.getElementById('competition-percent').textContent = state.rewardBreakdown.competition.toFixed(0) + '%';
            document.getElementById('competition-bar').style.width = state.rewardBreakdown.competition + '%';
            
            const allPassed = Object.values(state.safetyFlags).every(v => v);
            const safetyStatus = document.getElementById('safety-status');
            const safetyText = document.getElementById('safety-text');
            
            if (allPassed) {
                safetyStatus.classList.remove('fail');
                safetyStatus.classList.add('pass');
                safetyText.textContent = 'PASS';
                safetyStatus.querySelector('.status-icon').textContent = '✓';
            } else {
                safetyStatus.classList.remove('pass');
                safetyStatus.classList.add('fail');
                safetyText.textContent = 'FAIL';
                safetyStatus.querySelector('.status-icon').textContent = '✗';
            }
            
            document.getElementById('check-idle').textContent = state.safetyFlags.no_idle_resource_abuse ? '✓' : '✗';
            document.getElementById('check-idle').className = 'check-icon ' + (state.safetyFlags.no_idle_resource_abuse ? 'pass' : 'fail');
            
            document.getElementById('check-invalid').textContent = state.safetyFlags.no_invalid_dispatch ? '✓' : '✗';
            document.getElementById('check-invalid').className = 'check-icon ' + (state.safetyFlags.no_invalid_dispatch ? 'pass' : 'fail');
            
            document.getElementById('check-repeated').textContent = state.safetyFlags.no_repeated_actions ? '✓' : '✗';
            document.getElementById('check-repeated').className = 'check-icon ' + (state.safetyFlags.no_repeated_actions ? 'pass' : 'fail');
            
            updateMap();
        }

        function updateMap() {
            const container = document.getElementById('map-entities');
            container.innerHTML = '';
            
            if (!state.mapState) {
                return;
            }
            
            const { hospitals, incidents, ambulances } = state.mapState;
            
            (hospitals || []).forEach(hospital => {
                const el = document.createElement('div');
                el.className = 'map-entity hospital';
                el.style.left = hospital.x + '%';
                el.style.top = hospital.y + '%';
                el.innerHTML = `<div class="entity-icon">🏥</div><div class="entity-label">HOSP</div>`;
                container.appendChild(el);
            });
            
            (incidents || []).filter(inc => inc.status !== 'resolved').forEach(incident => {
                const el = document.createElement('div');
                el.className = 'map-entity incident ' + incident.status;
                el.style.left = incident.x + '%';
                el.style.top = incident.y + '%';
                el.innerHTML = `<div class="entity-icon pulse">🚨</div><div class="entity-label">S: ${incident.severity?.toFixed(1)}</div>`;
                container.appendChild(el);
            });
            
            (ambulances || []).forEach(ambulance => {
                const el = document.createElement('div');
                el.className = 'map-entity ambulance ' + ambulance.state + ' ' + (ambulance.agentName || '');
                el.style.left = ambulance.x + '%';
                el.style.top = ambulance.y + '%';
                const agentName = ambulance.agentName || 'adaptive';
                el.innerHTML = `<div class="entity-icon ambulance-icon ${agentName}">🚑</div><div class="entity-label">${agentName.toUpperCase()}</div>`;
                container.appendChild(el);
            });
        }

        function updateLearningMetrics() {
            if (state.telemetry.length === 0) {
                document.getElementById('avg-response-time').textContent = '0.0s';
                document.getElementById('avg-survival-rate').textContent = '0%';
                document.getElementById('total-resolved').textContent = '0';
                return;
            }
            
            const avgResponseTime = state.telemetry.reduce((sum, t) => sum + (t?.response_time || 0), 0) / state.telemetry.length;
            const avgSurvival = state.telemetry.reduce((sum, t) => sum + (t?.survival || 0), 0) / state.telemetry.length;
            const totalResolved = state.telemetry.reduce((sum, t) => sum + (t?.hospital_deliveries || 0), 0);
            
            document.getElementById('avg-response-time').textContent = avgResponseTime.toFixed(1) + 's';
            document.getElementById('avg-survival-rate').textContent = avgSurvival.toFixed(0) + '%';
            document.getElementById('total-resolved').textContent = totalResolved;
        }

        function updateLeaderboard() {
            const container = document.getElementById('leaderboard-list');
            
            if (state.leaderboard.length === 0) {
                container.innerHTML = '<div class="no-data">No leaderboard data available</div>';
                return;
            }
            
            container.innerHTML = '';
            state.leaderboard.forEach((entry, index) => {
                const el = document.createElement('div');
                el.className = 'leaderboard-item ' + (index === 0 ? 'leading' : '');
                el.innerHTML = `
                    <span class="agent-badge ${entry.agent.toLowerCase()}">${entry.agent.charAt(0).toUpperCase() + entry.agent.slice(1)}</span>
                    <div class="agent-stats">
                        <span class="stat">Reward: ${entry.score.toFixed(1)}</span>
                        <span class="stat">Resolved: ${entry.resolved || 0}</span>
                        <span class="stat">Avg: ${(entry.avg || 0).toFixed(1)}</span>
                    </div>
                `;
                container.appendChild(el);
            });
        }

        function updateTelemetry() {
            const container = document.getElementById('telemetry-charts');
            
            if (state.telemetry.length === 0) {
                container.innerHTML = '<div class="no-data">No telemetry data available</div>';
                return;
            }
            
            const telemetryData = state.telemetry.slice(-20).map((entry, index) => ({
                step: state.telemetry.length - 20 + index + 1,
                reward: entry.reward,
                incidents: entry.incident_count,
                responseTime: entry.response_time
            }));
            
            // Destroy old chart instances
            if (rewardChart) rewardChart.destroy();
            if (incidentsChart) incidentsChart.destroy();
            if (responseChart) responseChart.destroy();
            
            container.innerHTML = `
                <div class="telemetry-chart">
                    <h4 class="chart-title">Reward</h4>
                    <canvas class="chart-canvas" id="reward-chart" style="height: 80px;"></canvas>
                </div>
                <div class="telemetry-chart">
                    <h4 class="chart-title">Incidents</h4>
                    <canvas class="chart-canvas" id="incidents-chart" style="height: 80px;"></canvas>
                </div>
                <div class="telemetry-chart">
                    <h4 class="chart-title">Response Time (s)</h4>
                    <canvas class="chart-canvas" id="response-chart" style="height: 80px;"></canvas>
                </div>
            `;
            
            const chartOptions = {
                responsive: false,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { display: false },
                    y: { 
                        display: true,
                        grid: { color: 'rgba(71, 85, 105, 0.2)' },
                        ticks: { color: '#64748b', font: { size: 9 } },
                        suggestedMin: -10,
                        suggestedMax: 10
                    }
                },
                animation: {
                    duration: 0
                }
            };
            
            rewardChart = new Chart(document.getElementById('reward-chart'), {
                type: 'line',
                data: {
                    labels: telemetryData.map(d => d.step),
                    datasets: [{
                        data: telemetryData.map(d => d.reward),
                        borderColor: '#06b6d4',
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0
                    }]
                },
                options: chartOptions
            });
            
            incidentsChart = new Chart(document.getElementById('incidents-chart'), {
                type: 'line',
                data: {
                    labels: telemetryData.map(d => d.step),
                    datasets: [{
                        data: telemetryData.map(d => d.incidents),
                        borderColor: '#ef4444',
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0
                    }]
                },
                options: chartOptions
            });
            
            responseChart = new Chart(document.getElementById('response-chart'), {
                type: 'line',
                data: {
                    labels: telemetryData.map(d => d.step),
                    datasets: [{
                        data: telemetryData.map(d => d.responseTime),
                        borderColor: '#eab308',
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 0
                    }]
                },
                options: chartOptions
            });
        }

        function updateReflectionLog() {
            const container = document.getElementById('reflection-log');
            
            if (state.reflectionLogs.length === 0) {
                container.innerHTML = '<div class="no-data">No reflection logs available</div>';
                return;
            }
            
            container.innerHTML = '';
            state.reflectionLogs.slice().reverse().slice(0, 10).forEach(log => {
                const el = document.createElement('div');
                el.className = 'reflection-item';
                el.innerHTML = `
                    <div class="reflection-header">
                        <span class="reflection-step">Step ${log.step}</span>
                        <span class="reflection-agent">${log.agent}</span>
                        <span class="reflection-timestamp">${new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div class="reflection-details">
                        <p><strong>Action:</strong> ${log.action.type} - ${log.action.reason}</p>
                        <p><strong>What Happened:</strong> ${log.what_happened.incidents_resolved} resolved, ${log.what_happened.incidents_spawned} spawned, ${log.what_happened.schema_drift ? 'Schema Drift: YES' : 'Schema Drift: NO'}</p>
                        <p><strong>Reward:</strong> ${log.reward.total.toFixed(2)}</p>
                    </div>
                `;
                container.appendChild(el);
            });
        }

        document.getElementById('start-btn').addEventListener('click', toggleRunning);
        document.getElementById('reset-btn').addEventListener('click', reset);

        document.getElementById('difficulty-slider').addEventListener('input', (e) => {
            state.difficulty = parseFloat(e.target.value);
            document.getElementById('slider-difficulty-value').textContent = state.difficulty.toFixed(2);
            document.getElementById('difficulty-value').textContent = state.difficulty.toFixed(2);
            updateControlParameters({ difficulty: state.difficulty });
        });

        document.getElementById('adversarial-slider').addEventListener('input', (e) => {
            state.adversarialLevel = parseFloat(e.target.value);
            document.getElementById('slider-adversarial-value').textContent = state.adversarialLevel.toFixed(2);
            updateControlParameters({ adversarial_level: state.adversarialLevel });
        });

        document.getElementById('tick-slider').addEventListener('input', (e) => {
            state.tickInterval = parseInt(e.target.value);
            document.getElementById('slider-tick-value').textContent = state.tickInterval;
            updateControlParameters({ tick_interval: state.tickInterval });
            
            if (state.running) {
                clearInterval(intervalId);
                intervalId = setInterval(step, state.tickInterval);
            }
        });

        document.querySelectorAll('.agent-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.agent-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.agentType = btn.dataset.agent;
                document.getElementById('reward-agent-type').textContent = state.agentType.charAt(0).toUpperCase() + state.agentType.slice(1);
            });
        });

        document.getElementById('multi-agent-toggle').addEventListener('click', (e) => {
            state.multiAgentMode = !state.multiAgentMode;
            e.currentTarget.classList.toggle('on', state.multiAgentMode);
            e.currentTarget.classList.toggle('off', !state.multiAgentMode);
            
            const agentSelection = document.getElementById('agent-selection');
            agentSelection.style.display = state.multiAgentMode ? 'none' : 'block';
            
            reset();
        });

        fetchState();
        fetchControlParameters();
        fetchTelemetry();
        fetchLeaderboard();
        fetchReflectionLogs();

        refreshIntervalId = setInterval(() => {
            fetchReflectionLogs();
            fetchTelemetry();
            fetchLeaderboard();
            fetchState();
        }, 1500);
    </script>
</body>
</html>
"""


# ============================================================================
# BACKEND INTEGRATION - Using local SECIS_ENV_V2_environment
# ============================================================================

from pydantic import BaseModel
from typing import Optional

class StepRequest(BaseModel):
    agent_type: str = "adaptive"
    multi_agent: bool = False

class ControlParametersRequest(BaseModel):
    difficulty: Optional[float] = None
    adversarial_level: Optional[float] = None
    tick_interval: Optional[int] = None

# Initialize backend components
_crisis_env = None
_multi_agent_env = None
_greedy_agent = None
_conservative_agent = None
_llm_agent = None
_telemetry_history = []
_telemetry_log_file = "logs/telemetry.json"

def save_telemetry_to_file():
    """Save telemetry data to file for trajectory generation"""
    global _telemetry_history
    os.makedirs("logs", exist_ok=True)
    with open(_telemetry_log_file, "w") as f:
        json.dump(_telemetry_history, f, indent=2)

def init_backend():
    """Initialize backend components"""
    global _crisis_env, _multi_agent_env, _greedy_agent, _conservative_agent, _llm_agent, _telemetry_history
    if _crisis_env is None:
        try:
            from backend.env.crisis_env import CrisisEnv
            from backend.env.multi_agent_env import MultiAgentEnv
            from backend.agent.greedy_agent import GreedyAgent
            from backend.agent.conservative_agent import ConservativeAgent
            from backend.agent.llm_agent import LLMAgent
            from backend.training.safety import check_safety_constraints
            from backend.logs.reflection_logger import log_step_reflection, get_reflection_logs, clear_reflection_logs
            
            _crisis_env = CrisisEnv(max_steps=20, ambulances_per_agent=2, agent_name="agent", single_agent_mode=True)
            _multi_agent_env = MultiAgentEnv(max_steps=20)
            _greedy_agent = GreedyAgent()
            _conservative_agent = ConservativeAgent()
            _llm_agent = LLMAgent()
            _telemetry_history = []
        except Exception as e:
            print(f"Error initializing backend from backend folder: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to SECIS_ENV_V2_environment
            from server.SECIS_ENV_V2_environment import CrisisEnv, MultiAgentEnv, GreedyAgent, ConservativeAgent, LLMAgent
            _crisis_env = CrisisEnv(max_steps=20, ambulances_per_agent=2, agent_name="agent", single_agent_mode=True)
            _multi_agent_env = MultiAgentEnv(max_steps=20)
            _greedy_agent = GreedyAgent()
            _conservative_agent = ConservativeAgent()
            _llm_agent = LLMAgent()
            _telemetry_history = []

@app.post("/api/reset")
async def reset_environment():
    """Reset environment"""
    global _telemetry_history
    init_backend()
    _crisis_env.reset()
    _multi_agent_env.reset()
    _greedy_agent.reset_episode()
    _conservative_agent.reset_episode()
    _llm_agent.reset_episode()
    _telemetry_history = []
    return {"message": "Environment reset successfully", "observation": {"state": _crisis_env.current_state, "stats": _crisis_env.get_stats(), "step": 0, "done": False}}

@app.post("/api/step")
async def step_environment(request: StepRequest):
    """Execute one step with specified agent"""
    global _telemetry_history
    init_backend()
    
    if request.multi_agent:
        # Multi-agent mode
        actions = {
            "greedy": _greedy_agent.act(_multi_agent_env.environments["greedy"].current_state),
            "conservative": _conservative_agent.act(_multi_agent_env.environments["conservative"].current_state),
            "adaptive": _llm_agent.act(_multi_agent_env.environments["adaptive"].current_state)
        }
        results = _multi_agent_env.step_all(actions)
        
        # Add telemetry data for multi-agent mode
        for agent_name, agent_result in results["agents"].items():
            stats = agent_result.get("stats", {})
            reward_breakdown = agent_result.get("metadata", {}).get("reward_breakdown", {})
            hospital_occupancy = stats.get("hospital_occupied", 0) / max(1, stats.get("hospital_capacity", 100)) * 100
            telemetry_entry = {
                "timestamp": datetime.now().isoformat(),
                "step": results["step"],
                "reward": agent_result.get("reward", 0),
                "incident_count": len(agent_result.get("state", {}).get("incidents", [])),
                "response_time": random.uniform(1.0, 5.0),
                "overflow": stats.get("hospital_occupied", 0) >= stats.get("hospital_capacity", 100),
                "efficiency": reward_breakdown.get("efficiency_score", 0),
                "fairness": reward_breakdown.get("fairness_score", 0),
                "survival": reward_breakdown.get("survival_score", 0),
                "hospital_deliveries": stats.get("hospital_deliveries", 0),
                "hospital_occupancy": hospital_occupancy,
                "agent": agent_name,
                # Add raw state and action for trajectory generation
                "state": agent_result.get("state", {}),
                "action": actions.get(agent_name, {})
            }
            _telemetry_history.append(telemetry_entry)
        
        # Save telemetry to file for trajectory generation
        save_telemetry_to_file()
        
        # Log reflection for each agent
        try:
            from backend.logs.reflection_logger import log_step_reflection
        except:
            from server.SECIS_ENV_V2_environment import log_step_reflection
        
        for agent_name, agent_result in results["agents"].items():
            try:
                log_step_reflection(
                    step=results["step"],
                    agent_name=agent_name,
                    action=actions.get(agent_name, {}),
                    state=agent_result.get("state", {}),
                    reward=agent_result.get("reward", 0),
                    reward_breakdown=agent_result.get("metadata", {}).get("reward_breakdown", {}),
                    resolved_incidents=agent_result.get("metadata", {}).get("resolved_incidents", 0),
                    new_incidents=agent_result.get("metadata", {}).get("new_incidents", 0),
                    schema_drift=agent_result.get("drift_flag", False),
                    metadata=agent_result.get("metadata", {})
                )
            except:
                pass
        
        # Auto-generate trajectories when simulation completes (multi-agent mode)
        try:
            if results["done"]:
                try:
                    import subprocess
                    subprocess.run(["python", "generate_trajectory_dataset.py"], 
                                  capture_output=True, text=True, 
                                  cwd="c:/Users/Bhuvan M H/Desktop/windsurf-project/windsurf-project/SECIS/SECIS_ENV_V2")
                    print("Trajectories auto-generated after simulation completion")
                except Exception as e:
                    print(f"Error auto-generating trajectories: {e}")
        except NameError:
            pass  # results not defined in case of error
        
        return {
            "multi_agent": True,
            "step": results["step"],
            "done": results["done"],
            "agents": results["agents"]
        }
    
    else:
        # Single-agent mode
        if request.agent_type == "greedy":
            agent = _greedy_agent
        elif request.agent_type == "conservative":
            agent = _conservative_agent
        else:
            agent = _llm_agent
        
        action = agent.act(_crisis_env.current_state)
        
        # Check safety constraints
        try:
            from backend.training.safety import check_safety_constraints
        except:
            from server.SECIS_ENV_V2_environment import check_safety_constraints
        try:
            is_safe, safety_reason, safety_flags = check_safety_constraints(action, _crisis_env.current_state)
        except:
            is_safe, safety_reason, safety_flags = True, "", {
                "no_idle_resource_abuse": True,
                "no_invalid_dispatch": True,
                "no_repeated_actions": True
            }
        
        if not is_safe:
            return {
                "multi_agent": False,
                "error": safety_reason,
                "state": _crisis_env.current_state,
                "reward": 0.0,
                "done": False,
                "safety_flags": safety_flags
            }
        
        state, reward, done, metadata = _crisis_env.step(action)
        
        # Add agentName to ambulances for frontend rendering
        state_with_agent = state.copy()
        if "ambulances" in state_with_agent:
            state_with_agent["ambulances"] = [
                {**amb, "agentName": request.agent_type} for amb in state_with_agent["ambulances"]
            ]
        
        stats = _crisis_env.get_stats()
        
        # Log telemetry
        stats = _crisis_env.get_stats()
        # Extract reward breakdown for telemetry metrics
        reward_breakdown = metadata.get("reward_breakdown", {})
        hospital_occupancy = stats.get("hospital_occupied", 0) / max(1, stats.get("hospital_capacity", 100)) * 100
        
        telemetry_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": _crisis_env.current_step,
            "reward": reward,
            "incident_count": len(state_with_agent.get("incidents", [])),
            "response_time": random.uniform(1.0, 5.0),
            "overflow": stats.get("hospital_occupied", 0) >= stats.get("hospital_capacity", 100),
            "efficiency": reward_breakdown.get("efficiency_score", 0),
            "fairness": reward_breakdown.get("fairness_score", 0),
            "survival": reward_breakdown.get("survival_score", 0),
            "hospital_deliveries": metadata.get("resolved_incidents", 0),
            "hospital_occupancy": hospital_occupancy,
            # Add raw state and action for trajectory generation
            "state": state_with_agent,
            "action": action
        }
        _telemetry_history.append(telemetry_entry)
        
        # Save telemetry to file for trajectory generation
        save_telemetry_to_file()
        
        # Log reflection
        try:
            from backend.logs.reflection_logger import log_step_reflection
        except:
            from server.SECIS_ENV_V2_environment import log_step_reflection
        try:
            log_step_reflection(
                step=_crisis_env.current_step,
                agent_name=request.agent_type,
                action=action,
                state=state_with_agent,
                reward=reward,
                reward_breakdown=metadata.get("reward_breakdown", {}),
                resolved_incidents=metadata.get("resolved_incidents", 0),
                new_incidents=metadata.get("new_incidents", 0),
                schema_drift=_crisis_env.drift_flag,
                metadata=metadata
            )
        except:
            pass
        
        return {
            "multi_agent": False,
            "step": _crisis_env.current_step,
            "observation": {
                "state": state_with_agent,
                "stats": stats,
                "step": _crisis_env.current_step,
                "done": done,
                "reward": reward,
                "metadata": metadata
            },
            "state": state_with_agent,
            "reward": reward,
            "done": done,
            "metadata": metadata,
            "action": action,
            "agent_type": request.agent_type,
            "stats": stats,
            "safety_flags": safety_flags,
            "drift_flag": _crisis_env.drift_flag if hasattr(_crisis_env, 'drift_flag') else False
        }
        
        # Auto-generate trajectories when simulation completes (single-agent mode)
        try:
            if done:
                try:
                    import subprocess
                    subprocess.run(["python", "generate_trajectory_dataset.py"], 
                                  capture_output=True, text=True, 
                                  cwd="c:/Users/Bhuvan M H/Desktop/windsurf-project/windsurf-project/SECIS/SECIS_ENV_V2")
                    print("Trajectories auto-generated after simulation completion")
                except Exception as e:
                    print(f"Error auto-generating trajectories: {e}")
        except NameError:
            pass  # done not defined in case of error

@app.get("/api/trajectories")
async def get_trajectories():
    """Get trajectory dataset file"""
    try:
        with open("dataset/trajectories.json", "r") as f:
            return HTMLResponse(content=f.read(), media_type="application/json")
    except FileNotFoundError:
        return {"message": "No trajectories file found. Run simulation first."}

@app.get("/api/state")
async def get_state():
    """Get current environment state"""
    init_backend()
    return {
        "state": _crisis_env.current_state,
        "stats": _crisis_env.get_stats(),
        "step": _crisis_env.current_step,
        "done": _crisis_env.done,
        "drift_flag": _crisis_env.drift_flag if hasattr(_crisis_env, 'drift_flag') else False
    }

@app.get("/api/telemetry")
async def get_telemetry():
    """Get telemetry data"""
    global _telemetry_history
    init_backend()
    return {"telemetry": _telemetry_history}

@app.get("/api/leaderboard")
async def get_leaderboard():
    """Get leaderboard"""
    init_backend()
    leaderboard = _multi_agent_env.get_leaderboard()
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    return {"leaderboard": leaderboard}

@app.get("/api/reflection")
async def get_reflection():
    """Get reflection logs"""
    try:
        from backend.logs.reflection_logger import get_reflection_logs
    except:
        from server.SECIS_ENV_V2_environment import get_reflection_logs
    try:
        reflections = get_reflection_logs()
        return {"reflections": reflections}
    except:
        return {"reflections": []}

@app.delete("/api/reflection")
async def clear_reflection():
    """Clear reflection logs"""
    try:
        from backend.logs.reflection_logger import clear_reflection_logs
    except:
        from server.SECIS_ENV_V2_environment import clear_reflection_logs
    clear_reflection_logs()
    return {"message": "Reflection logs cleared successfully"}

@app.get("/api/control-parameters")
async def get_control_parameters():
    """Get control parameters"""
    init_backend()
    params = _crisis_env.get_control_parameters()
    return {"control_parameters": params}

@app.put("/api/control-parameters")
async def update_control_parameters(request: ControlParametersRequest):
    """Update control parameters"""
    init_backend()
    _crisis_env.set_control_parameters(
        difficulty=request.difficulty,
        adversarial_level=request.adversarial_level,
        tick_interval=request.tick_interval
    )
    _multi_agent_env.set_control_parameters(
        difficulty=request.difficulty,
        adversarial_level=request.adversarial_level,
        tick_interval=request.tick_interval
    )
    updated_params = _crisis_env.get_control_parameters()
    return {
        "message": "Control parameters updated successfully",
        "control_parameters": updated_params
    }

@app.post("/api/add-trajectory")
async def add_trajectory(trajectory: dict):
    """Add a single trajectory to the hybrid dataset"""
    try:
        from dataset_builder import TrajectoryDataset
        
        # Initialize dataset builder
        builder = TrajectoryDataset("dataset/hybrid_trajectories.json")
        
        # Load existing trajectories
        existing = builder.load_trajectories()
        
        # Mark as UI-generated
        trajectory["metadata"] = trajectory.get("metadata", {})
        trajectory["metadata"]["source"] = "ui"
        trajectory["metadata"]["timestamp"] = datetime.now().isoformat()
        
        # Add to dataset
        builder.trajectories = existing + [trajectory]
        
        # Save
        builder.save_trajectories()
        
        return {
            "message": "Trajectory added successfully",
            "total_trajectories": len(builder.trajectories)
        }
    except Exception as e:
        return {"message": f"Error adding trajectory: {str(e)}"}

@app.get("/api/hybrid-trajectories")
async def get_hybrid_trajectories():
    """Get hybrid trajectory dataset"""
    try:
        with open("dataset/hybrid_trajectories.json", "r") as f:
            data = json.load(f)
        return {"trajectories": data, "count": len(data)}
    except FileNotFoundError:
        return {"trajectories": [], "count": 0, "message": "No hybrid trajectories found"}


def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution via uv run or python -m.

    This function enables running the server without Docker:
        uv run --project . server
        uv run --project . server --port 8001
        python -m SECIS_ENV_V2.server.app

    Args:
        host: Host address to bind to (default: "0.0.0.0")
        port: Port number to listen on (default: 8000)

    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn SECIS_ENV_V2.server.app:app --workers 4
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)
