#!/bin/bash
# One parallel worker. Usage: scripts/run_shard.sh a [MAX]
set -u
cd "$(dirname "$0")/.." || exit 1
S=${1:?shard letter}; MAX=${2:-100}
export FRAMES_FILE=02_frames_ar/shard_$S.txt OUT_PREFIX=full_$S NAMES_FILE=01_glossary/names_map_$S.tsv
[ -f 02_frames_ar/GATE_2_CLOSED ] || { echo "BLOCK: GATE_2 not closed"; exit 7; }
[ -f "$FRAMES_FILE" ] || { echo "BLOCK: $FRAMES_FILE missing — run scripts/make_shards.py"; exit 7; }
[ -f "$NAMES_FILE" ] || printf 'en\tar\n' > "$NAMES_FILE"
touch 02_frames_ar/${OUT_PREFIX}_frames_ar.jsonl 02_frames_ar/${OUT_PREFIX}_fes_ar.jsonl
mkdir -p logs
PROMPT=$(cat CONTINUE_006.md)
START=$(ls logs/${OUT_PREFIX}_round_*.log 2>/dev/null | wc -l | tr -d ' ')
log(){ echo "$(date '+%F %T') [$OUT_PREFIX] $*" | tee -a logs/driver_$S.log; }
measure(){ python3 scripts/04_check_pilot.py 2>&1; }
log "=== start (max $MAX) FRAMES_FILE=$FRAMES_FILE"
PF=$(env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN claude -p "Reply with exactly: PREFLIGHT_OK" 2>&1 | tail -1)
echo "$PF" | grep -q PREFLIGHT_OK || { log "ABORT preflight: $PF"; exit 8; }
for k in $(seq 1 "$MAX"); do
  n=$((START + k)); L="logs/${OUT_PREFIX}_round_$n.log"
  OUT=$(measure)
  echo "$OUT" | grep -q '^GATE_1 = CLOSED' || { log "ABORT round $n: GATE_1 not closed"; exit 3; }
  FM=$(echo "$OUT" | awk -F' = ' '/^frames_missing/{print $2}'); RJ=$(echo "$OUT" | awk '/^rejected/{print $3}')
  log "round $n pre: frames_missing=$FM rejected=$RJ"
  [ "$FM" = "0" ] && { log "DONE shard $S"; exit 0; }
  [ "${RJ:-0}" != "0" ] && { log "ABORT round $n: pre-existing rejects=$RJ"; exit 4; }
  RETRIES=${RETRIES:-6}; WAIT=${WAIT:-600}; STATUS=""
  for t in $(seq 0 "$RETRIES"); do
    [ "$t" -gt 0 ] && { log "round $n retry $t/$RETRIES after ${WAIT}s (transient)"; sleep "$WAIT"; }
    env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN perl -e 'alarm 5400; exec @ARGV' -- claude -p "$PROMPT" --dangerously-skip-permissions > "$L" 2>&1; RC=$?
    STATUS=$(grep -m1 '^ROUND_STATUS' "$L" | awk -F'= ' '{print $2}')
    [ -n "$STATUS" ] && break
    grep -qiE "overloaded|rate limit|usage limit|session limit|hit your|529|timed out" "$L" || [ ! -s "$L" ] || break
  done
  FM2=$(measure | awk -F' = ' '/^frames_missing/{print $2}')
  log "round $n post: rc=$RC status=${STATUS:-MISSING} frames_missing=${FM}->${FM2}"
  case "${STATUS:-MISSING}" in OK) ;; DONE_NOTHING_TO_DO) log "DONE shard $S"; exit 0 ;; *) log "ABORT round $n: ${STATUS:-no ROUND_STATUS} — see $L"; exit 5 ;; esac
  [ "$FM" = "$FM2" ] && { log "ABORT round $n: no progress"; exit 6; }
done
log "=== MAX rounds reached"; exit 0
