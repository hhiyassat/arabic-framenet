#!/bin/bash
# Unattended driver. Loop condition = the CHECKER, never the agent's opinion.
set -u
cd "$(dirname "$0")/.." || exit 1
SCOPE=${1:-pilot}; PHASE=${2:-phase1}
case "$SCOPE" in
  pilot) export FRAMES_FILE=02_frames_ar/pilot_frames.txt OUT_PREFIX=pilot; PROMPT_FILE=CONTINUE_004.md ;;
  full)  export FRAMES_FILE=02_frames_ar/all_frames.txt   OUT_PREFIX=full;  PROMPT_FILE=CONTINUE_005.md
         [ -f 02_frames_ar/GATE_2_CLOSED ] || { echo "BLOCK: 02_frames_ar/GATE_2_CLOSED missing — owner must close GATE_2 first"; exit 7; }
         [ -f 02_frames_ar/full_frames_ar.jsonl ] || cp 02_frames_ar/pilot_frames_ar.jsonl 02_frames_ar/full_frames_ar.jsonl
         [ -f 02_frames_ar/full_fes_ar.jsonl ]    || cp 02_frames_ar/pilot_fes_ar.jsonl    02_frames_ar/full_fes_ar.jsonl ;;
  *) echo "usage: $0 pilot|full phase1|phase2 [MAX]"; exit 1 ;;
esac
case "$PHASE" in
  phase1) MAX=3 ;;
  phase2) MAX=${3:-$([ "$SCOPE" = full ] && echo 150 || echo 40)} ;;
  *) echo "usage: $0 pilot|full phase1|phase2 [MAX]"; exit 1 ;;
esac
mkdir -p logs
PROMPT=$(cat "$PROMPT_FILE")
START=$(ls logs/${SCOPE}_round_*.log 2>/dev/null | wc -l | tr -d ' ')
log(){ echo "$(date '+%F %T') [$SCOPE] $*" | tee -a logs/driver.log; }
measure(){ python3 scripts/04_check_pilot.py 2>&1; }
snapshot(){ shasum -a 256 02_frames_ar/${OUT_PREFIX}_frames_ar.jsonl 02_frames_ar/${OUT_PREFIX}_fes_ar.jsonl 01_glossary/names_map.tsv 2>/dev/null | awk '{print $1}' | tr '\n' ' '; }

log "=== $PHASE start (max $MAX rounds) FRAMES_FILE=$FRAMES_FILE OUT_PREFIX=$OUT_PREFIX"
PF=$(env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN claude -p "Reply with exactly: PREFLIGHT_OK" 2>&1 | tail -1)
echo "$PF" | grep -q PREFLIGHT_OK || { log "ABORT preflight: headless claude failed: $PF"; exit 8; }
log "preflight OK"
for k in $(seq 1 "$MAX"); do
  n=$((START + k)); L="logs/${SCOPE}_round_$n.log"
  OUT=$(measure)
  echo "$OUT" | grep -q '^GATE_1 = CLOSED' || { log "ABORT round $n: GATE_1 not closed"; echo "$OUT" >> logs/driver.log; exit 3; }
  FM=$(echo "$OUT" | awk -F' = ' '/^frames_missing/{print $2}')
  EM=$(echo "$OUT" | awk -F' = ' '/^fes_missing/{print $2}')
  RJ=$(echo "$OUT" | awk '/^rejected/{print $3}')
  log "round $n pre: frames_missing=$FM fes_missing=$EM rejected=$RJ"
  if [ "$FM" = "0" ] && [ "$EM" = "0" ]; then log "DONE: nothing missing"; exit 0; fi
  if [ "${RJ:-0}" != "0" ]; then log "ABORT round $n: pre-existing rejects=$RJ (owner review)"; exit 4; fi
  BEFORE=$(snapshot)
  env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN claude -p "$PROMPT" --dangerously-skip-permissions > "$L" 2>&1; RC=$?
  AFTER=$(snapshot)
  STATUS=$(grep -m1 '^ROUND_STATUS' "$L" | awk -F'= ' '{print $2}')
  POST=$(measure); FM2=$(echo "$POST" | awk -F' = ' '/^frames_missing/{print $2}')
  log "round $n post: rc=$RC status=${STATUS:-MISSING} frames_missing=${FM}->${FM2} changed=$([ "$BEFORE" != "$AFTER" ] && echo yes || echo no)"
  case "${STATUS:-MISSING}" in
    OK) ;;
    DONE_NOTHING_TO_DO) log "DONE"; exit 0 ;;
    *) log "ABORT round $n: agent reported ${STATUS:-no ROUND_STATUS line} — see $L"; exit 5 ;;
  esac
  [ "$FM" = "$FM2" ] && { log "ABORT round $n: no progress"; exit 6; }
done
log "=== $PHASE end: $MAX rounds completed"; [ "$PHASE" = phase1 ] && log "PHASE1 COMPLETE — owner review required before phase2"; exit 0
