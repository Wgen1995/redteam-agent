#!/usr/bin/env bash
# v0.7 方差压缩器假设 N=5 补样：b41（对照）+ b42（处置）——各补至 n=5
set -u
cd "$(dirname "$0")/.."
DIR_B28=/Users/wgen/.tanyin/battles/battle-28/directive.txt

wait_api() {
  local i
  for i in $(seq 1 24); do
    [ "$(curl -sS -m 8 -o /dev/null -w '%{http_code}' https://open.bigmodel.cn 2>/dev/null)" = "200" ] && return 0
    echo "[$(date '+%H:%M')] API_DOWN wait 5m ($i/24)"
    sleep 300
  done
  return 1
}

run_battle() {  # $1=n $2=gen $3=arm
  local n=$1 gen=$2 arm=$3 H R TL0 FROZE i TL
  wait_api || { echo "b$n SKIP_API_DEAD_2H"; return; }
  H=$HOME/.tanyin/battles/battle-$n
  echo "== [$(date '+%H:%M')] battle-$n ($arm) start =="
  python3 scripts/battle.py init --n "$n" --gen "$gen" >/dev/null 2>&1 || { echo "b$n INIT_FAIL"; return; }
  if [ "$arm" = "treatment" ]; then cp "$DIR_B28" "$H/directive.txt"; fi
  python3 scripts/battle.py launch --n "$n" --gen "$gen" --caffeinate >/dev/null 2>&1 || { echo "b$n LAUNCH_FAIL"; return; }
  R=$H/opencode-run.log.runner.tsv
  TL0=0; FROZE=0
  for i in $(seq 1 130); do
    grep -qE 'DONE|GIVEUP' "$R" 2>/dev/null && break
    TL=$(wc -l < "$H/$gen/timeline.tsv" 2>/dev/null || echo 0)
    if [ "$TL" -gt "$TL0" ]; then TL0=$TL; FROZE=0; else FROZE=$((FROZE+1)); fi
    [ $FROZE -ge 25 ] && { echo "b$n DNFT_FROZEN25"; break; }
    sleep 60
  done
  sleep 5
  tail -1 "$R" 2>/dev/null
  python3 scripts/battle.py settle --n "$n" --gen "$gen" > "$H/settle-report.txt" 2>&1 \
    && echo "b$n SETTLE_OK $(grep -m1 recall= $H/settle-report.txt)" \
    || echo "b$n SETTLE_FAIL(rc=$?)"
  if grep -q '^recall=0.00 ' "$H/settle-report.txt" 2>/dev/null \
     && [ "$(grep -c '^MISSING' "$H/settle-report.txt")" = "56" ]; then
    echo "b$n SUSPECT_ZERO"
  fi
}
run_battle 41 G-r42 control
run_battle 42 G-r43 treatment
echo "== [$(date '+%H:%M')] N5_DONE =="
for n in 41 42; do
  grep -m1 recall= "$HOME/.tanyin/battles/battle-$n/settle-report.txt" 2>/dev/null | sed "s/^/b$n /"
done
