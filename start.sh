#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# Agent Orchestrator Server - Start Script
# ═══════════════════════════════════════════════════════════════

set -e

echo "🚀 Starting Agent Orchestrator Server..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Creating from .env.example..."
    cp .env.example .env
    echo "   Please edit .env with your credentials before running again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "✓ All dependencies installed"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Agent Orchestrator Server"
echo "  Running on http://localhost:8000"
echo "════════════════════════════════════════════════════════════"
echo ""

# Start the server
uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
