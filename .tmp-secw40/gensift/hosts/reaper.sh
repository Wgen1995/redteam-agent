#!/usr/bin/env bash
# GenSift hosts/reaper.sh —— 孤儿进程收尸 + idle 看门狗 + 墙钟硬超时（posix 侧；windows 侧用 reaper.ps1）
# 设计依据：§15 宿主适配补强（D-098 三重完成检测的后两机制 / D-099 idle 阈值校准 / D-100 收尸成套）。
# 状态自包含：全部事实在会话目录（audit/host-children.tsv 注册表 + STATE），不依赖调用方记忆。
# 用法：
#   reaper.sh register <session> <pid> <desc>                 # 子进程入注册表（加锁）
#   reaper.sh unregister <session> <pid>                       # 子进程正常退出后出表（加锁）
#   reaper.sh watch <session> <pid> <idle_s> <wall_s> [poll_s] # 看门狗：idle 超阈值或墙钟超时→进程组 kill
#   reaper.sh reap <session> [--all]                           # 收尸：表内已死条目清档；--all 连活条目一并 kill
# 退出码：0=正常；3=watch 判 idle/墙钟超时并已 kill；4=收尸发现孤儿并已 kill；1=用法错
set -u
export LC_ALL=C
cmd="${1:-}"; sess="${2:-}"; pid="${3:-}"
usage(){ echo "usage: reaper.sh register|unregister|watch|reap <session> <pid> [args]" >&2; exit 1; }
[ -n "$cmd" ] && [ -n "$sess" ] || usage
REG="$sess/audit/host-children.tsv"; LOCK="$sess/audit/reaper.lock"
mkdir -p "$sess/audit" 2>/dev/null
[ -f "$REG" ] || printf 'pid\tstarted\tdesc\n' > "$REG"
# ── 加锁注册表（mkdir 原子锁；D-100"加锁注册表"）──
with_lock(){ local i=0; until mkdir "$LOCK" 2>/dev/null; do i=$((i+1)); [ $i -gt 100 ] && { echo "reaper: lock 超时" >&2; return 1; }; sleep 0.1; done
  trap 'rmdir "$LOCK" 2>/dev/null' RETURN
  "$@"; }
alive(){ kill -0 "$1" 2>/dev/null; }
pgkill(){ # 进程组 kill（负 PID）；组不存在则单点 kill 兜底（D-100"进程组 kill"）
  kill -TERM -- -"$1" 2>/dev/null || kill -TERM "$1" 2>/dev/null
  sleep 2; kill -KILL -- -"$1" 2>/dev/null || kill -KILL "$1" 2>/dev/null; return 0; }
case "$cmd" in
register)
  [ -n "$pid" ] || usage
  with_lock sh -c "printf '%s\t%s\t%s\n' '$pid' \"\$(date '+%F %T')\" '${4:-child}' >> '$REG'"
  echo "registered $pid" ;;
unregister)
  [ -n "$pid" ] || usage
  with_lock sh -c "grep -v \"^$pid	\" '$REG' > '$REG.tmp' 2>/dev/null && mv '$REG.tmp' '$REG' || true"
  echo "unregistered $pid" ;;
watch)
  # 三重完成检测之②③（①=宿主 CLI 事件流，见 adapter 文档）：不依赖被监控方配合——
  # 活性信号=会话目录 mtime（账本/分片在写=在干活），墙钟=条目 started 起算
  idle_s="${4:-2700}"; wall_s="${5:-14400}"; poll_s="${6:-60}"
  [ -n "$pid" ] || usage
  started=$(date +%s); last_act=$started; found=0
  with_lock sh -c "printf '%s\t%s\twatchdog\n' '$pid' \"\$(date '+%F %T')\" >> '$REG'"
  while :; do
    sleep "$poll_s"
    alive "$pid" || { found=1; break; }                            # 正常退出（CLI 事件流兜底）
    now=$(date +%s)
    act=$(find "$sess" -type f -newermt "@$last_act" 2>/dev/null | head -1)
    [ -n "$act" ] && last_act=$now
    if [ $((now - last_act)) -gt "$idle_s" ]; then                 # idle 看门狗（阈值校准见 adapter 文档 D-099）
      echo "watchdog: idle $((now - last_act))s > ${idle_s}s → kill 进程组 $pid" >&2
      pgkill "$pid"; found=3; break; fi
    if [ $((now - started)) -gt "$wall_s" ]; then                  # 墙钟硬超时
      echo "watchdog: 墙钟 $((now - started))s > ${wall_s}s → kill 进程组 $pid" >&2
      pgkill "$pid"; found=3; break; fi
  done
  with_lock sh -c "grep -v \"^$pid	\" '$REG' > '$REG.tmp' 2>/dev/null && mv '$REG.tmp' '$REG' || true"
  [ "$found" = "3" ] && exit 3
  exit 0 ;;
reap)
  killed=0
  while IFS=$'\t' read -r rp rs rd; do
    case "$rp" in ''|pid) continue ;; esac
    if alive "$rp"; then
      [ "${3:-}" = "--all" ] || continue
      echo "reap: kill 活条目 $rp（$rd）" >&2; pgkill "$rp"; killed=1
    else
      echo "reap: 清档死条目 $rp（$rd）" >&2; killed=1; fi
    with_lock sh -c "grep -v \"^$rp	\" '$REG' > '$REG.tmp' 2>/dev/null && mv '$REG.tmp' '$REG' || true"
  done < "$REG"
  [ $killed -eq 1 ] && exit 4
  exit 0 ;;
*)
  usage ;;
esac
