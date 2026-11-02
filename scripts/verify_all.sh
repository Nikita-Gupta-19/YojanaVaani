#!/usr/bin/env bash
# verify_all.sh — Pre-PR Local Health & Test Verification Script
# Run this before opening a Pull Request to make sure all tests pass.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "======================================================="
echo "🧪 Running YojanaVaani Pre-Merge Verification"
echo "======================================================="

# 1. Backend tests
echo ""
echo "▶ Running Backend Pytest Suites..."
cd "$REPO_ROOT/backend"
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
pytest tests/ -v --tb=short

# 2. Mobile tests
echo ""
echo "▶ Running Mobile Jest Test Suites..."
cd "$REPO_ROOT/mobile"
npm test -- --watchAll=false

echo ""
echo "======================================================="
echo "✅ All verification checks passed! You are ready to open a PR."
echo "======================================================="
