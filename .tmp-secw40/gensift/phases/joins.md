<!-- 引用件：由入口 SKILL.md「阶段索引」进入，L2 收敛/上限后执行一次（audit/joins-round-done 留痕）。本件不引用其他引用件。 -->

## 拼链与合并（L2 收敛后；joins 第七账本件 + combinations 语义件）

**J1. 拼链轮派发（多模块才拼——Egress=契约=Ingress；单模块如实 N/A）**

```bash
. "$S/env.sh"
# 表头兜底（3d 已预建；旧会话续跑补——A-045/B-195）
[ -f "$S/joins.tsv" ] || printf "join_id\tegress_ref\tcontract_ref\tingress_ref\tconfidence\tassumptions\n" > "$S/joins.tsv"
# 触发口径：file_inventory.module 语义模块去重 ≥2（F1：只认 mod: 前缀——dir: 机械回填不算，防目录数虚撑近恒真；
# 机械；单模块无跨模块链可拼——如实 N/A 不虚派）
MODJ=$(awk -F'\t' 'NR>1 && $5 ~ /^mod:/{ v=substr($5,5); print v }' "$S/inventories/file_inventory.tsv" | LC_ALL=C sort -u | wc -l | tr -d ' ')
echo "拼链轮: modules=$MODJ（≥2 才派 Reporter 拼链；单模块 N/A 如实——coverage 披露）"
if [ "$MODJ" -ge 2 ]; then
  # 机械信封（Reporter 只组织不制造）：sink/source 清单行 + 在役 mf 行
  awk -F'\t' 'NR>1{print "sink\t"$1"\t"$3"\t"$4}' "$S/inventories/sink_inventory.tsv" > "$S/tmp/join-input.txt"
  awk -F'\t' 'NR>1{print "src\t"$1"\t"$3"\t"$4}' "$S/inventories/source_inventory.tsv" >> "$S/tmp/join-input.txt"
  tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$13==""{print "mf\t"$1"\t"$6"\t"$4}' >> "$S/tmp/join-input.txt"
  echo "JOIN 输入: $(wc -l < "$S/tmp/join-input.txt" | tr -d ' ') 行 → 派 Reporter（prompt 见下）"
fi
```

派 Reporter 拼链（可写通用子代理；固定前缀+尾部变量块——A-107；{R} 为当前轮号）：

```
你是 GenSift Reporter（拼链轮）。读取 {SK}/agents/reporter.md 的「跨模块拼链（joins）」节并严格遵守。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）。
完成后只返回一行：分片路径 + 行数。
——以上固定前缀（A-107）——
输入：{S}/tmp/join-input.txt（sink/src/mf 机械信封）｜源码根：{SRC}
任务：A 侧 Egress（对外调用 sink）= 契约（字段级映射）= B 侧 Ingress（入口 source）拼跨模块半链。
写分片到 {S}/shards/JOIN-R{R}.tsv（带轮号，重派不覆盖），每行六列（TAB 分隔）：
JN-{5 位序号}\t{egress_ref=SINK-seq 或 NA}\t{契约一句话}\t{ingress_ref=SRC-seq 或 NA}\t{explicit-schema|code-dto|heuristic|none}\t{假设点，多个分号隔开；无则空}
无对端 NA=dangling（B-145 进披露）。拼链者不得拍板：凡依赖你判断的（净化层位/契约方向/Source 绑定）一律进 assumptions 由 follow-up 卡核实。
```

**J2. JOIN 分片落账 + follow-up ext 卡 + dangling 披露（B-122/B-142/B-144/A-055）**

```bash
. "$S/env.sh"
# JOIN 分片机械合并入账（join_id 去重追加——协议命令形态，禁逐字粘贴；重派/多轮不双计）
for jf in "$S"/shards/JOIN-*.tsv; do
  [ -f "$jf" ] || continue
  grep '^JN-' "$jf"
done | awk -F'\t' 'NR==FNR{ if(FNR>1) seen[$1]=1; next } !($1 in seen){ print }' "$S/joins.tsv" - >> "$S/joins.tsv"
# assumptions 非空 → follow-up ext 卡（origin_ref=join_id——A-055/B-144：假设点必复核，卡由 Analyzer 下轮核实）
NJ=0
while IFS=$'\t' read -r jid eg ct ig cf as; do
  [ -n "$jid" ] || continue
  [ -n "$as" ] || continue
  cid="CK-ext-${jid}"
  awk -F'\t' -v c="$cid" '$1==c{f=1} END{exit !f}' "$S/checks.tsv" 2>/dev/null && continue
  printf "%s\text\t%s\t%s\tunchecked\t\t\t0\tr1\n" "$cid" "$jid" "$jid" >> "$S/checks.tsv"
  NJ=$((NJ+1))
done < <(tail -n +2 "$S/joins.tsv")
# dangling 披露数据（B-145：无对端=egress/ingress 为 NA 的行——frontier/coverage 消费）
tail -n +2 "$S/joins.tsv" | awk -F'\t' '$2=="NA"||$4=="NA"{print $1"\t"$6}' > "$S/tmp/joins-dangling.txt"
echo "拼链落账: $(tail -n +2 "$S/joins.tsv" | wc -l | tr -d ' ') 行｜follow-up 卡 +${NJ}（I13 闭合口径）｜dangling $(wc -l < "$S/tmp/joins-dangling.txt" | tr -d ' ') 行"
touch "$S/audit/joins-round-done"
if [ "$NJ" -gt 0 ]; then
  echo "→ follow-up ext 卡 ${NJ} 张回主循环派发（下轮 2b ext 分支；闭合前不得终态——I13 拦截）"
else
  echo "→ 无新 follow-up 卡，直接【终态】（phases/terminal.md）"
fi
```

**J3. 组合分析派发 + combinations.md 存在性检查（C-009/C-023/D-055——语义创作归 Reporter，独立成件不混进 report.md）**

对多模块会话（J1 的 modules ≥2）派一个 Reporter 组合轮（同一轮可与拼链轮合并派发）：

```
你是 GenSift Reporter（组合分析轮）。读取 {SK}/agents/reporter.md 的「组合分析与投影」节并严格遵守。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）。
完成后只返回一行：产物路径 + 组合数。
——以上固定前缀（A-107）——
输入：{S}/machine-fields.tsv（只读）+ {S}/joins.tsv（只读）｜源码根：{SRC}
任务：跨 finding 组合风险（pre-auth 链/原语组合/与已知 CVE 组合攻击）。
写 {S}/combinations.md（W5 阶段性刷新——覆盖重写；不混进 report.md，G3 语义层软保证）。
每条组合必须锚定 ≥2 个 finding_id；不引入账本外新事实；无组合时写"（无跨 finding 组合在案）"。
```

```bash
. "$S/env.sh"
# 存在性检查（阶段/终态两处同口径——缺失=降级披露不静默不阻断；
# 单模块会话 N/A 分支：组合轮本就未派（J1 触发口径=多模块），不记降级——否则单模块会话必然 EC=2）
MODC=$(awk -F'\t' 'NR>1 && $5!="-" && $5!=""{print $5}' "$S/inventories/file_inventory.tsv" 2>/dev/null | LC_ALL=C sort -u | wc -l | tr -d ' ')
if [ "$MODC" -lt 2 ]; then
  echo "combinations: N/A（单模块——无跨模块链，组合件通道未开；与 J1 拼链同触发口径，不计降级）"
elif [ -s "$S/combinations.md" ]; then
  echo "combinations.md 在档（$(wc -l < "$S/combinations.md" | tr -d ' ') 行）——存在性 PASS"
else
  echo "COMBINATIONS 未产出（Reporter 组合轮未返回——如实披露不静默，C-009/D-055）" >> "$S/audit/coverage-degraded.log"
  echo "combinations.md 缺失：已记降级（audit/coverage-degraded.log；终态 coverage 再披露一次）"
fi
```
