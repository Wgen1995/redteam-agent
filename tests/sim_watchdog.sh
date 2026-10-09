#!/usr/bin/env bash
# b10 看门狗仿真（可复跑）：假战士+快速阈值，验证 SOFTSTALL/STALL击杀/BACKOFF/DIRECTIVE/自适应tick 全链
# 用法：bash tests/sim_watchdog.sh   （约 30s；无 LLM 依赖）
set -euo pipefail
ROOT=$(mktemp -d /tmp/tanyin-sim.XXXXXX)
mkdir -p "$ROOT/bin"
printf '%s\n' '#!/usr/bin/env bash' 'LOG="${FAKE_LOG:?}"' 'echo "[probe] warrior alive $$" >> "$LOG"' 'exec sleep 600' > "$ROOT/bin/opencode"
chmod +x "$ROOT/bin/opencode"
export PATH="$ROOT/bin:$PATH"
export FAKE_LOG="$ROOT/main.log"
REPO=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO"
: > "$ROOT/main.log"
echo "第一令：探针" > "$ROOT/mission.txt"
# 场景A：硬击杀链（soft 3s/hard 7.2s，无指令）
python3 cli/tanyin-runner start --cwd "$ROOT" --prompt-file "$ROOT/mission.txt" \
  --log "$ROOT/main.log" --ledger-dir "$ROOT" \
  --max-restarts 2 --soft-stall-min 0.05 --stall-min 0.12 \
  --backoff-base 1 --tick-sec 1 &
RUNNER_PID=$!
for i in $(seq 1 60); do grep -q 'GIVEUP.*after stall' "$ROOT/main.log.runner.tsv" 2>/dev/null && break; sleep 1; done
kill $RUNNER_PID 2>/dev/null || true; sleep 1
A_SOFT=$(grep -c SOFTSTALL "$ROOT/main.log.runner.tsv")
A_STALL=$(grep -c STALL "$ROOT/main.log.runner.tsv")
A_BACK=$(grep -c BACKOFF "$ROOT/main.log.runner.tsv")
echo "场景A 硬击杀链: SOFTSTALL=$A_SOFT STALL=$A_STALL BACKOFF=$A_BACK"
# 场景B：指令注入链（digest 变化→DIRECTIVE→带令 RESTART）
rm -f "$ROOT/directive.txt" "$ROOT/main.log.runner.tsv"
: > "$ROOT/main.log"
python3 cli/tanyin-runner start --cwd "$ROOT" --prompt-file "$ROOT/mission.txt" \
  --log "$ROOT/main.log" --ledger-dir "$ROOT" \
  --max-restarts 6 --soft-stall-min 0.05 --stall-min 0.5 \
  --backoff-base 1 --tick-sec 1 --directive-file "$ROOT/directive.txt" &
RUNNER_PID=$!
for i in $(seq 1 30); do [ -f "$ROOT/main.log.runner.tsv" ] && grep -q SOFTSTALL "$ROOT/main.log.runner.tsv" && break; sleep 1; done
echo "补令注入：绕过 403 段" > "$ROOT/directive.txt"
for i in $(seq 1 30); do grep -q DIRECTIVE "$ROOT/main.log.runner.tsv" 2>/dev/null && break; sleep 1; done
kill $RUNNER_PID 2>/dev/null || true; sleep 1
B_DIR=$(grep -c DIRECTIVE "$ROOT/main.log.runner.tsv")
echo "场景B 指令注入链: DIRECTIVE=$B_DIR"
# 判定
FAIL=0
[ "$A_SOFT" -ge 1 ] && [ "$A_STALL" -ge 1 ] && [ "$A_BACK" -ge 1 ] && [ "$B_DIR" -ge 1 ] || FAIL=1
grep -E 'SOFTSTALL|STALL|BACKOFF|DIRECTIVE' "$ROOT/main.log.runner.tsv" | head -8
rm -rf "$ROOT"
[ $FAIL -eq 0 ] && echo "SIM_PASS" || { echo "SIM_FAIL"; exit 1; }
