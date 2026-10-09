#!/usr/bin/env bash
# 同步技能单一真源(.opencode/skills/tanyin) → 插件镜像(skills/tanyin)
# 用法：bash scripts/sync-skill.sh（在 platform/dsh-plugin-tanyin 内）
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"          # platform/dsh-plugin-tanyin
SRC="$HERE/../../.opencode/skills/tanyin"
DST="$HERE/skills/tanyin"
[ -f "$SRC/SKILL.md" ] || { echo "源缺失: $SRC/SKILL.md" >&2; exit 1; }
rm -rf "$DST"
mkdir -p "$DST"
cp -R "$SRC/." "$DST/"
# phases/ 详令+状态机在仓根（技能按需加载 phases/<门>.md）——一并镜像
mkdir -p "${DST}/phases"
cp -R "$HERE/../../phases/." "${DST}/phases/"
# 镜像头注：声明前提（仓在盘，CLI 以仓根相对路径调用）——不动真源
note="# 镜像说明\n# 单一真源=.opencode/skills/tanyin（勿直接改本目录；重跑 scripts/sync-skill.sh 刷新）\n# 使用前提：redteam-agent 仓已 clone 在盘且会话 cwd 可达仓根；技能内 CLI 命令按仓根相对路径调用。\n"
printf '%b' "$note" > "$DST/MIRROR.md"
count=$(find "$DST" -name '*.md' | wc -l | tr -d ' ')
echo "同步完成: ${DST} (${count} 个 md)"
