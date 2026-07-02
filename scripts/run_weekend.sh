#!/usr/bin/env bash
# Weekend precompute — scheduled for Friday 15:00
# Runs Friday → Monday (64h window).
#
# Estimated timeline (sequential, single GPU):
#   ~21h  RaidForums C (top-5000 users, top-50 posts)
#   ~13h  HF D comparison (top-300 per forum × 5 forums, top-100 posts)
#   ~19h  HF E comparison (top-300 per forum × 5 forums, top-150 posts)
#   ~2h   HF A embed_users (top-300 per forum, 1 embed/user)
#   ~5h   HF embed_users full (top-1000 per forum, for notebook 03)
#   ─────
#   ~60h  total  →  fits in 64h window (Fri 15:00 – Mon 07:00)
#
# Sample strategy for D/E/A: TOP_SAMPLE=300 most-prolific users per forum.
# Full C centroids (5000/forum) are the main analysis artifact.

set -euo pipefail

LOG_DIR="$HOME/csbc26/logs"
mkdir -p "$LOG_DIR"

TS=$(date +%Y%m%d_%H%M%S)
MASTER_LOG="$LOG_DIR/weekend_${TS}.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$MASTER_LOG"; }

cd "$HOME/csbc26"
log "=== WEEKEND PRECOMPUTE START ==="

log "--- PASO 1: HF comparativa C/D/E/A (incluye RaidForums C) ---"
uv run python3 scripts/run_centroids_hf_comparison.py 2>&1 | tee -a "$MASTER_LOG"
log "PASO 1 completado"

log "--- PASO 2: HF embed_users full (top-1000/foro, para notebook 03) ---"
uv run python3 scripts/run_embed_users_hf.py 2>&1 | tee -a "$MASTER_LOG"
log "PASO 2 completado"

log "=== WEEKEND PRECOMPUTE DONE ==="
