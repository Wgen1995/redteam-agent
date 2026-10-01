#!/usr/bin/env bash
# GenSift Stop hook —— 会话还有未分析卡时，阻止宿主提前收工。
# 接法与已知限制见同目录 README.md。
set -u
export LC_ALL=C

# ---- 会话目录解析（两段兜底）----
# 1) 环境变量 GENSHIFT_SESSION 显式指定（最准；可在 hook command 里注入）
# 2) 否则扫描 ~/gensift-sessions/gensift-*，取 STATE 为 running 且 mtime 最新的
S="${GENSHIFT_SESSION:-}"
if [ -z "$S" ] || [ ! -f "$S/checks.tsv" ]; then
  S=""
  # ls -dt 按 mtime 降序，取第一个满足条件的即最新
  for d in $(ls -dt "$HOME"/gensift-sessions/gensift-* 2>/dev/null); do
    [ -f "$d/STATE" ] || continue
    grep -qx "running" "$d/STATE" 2>/dev/null || continue
    [ -f "$d/checks.tsv" ] || continue
    S="$d"
    break
  done
fi

# 不是 GenSift 会话（无 running 会话 / 无账本）→ 不干预，放行停止
[ -n "$S" ] && [ -f "$S/checks.tsv" ] || exit 0
# 只干预 running 会话（B-065/C-026）：done/aborted-l1/interrupted 均已终态化，不再逼跑
grep -qx "running" "$S/STATE" 2>/dev/null || exit 0

# N1：Plateau 在案（主循环 step6 已判强制停轮）→ 放行停止——方向与逼跑相反，
# 终态化（不变量+报告+EXIT_CODE）由编排器按 phases/terminal.md 完成
if [ -f "$S/audit/plateau.flag" ]; then
  echo "Plateau 在案→终态化（phases/terminal.md）——step6 已判强制停轮，不再逼续跑"
  exit 0
fi

# ---- 统计未分析卡 ----
# 数据行以 $1 ~ ^CK- 过滤：checks.tsv 在主循环中被整体重排序，表头行可能沉到文件末尾，
# 因此不能用 NR>1 当数据行过滤条件（与 SKILL.md 终态判定同口径：$2!="ext" 且 $5=="unchecked"）。
N=$(awk -F'\t' '$1 ~ /^CK-/ && $2 != "ext" && $5 == "unchecked"' "$S/checks.tsv" \
     | wc -l | tr -d ' ')
# B-065：跑全口径含 ext deferred>0（设计 §7.1 停轮强制层：分母 unchecked>0 ∨ ext deferred>0 → 继续）
ED=$(awk -F'\t' '$1 ~ /^CK-/ && $2 == "ext" && $5 == "deferred"' "$S/checks.tsv" \
     | wc -l | tr -d ' ')

if [ "$N" -gt 0 ]; then
  # B-066：返回消息自带"下一条协议命令"——跨宿主协议卡，宿主照做即续跑
  nxt="执行 phases/main-loop.md 的 step0→step1（前置检查+取卡）"
  [ -f "$S/tmp/stall_lane" ] && nxt="执行 phases/main-loop.md 的 step1（L3 换道：本轮全派 fw/term）"
  msg="继续：剩余 ${N} 张卡未分析，下一条命令是 ${nxt}"
  echo "$msg"        # stdout：日志 / 人工运行可见
  echo "$msg" >&2    # stderr：Claude Code 的 Stop hook 只把 stderr 回喂给模型
  exit 2             # Claude Code Stop hook 语义：exit 2 = 阻止停止并继续；exit 1 不阻止
fi

if [ "$ED" -gt 0 ]; then
  msg="继续：ext deferred ${ED} 张待终态披露，下一条命令是 执行 phases/terminal.md（不变量+终态报告）"
  echo "$msg"; echo "$msg" >&2
  exit 2
fi

# C-026（A2 停止路径）：本 hook 的两个继续判据（分母 unchecked、ext deferred）都清空、
# 但 STATE 仍 running——宿主在终态块（不变量+报告+EXIT_CODE）跑完之前停轮。注意 ext unchecked
# 不在这两个判据内（其循环归属由主循环 step6 的 UE 口径承担，hook 不重复记账）。
# 状态全在盘，直接记 interrupted + 退出码 2（同源路径再次发起即断点续跑）
echo "interrupted" > "$S/STATE"
echo "2" > "$S/EXIT_CODE"
exit 0
