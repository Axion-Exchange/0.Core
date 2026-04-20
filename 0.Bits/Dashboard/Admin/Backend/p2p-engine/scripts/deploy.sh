#!/bin/bash
set -e
cd /data/PearV2
git add src/services/order_orchestrator.py
git commit -m "fix: add missing import logging to order_orchestrator.py" || true
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no' git push origin main
echo "---PUSH DONE---"
