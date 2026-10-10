#!/usr/bin/env bash
# v0.6 双臂重跑实验（rerun 协议正式首跑）——链式自动驾驶 6 战
# 臂A 对照（无指令）x3：b29 b30 b31；臂B 处置（b28 指令）x3：b32 b33 b34
set -u
cd "$(dirname "$0")/.."
DIR_B28=/Users/wgen/.tanyin/battles/battle-28/directive.txt
run_battle() {  # $1=n $2=gen $3=arm
  local n=$1 gen=$2 arm=$3 H R TL0 FROZE i TL
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
}
run_battle 29 G-r30 control
run_battle 30 G-r31 control
run_battle 31 G-r32 control
run_battle 32 G-r33 treatment
run_battle 33 G-r34 treatment
run_battle 34 G-r35 treatment
echo "== [$(date '+%H:%M')] ALL_ARMS_DONE =="
for n in 29 30 31 32 33 34; do
  grep -m1 recall= "$HOME/.tanyin/battles/battle-$n/settle-report.txt" 2>/dev/null | sed "s/^/b$n /"
done
