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
# 场景C（v0.5b G1）：预算执法全链——超限→BUDGET-ENFORCE+收尾令重启
rm -f "$ROOT/main.log.runner.tsv"; : > "$ROOT/main.log"
mkdir -p "$ROOT/bgoal"
cp tests/fixtures/G-g1/goals.tsv "$ROOT/bgoal/"
printf '2026-09-23T01:00:00Z\t3000000\t40\t0.2\t0\tgoal\tP1 recon\t2\n' > "$ROOT/bgoal/budget.tsv"
python3 cli/tanyin-runner start --cwd "$ROOT" --prompt-file "$ROOT/mission.txt" \
  --log "$ROOT/main.log" --ledger-dir "$ROOT/bgoal" \
  --max-restarts 6 --soft-stall-min 0.05 --stall-min 5 \
  --backoff-base 1 --tick-sec 1 &
RUNNER_PID=$!
for i in $(seq 1 45); do grep -q BUDGET-ENFORCE "$ROOT/main.log.runner.tsv" 2>/dev/null && break; sleep 1; done
kill $RUNNER_PID 2>/dev/null || true; sleep 1
C_ENF=$(grep -c BUDGET-ENFORCE "$ROOT/main.log.runner.tsv" 2>/dev/null || true)
echo "场景C 预算执法链: BUDGET-ENFORCE=$C_ENF"
# 场景D（v0.5b G1）：ask:human 往返——ask.md→ASK/WAIT→answer→ASK-ANSWERED
rm -f "$ROOT/main.log.runner.tsv" "$ROOT/ask.md" "$ROOT/ask.md.answer.md"; : > "$ROOT/main.log"
python3 cli/tanyin-runner start --cwd "$ROOT" --prompt-file "$ROOT/mission.txt" \
  --log "$ROOT/main.log" --ledger-dir "$ROOT/bgoal" \
  --max-restarts 6 --soft-stall-min 0.05 --stall-min 0.3 \
  --backoff-base 1 --tick-sec 1 --ask-file "$ROOT/ask.md" &
RUNNER_PID=$!
sleep 2; echo "凭据发放面在哪个服务？" > "$ROOT/ask.md"
for i in $(seq 1 20); do grep -q ASK\\t "$ROOT/main.log.runner.tsv" 2>/dev/null && break; sleep 1; done
D_ASK=$(grep -c ASK\\t "$ROOT/main.log.runner.tsv" 2>/dev/null || true)
echo "答案：svc-login，走发放面" > "$ROOT/ask.md.answer.md"
for i in $(seq 1 20); do grep -q ASK-ANSWERED "$ROOT/main.log.runner.tsv" 2>/dev/null && break; sleep 1; done
kill $RUNNER_PID 2>/dev/null || true; sleep 1
D_ANS=$(grep -c ASK-ANSWERED "$ROOT/main.log.runner.tsv" 2>/dev/null || true)
echo "场景D ask:human 往返: ASK=$D_ASK ANSWERED=$D_ANS"
# 判定
FAIL=0
[ "$A_SOFT" -ge 1 ] && [ "$A_STALL" -ge 1 ] && [ "$A_BACK" -ge 1 ] && [ "$B_DIR" -ge 1 ] && [ "$C_ENF" -ge 1 ] && [ "$D_ASK" -ge 1 ] && [ "$D_ANS" -ge 1 ] || FAIL=1
grep -E 'SOFTSTALL|STALL|BACKOFF|DIRECTIVE|BUDGET-ENFORCE|ASK' "$ROOT/main.log.runner.tsv" | head -10
rm -rf "$ROOT"
[ $FAIL -eq 0 ] && echo "SIM_PASS" || { echo "SIM_FAIL"; exit 1; }
