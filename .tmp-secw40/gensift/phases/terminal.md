<!-- 引用件：由入口 SKILL.md「阶段索引」进入，L2 收敛/上限后执行；不变量 FAIL 的处置见本件中部说明。本件不引用其他引用件。 -->

## 终态

### 先跑不变量

```bash
. "$S/env.sh"
echo "═══ 不变量检查 ═══" | tee "$S/audit/invariants.md"
# D-091 能力边界列：每行附「边界: …」（— = 机械全量；非 — = 此检查为空/需人工的显式声明——假完整性比不做更危险）
# C-064：I1-I20 全 20 条都在册（I16 由指标块追加——report 写后复核；I18 由 G3 块追加——双跑才判）

# I1 类 fixture 门在 dev 侧（gensift-dev/commands/golden/）——会话内不重跑（成本与语料归属），如实记边界
echo "I1 类fixture: NEEDS-DEV（dev 侧 golden/smoke 双件对夹具——会话内不重跑）｜边界: 需 dev 门" | tee -a "$S/audit/invariants.md"

(cd "$S/inventories" && $HASH -c frozen.sha256 >/dev/null 2>&1) && echo "I2 冻结: PASS｜边界: —" | tee -a "$S/audit/invariants.md" || echo "I2 冻结: FAIL｜边界: —" | tee -a "$S/audit/invariants.md"

# I3 三向完备（C-Inv03）：每 sink 一张 bw / 每 http+external_message 入口一张 fw（反向=fw 引用必须在 source 清单内，
# 含 demand 追踪卡的 persisted 引用）/ 每 role∈{app,config} 文件一张 term（反向同法）；role 标注后 test/vendor 不入 term 口径
M1=$(comm -23 <(awk -F'\t' 'NR>1{print $1}' "$S/inventories/sink_inventory.tsv" | sort) <(awk -F'\t' '$2=="bw"{print $3}' "$S/checks.tsv" | sort) | wc -l | tr -d ' ')
M1R=$(comm -13 <(awk -F'\t' 'NR>1{print $1}' "$S/inventories/sink_inventory.tsv" | sort) <(awk -F'\t' '$2=="bw"{print $3}' "$S/checks.tsv" | sort) | wc -l | tr -d ' ')
M2=$(comm -23 <(awk -F'\t' 'NR>1 && ($4=="http"||$4=="external_message"){print $1}' "$S/inventories/source_inventory.tsv" | sort) <(awk -F'\t' '$2=="fw"{print $3}' "$S/checks.tsv" | sort) | wc -l | tr -d ' ')
M2R=$(comm -13 <(awk -F'\t' 'NR>1 && ($4=="http"||$4=="external_message"||$4=="persisted_read"){print $1}' "$S/inventories/source_inventory.tsv" | sort) <(awk -F'\t' '$2=="fw"{print $3}' "$S/checks.tsv" | sort) | wc -l | tr -d ' ')
M3=$(comm -23 <(awk -F'\t' 'NR>1 && ($6=="app"||$6=="config"){print $1}' "$S/inventories/file_inventory.tsv" | sort) <(awk -F'\t' '$2=="term"{print $3}' "$S/checks.tsv" | sort) | wc -l | tr -d ' ')
M3R=$(comm -13 <(awk -F'\t' 'NR>1 && ($6=="app"||$6=="config"){print $1}' "$S/inventories/file_inventory.tsv" | sort) <(awk -F'\t' '$2=="term"{print $3}' "$S/checks.tsv" | sort) | wc -l | tr -d ' ')
echo "I3 三向: $([ "$M1" = "0" ] && [ "$M1R" = "0" ] && [ "$M2" = "0" ] && [ "$M2R" = "0" ] && [ "$M3" = "0" ] && [ "$M3R" = "0" ] && echo PASS || echo "FAIL(bw:$M1/$M1R fw:$M2/$M2R term:$M3/$M3R)")｜边界: demand 追踪卡入 fw 反向口径" | tee -a "$S/audit/invariants.md"

BAD4=$(awk -F'\t' 'NR>1 && $5!~/^(unchecked|candidate|refuted|not_applicable|no_path|blocked|partial|deferred)$/' "$S/checks.tsv" | wc -l | tr -d ' ')
echo "I4 终态: $([ "$BAD4" = "0" ] && echo PASS || echo "FAIL($BAD4)")｜边界: —" | tee -a "$S/audit/invariants.md"

# I5 候选分片（C-Inv05 三子检查）：① verdict_state∉{merged-into} 且 delivery_state∉{degraded}（S8 两列）的
# 非种子候选各有 1 条 V 分片；② 每 V 分片 ≥1 行 SELF:
# ③ 种子行显式闭合（verdict_state∈{open,closed-by-evidence,refuted-by-evidence}——A-086，open=待本地证据的显式披露态）；
# ④ confirmed 有 severity+cvss（machine-fields $4 非空 且 finding 文件 CVSS 值非空）
BAD5=0; for vf in "$S"/shards/V-*.tsv; do [ -f "$vf" ] && [ "$(grep -c '^SELF:' "$vf")" -lt 1 ] && BAD5=$((BAD5+1)); done
ls "$S"/shards/V-*.tsv 2>/dev/null | sed 's|.*/V-||; s|\.tsv$||' > "$S/tmp/i5v.txt"
# I5①：merged-into 是 merged-into-{canonical} 前缀形态——整字段等值会把它当缺口误计；
#     i5v.txt 为空时 NR==FNR 吃全表（首文件空 → 第二文件行全进 v[] → BAD5A 恒 0）——改 FILENAME 判别
BAD5A=$(awk -F'\t' 'FILENAME==ARGV[1]{v[$1]=1; next} FNR>1 && $2!="G1" && $7!~/^merged-into/ && $8!="degraded" && !($1 in v){n++} END{print n+0}' \
  "$S/tmp/i5v.txt" "$S/candidates.tsv" 2>/dev/null)
BAD5B=$(awk -F'\t' 'FNR>1 && $2=="G1" && $7!="" && $7!="open" && $7!="closed-by-evidence" && $7!="refuted-by-evidence"{n++} END{print n+0}' \
  "$S/candidates.tsv" 2>/dev/null)
BAD5C=0
while IFS=$'\t' read -r fid fp vd sev crest; do
  [ "$vd" = "confirmed" ] || continue
  if [ -z "$sev" ] || ! grep -q 'CVSS: [^[:space:]]' "$S/findings/$fid.md" 2>/dev/null; then BAD5C=$((BAD5C+1)); fi
done < <(tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$13==""')   # 只查在役行（S9）：撤档行文件已移 audit/
echo "I5 候选分片: $([ "$BAD5" = "0" ] && [ "$BAD5A" = "0" ] && [ "$BAD5B" = "0" ] && [ "$BAD5C" = "0" ] && echo PASS || echo "FAIL(无SELF:$BAD5 缺V分片:$BAD5A 种子未闭合:$BAD5B 缺sev/cvss:$BAD5C)")｜边界: —" | tee -a "$S/audit/invariants.md"

# I6 四相等（S9 新口径）：findings 文件数 == mf 在役行数（lifecycle 空，$13——旧 12 列会话缺列视为在役）；
# mf 总行数 == findings 文件数 + audit/ 撤档件数（reversed-F-* 翻案撤档 + superseded-F-* 合并撤档——行保留不删）；
# C-Inv06 吸收记账：每个 merged-into 候选在 audit/merge.log 有一行 MERGED 留痕且 canonical 候选在册（被吸收只记 also-reported-by 不另起行）
F=$(ls "$S/findings"/F-*.md 2>/dev/null | wc -l | tr -d ' ')
FA=$(ls "$S"/audit/reversed-F-*.md "$S"/audit/superseded-F-*.md 2>/dev/null | wc -l | tr -d ' ')
MF=$(tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | wc -l | tr -d ' ')
# D-089 对账宽容序列化：lifecycle 列 '-'/'N/A'/'n/a' 归一为空（在役）再比——序列化差异不算缺口；
# 报缺判据=双空（mf 行与 findings 文件两侧都无才计入差额；一侧在即不计）
MFA=$(tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '{if($13=="-"||tolower($13)=="n/a")$13=""} $13==""' | wc -l | tr -d ' ')
BAD6=$(awk -F'\t' 'NR==FNR{ if($1=="MERGED"){ logm[$2]=1; canon[$4]=1 } next }
  FNR>1 && $7~/^merged-into/{ if(!($1 in logm)) n++; t=substr($7,13); if(!(t in canon)) n++ }
  END{print n+0}' "$S/audit/merge.log" "$S/candidates.tsv" 2>/dev/null); : "${BAD6:=0}"
echo "I6 对账: $([ "$F" = "$MFA" ] && [ "$MF" = $((F+FA)) ] && [ "$BAD6" = "0" ] && echo "PASS($F+${FA}撤档 吸收:$BAD6)" || echo "FAIL(findings:$F 在役:$MFA 总行:$MF 撤档:$FA 吸收记账:$BAD6)")｜边界: —" | tee -a "$S/audit/invariants.md"

# I7 剪枝事实 confirmer 过（C-Inv07 验收侧复核）：K 消卡（reason ^k）facts_used 引用的每个 FT-id 在 facts 中 status=confirmed
BAD7=$(awk -F'\t' 'NR==FNR{ if(FNR>1 && $6=="confirmed") cf[$1]=1; next }
  FNR>1 && $6~/^k[0-9]/{ if($7==""){n++; next} m=split($7,u,","); for(i=1;i<=m;i++) if(!(u[i] in cf)) n++ }
  END{print n+0}' "$S/facts.tsv" "$S/checks.tsv")
echo "I7 剪枝事实: $([ "$BAD7" = "0" ] && echo PASS || echo "FAIL($BAD7)")｜边界: —" | tee -a "$S/audit/invariants.md"

# I8 分片零丢失（C-Inv08 账本侧口径）：A/SUM 分片 FACT 行合计 vs facts.tsv 数据行——per-FACT 幂等去重（D-088）后
# 允许 差额=去重命中数，非零差额逐轮见 3b manifest（audit/shard-manifest-R*.tsv 行数账本）
RAW8=0
# I8：零命中分片 `grep -c` 打印 0 且退 1，`|| echo 0` 再打一个 0 → $((…)) 语法错中止全循环（RAW8 冻结在
#    首个零命中前的累计）——改先取值再守卫累加，零命中分片不再冻结计数
for f in "$S"/shards/A-*.tsv "$S"/shards/SUM-*.tsv; do
  [ -f "$f" ] || continue
  c8=$(grep -c '^FACT:' "$f" 2>/dev/null); [ -n "$c8" ] || c8=0
  RAW8=$((RAW8 + c8))
done
DED8=$(tail -n +2 "$S/facts.tsv" 2>/dev/null | wc -l | tr -d ' ')
echo "I8 分片对账: 分片FACT=$RAW8 账本行=$DED8 去重命中=$((RAW8-DED8<0 ? 0 : RAW8-DED8))｜边界: 幂等去重口径（重派/换轮号不双计；逐片对账=3b manifest）" | tee -a "$S/audit/invariants.md"

BAD9=0
# C-058/C-Inv09：引文比对先按账本转义契约还原（\\→\、\t→TAB、\n→LF——与 3a esc 同式反演）；
# FACT 行 evidence（第 3 字段）一并纳入（C-Inv09：不只 OBS/SELF）
unesc(){ printf '%s' "$1" | awk '{u=$0; gsub(/\\\\/,"\001",u); gsub(/\\t/,"\t",u); gsub(/\\n/,"\n",u); gsub(/\001/,"\\",u); print u}'; }
for f in "$S"/shards/*.tsv; do
  [ -f "$f" ] || continue
  # 整行读取后按首个 TAB 切——read 的尾字段会剥引文前导 TAB，缩进代码行必误报
  while IFS= read -r line; do
    ref=${line%%$'\t'*}; quote=${line#*$'\t'}
    [ "$quote" = "$line" ] && quote=""
    case "$ref" in OBS:*|SELF:*)
      loc=${ref#*:}; file=${loc%:*}; line_no=${loc##*:}
      case "$line_no" in ''|*[!0-9]*) BAD9=$((BAD9+1)); continue ;; esac
      src=$(awk -v n="$line_no" 'NR==n{print; exit}' "$SRC/$file" 2>/dev/null)
      [ "$src" = "$(unesc "$quote")" ] || BAD9=$((BAD9+1))
      ;;
    FACT:*)
      floc=$(printf '%s' "$quote" | cut -f1); fev=$(printf '%s' "$quote" | cut -f2)
      file=${floc%:*}; line_no=${floc##*:}
      case "$line_no" in ''|*[!0-9]*) BAD9=$((BAD9+1)); continue ;; esac
      src=$(awk -v n="$line_no" 'NR==n{print; exit}' "$SRC/$file" 2>/dev/null)
      [ "$src" = "$(unesc "$fev")" ] || BAD9=$((BAD9+1))
      ;; esac
  done < "$f"
done
echo "I9 引文: $([ "$BAD9" = "0" ] && echo PASS || echo "FAIL($BAD9)")｜边界: —（含 FACT evidence，转义还原后全行相等）" | tee -a "$S/audit/invariants.md"

# I10 引用可解析（C-Inv10）：facts.loc / candidates.loc / mf.sink（位置列）的文件段必须指向 file_inventory 内文件
# （剥 :行号 与 $SRC/ 前缀后整字段比对；空/- 跳过——INV/ext 候选无 loc 如实）
BAD10=$(awk -F'\t' '
  FILENAME==ARGV[2] { if(FNR>1) print $3; next }
  FILENAME==ARGV[3] { if(FNR>1) print $6; next }
  FILENAME==ARGV[4] { if(FNR>1) print $6; next }' "$S/inventories/file_inventory.tsv" "$S/facts.tsv" "$S/candidates.tsv" "$S/machine-fields.tsv" 2>/dev/null | \
  awk -v src="$SRC/" '{ r=$0; if(r=="" || r=="-") next; if(index(r,src)==1) r=substr(r,length(src)+1); sub(/:[0-9]*$/,"",r); print r }' | LC_ALL=C sort -u > "$S/tmp/i10refs.txt"
  comm -23 "$S/tmp/i10refs.txt" <(awk -F'\t' 'NR>1{print $2}' "$S/inventories/file_inventory.tsv" | LC_ALL=C sort -u) | wc -l | tr -d ' ')
echo "I10 引用可解析: $([ "$BAD10" = "0" ] && echo PASS || echo "FAIL($BAD10)——悬空文件清单见 tmp/i10refs.txt 差集")｜边界: —" | tee -a "$S/audit/invariants.md"

# I13 假设点必复核（C-Inv13）：joins 中 assumptions 非空 ⇒ follow-up 卡（origin_ref=join_id）已闭合（非 unchecked）
BAD13=$(awk -F'\t' 'NR==FNR{ if(FNR>1){ jl[$1]=$6 } next }
  FNR>1 && $2=="ext" && $4 in jl { closed[$4]=($5!="unchecked") }
  END{ for(k in jl) if(jl[k]!="" && !(k in closed)) n++; print n+0 }' "$S/joins.tsv" "$S/checks.tsv" 2>/dev/null); : "${BAD13:=0}"
echo "I13 假设点: $([ "$BAD13" = "0" ] && echo PASS || echo "FAIL($BAD13)")｜边界: 拼链轮未跑时为空检（0 行 joins）" | tee -a "$S/audit/invariants.md"

# I11 级联（C-Inv11）：K 消卡 facts_used 非空且其中每个 FT-id 都真实存在于 facts.tsv（悬空 id=剪枝证据丢失）
BAD11=$(awk -F'\t' 'NR==FNR{if(FNR>1)f[$1]=1; next}
  FNR>1 && $6~/^k[0-9]/{
    if($7==""){n++; next}
    m=split($7,u,","); for(i=1;i<=m;i++) if(!(u[i] in f)) n++
  } END{print n+0}' "$S/facts.tsv" "$S/checks.tsv")
echo "I11 级联: $([ "$BAD11" = "0" ] && echo PASS || echo "FAIL($BAD11)")｜边界: —" | tee -a "$S/audit/invariants.md"

# I12 band0/1（C-Inv12）：band0/1 卡被任何 K 规则机械关闭即 FAIL（K 门槛挡在产生侧，此处是验收侧复核）
V12=$(awk -F'\t' 'NR==FNR{if(FNR>1 && ($6=="0"||$6=="1"))b[$1]=1;next}
  FNR>1 && $6~/^k[0-9]/{if($3 in b)n++} END{print n+0}' \
  "$S/inventories/sink_inventory.tsv" "$S/checks.tsv")
echo "I12 band0: $([ "$V12" = "0" ] && echo PASS || echo "FAIL($V12)")｜边界: —" | tee -a "$S/audit/invariants.md"

# I15 恢复入口（C-Inv15）：blocked/partial/deferred 卡必须有缺口说明（reason 非空）；
# 入口投影=coverage §4（结构化重派入口：分片指针 + reason 原文 + 状态）——deferred 同列（ext 专属态不单列漏查）
BAD15=$(awk -F'\t' 'NR>1 && ($5=="blocked"||$5=="partial"||$5=="deferred") && $6==""{n++} END{print n+0}' "$S/checks.tsv" 2>/dev/null)
echo "I15 恢复入口: $([ "$BAD15" = "0" ] && echo PASS || echo "FAIL($BAD15)")｜边界: 入口投影=coverage §4" | tee -a "$S/audit/invariants.md"

# I17 写边界（C-Inv17）：目标树在会话起点（SOURCE 落盘时刻）之后无 mtime 变更文件——mtime 口径（粒度=文件系统时间精度）
W17=0
if [ -f "$S/SOURCE" ]; then
  W17=$(find "$SRC" -type f -newer "$S/SOURCE" 2>/dev/null | wc -l | tr -d ' ')
fi
echo "I17 写边界: $([ "$W17" = "0" ] && echo PASS || echo "FAIL($W17)")｜边界: mtime 口径（粒度=文件系统时间精度；会话外产物=OUT 目录树，天然隔离）" | tee -a "$S/audit/invariants.md"

# I14 ID 确定性（C-Inv14，v1.4.0-S10 按类型分派）：无重复；CD-{sink}-{source} / CD-INV-{inv}-{module} /
# CD-F-{file_seq} 三型可反推；CD-X-{origin} 逃逸段计披露不参与反推
DUP14=$(awk -F'\t' 'NR>1{print $1}' "$S/candidates.tsv" 2>/dev/null | sort | uniq -d | wc -l | tr -d ' ')
X14=$(awk -F'\t' 'NR>1 && $1!~/^CD-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9]$/ && $1!~/^CD-INV-/ && $1!~/^CD-F-/ && $1!~/^CD-SEED-/{n++} END{print n+0}' "$S/candidates.tsv" 2>/dev/null)
echo "I14 ID反推: $([ "$DUP14" = "0" ] && [ "$X14" = "0" ] && echo PASS || echo "FAIL(dup:$DUP14 X逃逸:$X14——CD-X- 锚点逃逸段，coverage 披露)")｜边界: CD-X 逃逸段计披露不参与反推" | tee -a "$S/audit/invariants.md"

# I19 枚举核对（C-Inv19/A-085）：三向对账在 phase0 0.5c 落 audit/i19.md，此处只报差异计数
if [ -f "$S/audit/i19.md" ]; then D19=$(grep -cE 'diff=-?[1-9]' "$S/audit/i19.md"); else D19=NA; fi
echo "I19 枚举对账: $([ "$D19" = "0" ] && echo PASS || echo "FAIL($D19)——逐行差异见 audit/i19.md")｜边界: —" | tee -a "$S/audit/invariants.md"

BAD20=0
for f in "$S"/shards/*.tsv; do
  [ -f "$f" ] || continue
  FT=$(grep -n '^TERM:\|^VERDICT:' "$f" | head -1 | cut -d: -f1)
  LO=$(grep -n '^OBS:\|^SELF:' "$f" | tail -1 | cut -d: -f1)
  if [ -n "$FT" ] && [ -n "$LO" ] && [ "$LO" -ge "$FT" ]; then BAD20=$((BAD20+1)); fi
done
echo "I20 先后: $([ "$BAD20" = "0" ] && echo PASS || echo "FAIL($BAD20)")｜边界: —" | tee -a "$S/audit/invariants.md"
```

### G2 闭卷对账（机械——不派 LLM；A-010/C-012/C-016）

```bash
. "$S/env.sh"
# G2 红线（§0）：不做 CVE 复读机——闭卷本地证据独立。三件：三向计数并排 + 每卡下场可指认
# （state 已裁 ⇒ reason 非空或 facts_used 非空/K 关联）+ CVE 编号污染剔除（finding 叙述携带编号即污染）。
# precision 抽检需人工标注——机械层不出数值，只声明边界（D-091 门内禁声）
N_SINK=$(awk -F'\t' 'NR>1' "$S/inventories/sink_inventory.tsv" 2>/dev/null | wc -l | tr -d ' ')
N_BW=$(awk -F'\t' 'NR>1 && $2=="bw"' "$S/checks.tsv" 2>/dev/null | wc -l | tr -d ' ')
N_CARD=$(awk -F'\t' 'NR>1' "$S/checks.tsv" 2>/dev/null | wc -l | tr -d ' ')
N_TERM_ST=$(awk -F'\t' 'NR>1 && $5!="unchecked"' "$S/checks.tsv" 2>/dev/null | wc -l | tr -d ' ')
N_MF=$(tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$13==""' | wc -l | tr -d ' ')
N_CAND=$(awk -F'\t' 'NR>1' "$S/candidates.tsv" 2>/dev/null | wc -l | tr -d ' ')
N_DELV=$(awk -F'\t' 'NR>1 && $8=="delivered"' "$S/candidates.tsv" 2>/dev/null | wc -l | tr -d ' ')
N_MERG=$(awk -F'\t' 'NR>1 && $7~/^merged-into/' "$S/candidates.tsv" 2>/dev/null | wc -l | tr -d ' ')
BADG2A=$(awk -F'\t' 'NR>1 && $5!="unchecked" && $6=="" && $7==""{n++} END{print n+0}' "$S/checks.tsv" 2>/dev/null)
POLL=0; : > "$S/tmp/g2-poll.txt"
for pf in "$S"/findings/F-*.md "$S"/combinations.md; do
  [ -f "$pf" ] || continue
  # 闭卷红线：finding/组合件叙述不得携带 CVE/advisory 编号（训练记忆污染通道——命中即剔除该叙述行证据资格并披露）
  while IFS= read -r ln; do printf '%s\t%s\n' "$(basename "$pf")" "$ln" >> "$S/tmp/g2-poll.txt"; POLL=$((POLL+1)); done < <(grep -nE 'CVE-[0-9]{4}-[0-9]{4,}|GHSA-[a-z0-9-]{4,}' "$pf" 2>/dev/null)
done
{ echo "# G2 闭卷对账（机械——不派 LLM；$(date '+%F %T')）"
  echo "## 三向计数（清单 vs 卡 vs findings——差异项逐条解释，不设相等断言：demand 追踪卡/ext 卡是合法增量）"
  echo "- 清单: sink=${N_SINK} ｜ 卡: 总=${N_CARD}（bw=${N_BW}，demand/fw 追踪卡为 fw 合法增量）｜ 已裁=${N_TERM_ST}"
  echo "- findings: 在役=${N_MF} ｜ 候选下场: 总=${N_CAND} delivered=${N_DELV} merged=${N_MERG}（其余=pending/degraded，coverage §8 披露）"
  echo "- 三向锚点: sink→bw 卡差=$((N_BW-N_SINK))（0=逐 sink 一卡；I3 反向口径同源）；delivered+merged ≤ 总候选=$([ $((N_DELV+N_MERG)) -le "$N_CAND" ] && echo 成立 || echo 破坏)"
  echo "## 每卡下场可指认（state 已裁 ⇒ reason 非空 ∨ facts_used 非空）"
  if [ "$BADG2A" -eq 0 ]; then echo "- 不可指认: 0 张"; else
    echo "- 不可指认: ${BADG2A} 张（下场无 reason 无 K 关联——账本口径缺口，逐卡如下）"
    awk -F'\t' 'NR>1 && $5!="unchecked" && $6=="" && $7==""{print "  - "$1" state="$5"（reason/facts_used 皆空）"}' "$S/checks.tsv"
  fi
  echo "## CVE 编号污染剔除（闭卷红线——A-010：本地证据独立，编号出现即污染）"
  if [ "$POLL" -eq 0 ]; then echo "- findings/combinations 命中: 0 处（闭卷干净）"; else
    echo "- findings/combinations 命中: ${POLL} 处——污染剔除：命中行不作为证据采信，相关 finding 需无编号复检"
    sed 's/^/  - /' "$S/tmp/g2-poll.txt"
  fi
  echo "## precision 抽检（G2 门人工侧）"
  echo "- 需人工：自报 finding 抽样标注 true/false positive——机械层不出数值（门内禁声，D-091 边界声明）"
  echo "结果: $([ "$BADG2A" -eq 0 ] && [ "$POLL" -eq 0 ] && echo PASS || echo "FAIL(不可指认:${BADG2A} 污染:${POLL})")"
} > "$S/audit/g2.md"
cat "$S/audit/g2.md"
```

### G3 双跑稳定（分级契约——A-004/A-041/C-013/C-024/C-Inv18）

```bash
. "$S/env.sh"
# 同 SRC ≥2 done 会话才判（每目标一次）；单跑如实 N.A.。对齐键=fingerprint（path+行内容+class——B-197）：
# 两跑间发生 refreeze 重编号时 cand_id 不可对齐，fingerprint 对齐不丢行（任务 3 语义收口）
PREV=""
for d in $(ls -dt "$OUT"/gensift-* 2>/dev/null); do
  [ "$d" = "$S" ] && continue
  [ -f "$d/STATE" ] && grep -q "done" "$d/STATE" 2>/dev/null || continue
  [ -f "$d/SOURCE" ] && [ "$(cat "$d/SOURCE" 2>/dev/null)" = "$SRC" ] || continue
  PREV="$d"; break
done
# run 输入记录（C-013）：pattern_version（模式表聚合哈希）+ 处置库哈希（feedback/ 全局库+本 run 库——
# 两跑间变更为差异第五类；本 run A4 落行同样改变有效处置输入，如实入哈希）
PVER=$(cat "$SK"/classes/patterns/*.pattern 2>/dev/null | $HASH | cut -c1-16); : "${PVER:=absent}"
DHASH=$(cat "$SK"/feedback/* "$S"/feedback/* 2>/dev/null | $HASH | cut -c1-16); : "${DHASH:=absent}"
printf 'pattern_version\t%s\ndispositions_hash\t%s\nfinished\t%s\n' "$PVER" "$DHASH" "$(date '+%F %T')" > "$S/audit/run-state.tsv"
if [ -z "$PREV" ]; then
  echo "G3: N.A.（单跑）——同 SRC done 会话 <2；双跑后本块自动归因，指标层维持禁声" | tee "$S/audit/stability-diff.md"
  echo "I18 双跑稳定: N.A.（单跑）｜边界: 双跑才判——机械层=分母冻结比对、语义层=confirmed 指纹重合度 ≥0.8" | tee -a "$S/audit/invariants.md"
else
  # 机械层：分母冻结比对（两跑 inventories 冻结哈希一致 ⇒ 枚举层逐字节稳定）。
  # 硬门口径（审查补齐）：cmp 不一致 ∧ refreeze 无留痕 = 机械层分母损坏（无法归因的输入漂移）→ G3 FAIL（EC=3）；
  # cmp 不一致 ∧ refreeze 在档 = 合法重编号路径 → 披露不拦（fingerprint 对齐承接，归因第五类）
  RFN=$(cat "$S/audit/refreeze.log" "$PREV/audit/refreeze.log" 2>/dev/null | wc -l | tr -d ' ')
  MACHBAD=0
  if cmp -s "$S/inventories/frozen.sha256" "$PREV/inventories/frozen.sha256" 2>/dev/null; then
    MACH="一致"
  elif [ "$RFN" -gt 0 ]; then
    MACH="不一致（refreeze 在档 ${RFN} 行——归因第五类 refreeze 差异，fingerprint 对齐承接，披露不拦）"
  else
    MACH="不一致且无 refreeze 留痕（机械层分母损坏——硬门 FAIL，S14 门未过口径）"; MACHBAD=1
  fi
  # 语义层：fingerprint join（在役行）→ 新增/消失/变级 + 重合度 + 归因
  # g3cur/g3prev 均无表头（tail -n +2 剥过）——下方新增/消失段的 awk 建图不得带 FNR>1（首行指纹会被吞，
  # 与 disp-fixed.tsv 同类问题：任务 8 复审遗留，本批修掉）
  tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$13==""{print $2"\t"$3"\t"$4"\t"$1}' | LC_ALL=C sort > "$S/tmp/g3cur.tsv"
  tail -n +2 "$PREV/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$13==""{print $2"\t"$3"\t"$4"\t"$1}' | LC_ALL=C sort > "$S/tmp/g3prev.tsv"
  # C-046 fixed 回归检测（双跑口径）：本跑在役 fingerprint ∩ fixed 处置 → NOTICE + report 处置节高亮
  # （单跑路径由 5a 落账 NOTICE-REGRESSION——audit/disposition-notice.log；本段是双跑归因侧的机械复核；
  #  两输入 disp-fixed.tsv/g3cur.tsv 均无表头——join 不得带 FNR>1，否则首行指纹被吞误报"无命中"）
  : > "$S/tmp/disp-fixed.tsv"
  for df in "$SK"/feedback/dispositions.tsv "$S"/feedback/dispositions.tsv; do
    [ -f "$df" ] && awk -F'\t' 'NR>1 && $2=="fixed"{print $1}' "$df" >> "$S/tmp/disp-fixed.tsv"
  done
  FIXROWS=$(awk -F'\t' 'FILENAME==ARGV[1]{fx[$1]=1; next} ($1 in fx){print $1"\t"$4}' "$S/tmp/disp-fixed.tsv" "$S/tmp/g3cur.tsv")
  FIXG=$(printf '%s\n' "$FIXROWS" | grep -c .); : "${FIXG:=0}"
  awk -F'\t' 'NR==FNR{ pv[$1]=$2; ps[$1]=$3; next } { cv[$1]=$2; cs[$1]=$3
      if(!($1 in pv)) new++; else { if(ps[$1]!=cs[$1]) recl++; if(pv[$1]!=cv[$1]) flip++; }
      bothc++; if($2=="confirmed") curc++ }
    END{ for(k in pv){ if(!(k in cv)) gone++; if(pv[k]=="confirmed") prevc++; if(pv[k]=="confirmed" && cv[k]=="confirmed") bothcc++ }
      print new+0"\t"gone+0"\t"recl+0"\t"flip+0"\t"curc+0"\t"prevc+0"\t"bothcc+0 }' "$S/tmp/g3prev.tsv" "$S/tmp/g3cur.tsv" > "$S/tmp/g3stat"
  read -r GN3 GG3 GR3 GF3 GC3 GP3 GB3 < "$S/tmp/g3stat"
  RATE=1; MIN=$GC3; [ "$GP3" -lt "$MIN" ] && MIN=$GP3
  [ "$MIN" -gt 0 ] && RATE=$(awk -v b="$GB3" -v m="$MIN" 'BEGIN{printf "%.2f", b/m}')
  if [ -f "$PREV/audit/run-state.tsv" ]; then PDH=$(awk -F'\t' '$1=="dispositions_hash"{print $2}' "$PREV/audit/run-state.tsv"); else PDH=""; fi
  [ "$PDH" = "$DHASH" ] && DISP="否" || DISP="是"
  # 判定 = 语义层重合度 ≥0.8 ∧ 机械层无未归因损坏（MACHBAD）
  VERD=$([ "$(awk -v r="$RATE" 'BEGIN{print (r>=0.8)?1:0}')" = "1" ] && [ "$MACHBAD" = "0" ] && echo PASS || echo FAIL)
  MACHX=""; [ "$MACHBAD" = "1" ] && MACHX="｜机械层分母损坏"
  { echo "# G3 双跑稳定（stability-diff——$(date '+%F %T')）"
    echo "- 对照样: $PREV（同 SRC done）｜本次: $S"
    echo "- run 输入: pattern_version=$PVER ｜ 处置库哈希=$DHASH（对照跑=$PDH → 处置库变更: $DISP）"
    echo "- 机械层分母冻结: $MACH"
    echo "## 新增（本跑在役、对照跑无——按 fingerprint 对齐）"
    comm -23 <(cut -f1 "$S/tmp/g3cur.tsv") <(cut -f1 "$S/tmp/g3prev.tsv") | \
      awk -F'\t' 'NR==FNR{ v[$1]=$2; s[$1]=$3; i[$1]=$4; next } $1!=""{print "- "$1" "v[$1]" "s[$1]"（新档 "i[$1]"）"}' "$S/tmp/g3cur.tsv" - | head -30
    [ "$GN3" -eq 0 ] && echo "- （无）"
    echo "## 消失（对照跑在役、本跑无——翻案/refute/合并吸收都算，逐条可追 mf 留痕行）"
    comm -13 <(cut -f1 "$S/tmp/g3cur.tsv") <(cut -f1 "$S/tmp/g3prev.tsv") | \
      awk -F'\t' 'NR==FNR{ v[$1]=$2; s[$1]=$3; i[$1]=$4; next } $1!=""{print "- "$1" "s[$1]"（对照档 "i[$1]"）"}' "$S/tmp/g3prev.tsv" - | head -30
    [ "$GG3" -eq 0 ] && echo "- （无）"
    echo "## 变级（两跑同 fingerprint、severity 不同——refreeze 重编号不影响本段：按 fp 对齐不按 cand_id）"
    join -t$'\t' <(cut -f1,3 "$S/tmp/g3cur.tsv" | LC_ALL=C sort) <(cut -f1,3 "$S/tmp/g3prev.tsv" | LC_ALL=C sort) 2>/dev/null | \
      awk -F'\t' '$2!=$3{print "- "$1" "$3" → "$2}' | head -30
    [ "$GR3" -eq 0 ] && echo "- （无）"
    echo "## 重合度（confirmed 集合，fingerprint 键）"
    echo "- 本跑 confirmed=${GC3} 对照=${GP3} 重合=${GB3} → ${GB3}/min=${MIN} = ${RATE}（阈值 ≥0.8 起步——§10 G3 分级契约）"
    echo "## 归因（差异五分类——机械可得三类如实，其余语义层需人工）"
    echo "- 判定翻转: ${GF3} 条（同 fp verdict 不同）"
    echo "- refreeze 差异: $([ "$RFN" -gt 0 ] && echo "在档（两跑合计 ${RFN} 行）——cand_id 重排不可对齐，本对账按 fingerprint 键" || echo "不在档")"
    echo "- 处置库变更: ${DISP}（dispositions_hash 两跑比对——feedback/ 全局库）"
    echo "- 抽样波动 / L2 发散差异: 语义层归因需人工逐条复核（边界声明——机械层不臆造归因）"
    echo "## fixed 回归检测（C-046——本跑在役指纹 ∩ fixed 处置库）"
    if [ "$FIXG" -gt 0 ]; then
      echo "- NOTICE: ${FIXG} 条回归（已修复同指纹复现——report 处置节高亮；audit/disposition-notice.log）"
      printf '%s\n' "$FIXROWS" | sed 's/^/  - fp=/'
    else
      echo "- （无 fixed 处置命中——回归检测如实为空）"
    fi
    echo "- 不追求语义层 diff 为空（LLM 非确定是已知缺陷，硬门必然自锁死——设计 §10）"
    echo "G3: ${VERD}（重合度 ${RATE}${MACHX}）"
  } > "$S/audit/stability-diff.md"
  echo "I18 双跑稳定: ${VERD}(重合度 ${RATE}${MACHX})｜边界: 机械层=分母冻结比对（不一致且无 refreeze 留痕=FAIL）；语义层归因两类（抽样波动/L2 发散）需人工" | tee -a "$S/audit/invariants.md"
  cat "$S/audit/stability-diff.md"
fi
```

**任何 FAIL 的处置（显式出口，不许无命令空转）**：I2 冻结 FAIL=清单被改过 → 终止并报告（技能缺陷级）；I3/I4/I6/I9 FAIL → 该不变量行原样保留在 invariants.md 交付（如实披露），**不阻塞交付但必须在 report.md 头部披露 FAIL 项**；其余 FAIL 同 I3 口径。修不完不许谎称 PASS。

### CALIBRATION 草案产出（终态知识闭环——B-057/B-118/B-212/B-231/C-048/D-060/D-096）

```bash
. "$S/env.sh"
# CALIBRATION 通道（知识演化闭环——权重常量不动，校准只走本通道 B-057）：
#   机械侧（本块）产出三类候补草案行到 $S/calibration-drafts.tsv：
#   ① out-of-truth-new 真值外新发现：confirmed 在役 finding 的 (class,loc) 不在 sink 清单——pattern 漏报面
#   ② pattern-misfire pattern 误报：per pattern_id（sink_inventory.api 顿号串拆分）命中卡被
#      refuted/no_path/not_applicable 关闭占比 ≥80% 且样本 ≥5——pattern 过宽面
#   ③ disp-promotion 处置晋升（C-048）：处置库 false-positive 同 scope 类段命中 ≥3 → 晋升类页面 FP 卡候选
#   LLM 侧（操作者事后一次判读）：按 gensift-dev/registers/calibration.md 格式补 ERE 草案与判读理由，
#   人工批准后进 pattern 文件/类页面 FP 卡（append-only+批准位 B-115）；写回只写默认套件（D-096）
# pattern_version 必填（B-231：引用实体不带 pattern_version 不可解析——与 G3 run-state/5a 同式聚合哈希）
PVER=$(cat "$SK"/classes/patterns/*.pattern 2>/dev/null | $HASH | cut -c1-16); : "${PVER:=absent}"
printf 'draft_id\ttype\tref_entity\tclass_id\tpattern_id\tpattern_version\tevidence\tdraft_ere\tstatus\n' > "$S/calibration-drafts.tsv"
# ① 真值外新发现（mf 在役 confirmed 的 (sink 侧 loc,class) ∉ sink 清单——pattern 漏报面；
#   sink 列空的 INV/F 轨不属 pattern 漏报面，如实跳过）
awk -F'\t' -v pver="$PVER" -v of="$S/calibration-drafts.tsv" '
  FILENAME==ARGV[1]{ if(FNR>1) sink[$3"\t"$4]=1; next }
  FNR>1 && $13=="" && $3=="confirmed" && $5!="" && $6!=""{
    if(!(($6"\t"$5) in sink))
      printf "CAL-%03d\tout-of-truth-new\t%s\t%s\t-\t%s\tconfirmed 在役但位置不在 sink 清单（pattern 漏报面）\t\tpending\n", ++n, $1, $5, pver >> of }' \
  "$S/inventories/sink_inventory.tsv" "$S/machine-fields.tsv" 2>/dev/null
# ② pattern 误报（pattern→卡 终态占比：sink_inventory.api 顿号串拆分 × checks.ref_seq 逐卡计数）
# draft_id 续传（任务11 终审B P1）：三个 awk 各自 ++n 从 0 重启会撞 CAL-001——②③ 以草案表既有行数续编（与 ps1 单计数器同口径）
CALN=$(awk -F'\t' 'NR>1' "$S/calibration-drafts.tsv" | wc -l | tr -d ' ')
awk -F'\t' -v pver="$PVER" -v of="$S/calibration-drafts.tsv" -v n="$CALN" '
  FILENAME==ARGV[1]{ if(FNR>1){ m=split($5,ids,"、"); for(i=1;i<=m;i++) if(ids[i]!=""){ pmap[ids[i]"\t"$1]=1; cls[ids[i]]=$4 } } next }
  FILENAME==ARGV[2]{ if(FNR>1){ cards[$3]=cards[$3] $1 "\n"; st[$1]=$5 } next }
  END{ for(pk in pmap){ split(pk,a,"\t"); p=a[1]; s=a[2]
      n2=split(cards[s],c,"\n")
      for(i=1;i<=n2;i++){ if(c[i]=="") continue; tot[p]++
        if(st[c[i]]=="refuted"||st[c[i]]=="no_path"||st[c[i]]=="not_applicable") bad[p]++ } }
    for(p in tot){ if(tot[p]>=5 && bad[p]*100/tot[p]>=80)
      printf "CAL-%03d\tpattern-misfire\t%s\t%s\t%s\t%s\t命中 %d 卡中 %d 被 refuted/no_path/not_applicable（≥80%%——pattern 过宽面）\t\tpending\n", ++n, p, cls[p], p, pver, tot[p], bad[p]+0 >> of } }' \
  "$S/inventories/sink_inventory.tsv" "$S/checks.tsv" 2>/dev/null
# ③ 处置晋升（C-048——false-positive 同 scope 类段 ≥3）
for df in "$SK"/feedback/dispositions.tsv "$S"/feedback/dispositions.tsv; do
  [ -f "$df" ] || continue
  CALN=$(awk -F'\t' 'NR>1' "$S/calibration-drafts.tsv" | wc -l | tr -d ' ')
  awk -F'\t' -v pver="$PVER" -v of="$S/calibration-drafts.tsv" -v n="$CALN" '
    FNR>1 && $2=="false-positive"{ split($4,sc,"|"); if(sc[1]!="") c[sc[1]]++ }
    END{ for(k in c) if(c[k]>=3)
      printf "CAL-%03d\tdisp-promotion\t%s\t%s\t-\t%s\tfalse-positive 处置同 scope 类段命中 %d 次（≥3——晋升类页面 FP 卡候选，C-048）\t\tpending\n", ++n, k, k, pver, c[k] >> of }' "$df"
done
DN=$(awk 'NR>1' "$S/calibration-drafts.tsv" | wc -l | tr -d ' ')
echo "CALIBRATION 草案: $DN 行（$S/calibration-drafts.tsv——pattern_version=$PVER；LLM 判读一次补 draft_ere，人工批准后按 gensift-dev/registers/calibration.md 入册；写回只写默认套件 D-096）"
```

### 投影终态报告

```bash
. "$S/env.sh"
# 处置 join 预计算（§10.2——report 处置分组/标注型含到期日/fixed 回归高亮 + coverage 7b 处置统计共用；
# 双库=全局 $SK/feedback + 本 run $S/feedback；expired=复核到期已过（降级 hint，C-043）；
# 两层分离（C-030）：处置只在本投影层 join，machine-fields 的 verdict 列不动）
: > "$S/tmp/disp-rep.tsv"
for df in "$SK"/feedback/dispositions.tsv "$S"/feedback/dispositions.tsv; do
  [ -f "$df" ] || continue
  awk -F'\t' -v today="$(date +%F)" 'NR>1 && $1!=""{
    ex=($7!="" && $7<today)?"expired":"active"
    printf "%s\t%s\t%s\t%s\t%s\n",$1,$2,ex,$7,$5 }' "$df" >> "$S/tmp/disp-rep.tsv"
done
{ echo "# GenSift 审计报告"
  echo "目标: $SRC"
  echo ""
  echo "## 概要（在役行——lifecycle 空才进分组；已翻案撤销单列披露）"
  echo "| verdict | count |"; echo "|---|---|"
  tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$13==""{v[$3]++} END{for(k in v) print "| "k" | "v[k]" |"}'
  WD=$(tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$13=="withdrawn"' | wc -l | tr -d ' ')
  echo "- 已翻案撤销 ${WD} 条（lifecycle=withdrawn——mf 行留痕、文件撤 audit/reversed-*；不混入在役分组）"
  echo ""
  echo "## 处置（§10.2 两层分离——处置 join 投影，verdict 列不改写；标注型不抑制照常报告）"
  echo "| disposition | 在役 findings |"; echo "|---|---|"
  awk -F'\t' 'FILENAME==ARGV[1]{ if(FNR>1) mf[$2]=1; next }
    FILENAME==ARGV[2]{ if($1 in mf) c[$2]++ }
    END{ split("false-positive,intended-behavior,compensating-control,accepted-risk,known-issue,duplicate,fixed",o,",")
      for(i=1;i<=7;i++) print "| "o[i]" | "c[o[i]]+0" |" }' "$S/machine-fields.tsv" "$S/tmp/disp-rep.tsv" 2>/dev/null
  DMSN=$(tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$13=="" && $3=="dismissed"' | wc -l | tr -d ' ')
  if [ "$DMSN" -gt 0 ]; then
    echo "### dismissed 裁决（抑制型复核成立——引用处置 ID 见各 finding 头部 dismissed-cite 行，C-044）"
    tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | \
      awk -F'\t' '$13=="" && $3=="dismissed"{print "- "$1"（verdict=dismissed）"}'
  fi
  echo "### 标注型（accepted-risk/known-issue——不抑制，含到期日，C-045）"
  ANN=$(awk -F'\t' 'FILENAME==ARGV[1]{ if(FNR>1) mf[$2]=$1; next }
    FILENAME==ARGV[2]{ if(($1 in mf) && ($2=="accepted-risk"||$2=="known-issue"))
      print "- "mf[$1]" "$2"（"$3"｜到期 "$4"｜批准 "$5"）" }' "$S/machine-fields.tsv" "$S/tmp/disp-rep.tsv" 2>/dev/null)
  if [ -n "$ANN" ]; then printf '%s\n' "$ANN"; else echo "- （无标注型命中——处置库为空或指纹未命中在役行）"; fi
  if [ -f "$S/audit/disposition-notice.log" ] && grep -q '^NOTICE-REGRESSION' "$S/audit/disposition-notice.log" 2>/dev/null; then
    echo "### fixed 回归高亮（C-046——已修复同指纹复现 → NOTICE，audit/disposition-notice.log）"
    grep '^NOTICE-REGRESSION' "$S/audit/disposition-notice.log" | sed 's/^/  - /'
  fi
  echo ""
  echo "## 验收不变量"
  if grep -q "FAIL" "$S/audit/invariants.md" 2>/dev/null; then
    echo "**存在 FAIL 项（如实披露，逐条见 audit/invariants.md）：**"
    grep "FAIL" "$S/audit/invariants.md" | sed 's/^/- /'
  else
    echo "- 全部 PASS"
  fi
  echo ""
  echo "## 逐漏洞（severity 降序——在役行）"
  tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | \
    awk -F'\t' 'BEGIN{r["critical"]=5;r["high"]=4;r["medium"]=3;r["low"]=2;r["info"]=1}
      $13==""{print r[$4]+0"\t"$0}' | sort -t$'\t' -k1,1rn | cut -f2- | \
    awk -F'\t' '{printf "### [%s] %s\n- 类: %s ｜ sink: %s\n- 详情: findings/%s.md\n\n",$4,$1,$5,$6,$1}'
  echo "### 已翻案撤销（withdrawn——留痕不删除，不混入上表）"
  tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | \
    awk -F'\t' '$13=="withdrawn"{print "- "$1"（"$3" → 撤档 audit/reversed-"$1"*.md）"}'
  echo ""
  # B-033/A-012/A-035：reasoning-only 类（类页面标 "> oracle: none"）的 finding 显式交人工 triage——不冒充机械定论
  echo "## Human Triage（reasoning-only 类——无机械/执行 oracle，最终裁决交人工）"
  RO=$(grep -l '^> oracle: none' "$SK"/classes/*.md 2>/dev/null | sed 's|.*/||; s|\.md$||' | LC_ALL=C sort | tr '\n' ' ')
  echo "- reasoning-only 类集合: ${RO:-（无——机械类全量）}"
  tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | \
    awk -F'\t' '$12=="yes" && $3!="refuted" && $3!="dismissed"{printf "  - [%s] %s（%s）→ 人工 triage\n",$4,$1,$3}'
  echo "- 旧会话 10 列 machine-fields 无该列时上表为空——以类页面标记重新核对"
} > "$S/report.md"

{ echo "# Coverage（"没发现"必须能解释）"
  echo ""
  echo "## 1 卡状态分布"
  echo "| state | count |"; echo "|---|---|"
  awk -F'\t' 'NR>1{v[$5]++} END{for(k in v) print "| "k" | "v[k]" |"}' "$S/checks.tsv" | LC_ALL=C sort
  echo ""
  echo "## 2 类×语言检测可得性（无 pattern 的格子=该类该语言零检测；语言列由 langpacks/ 目录自派生——协议零语言假设）"
  LANGS=$(for d in "$SK"/langpacks/*/; do [ -d "$d" ] && basename "$d"; done 2>/dev/null | LC_ALL=C sort | tr '\n' ' ')   # 目录枚举（与 ps1 -Directory 同口径——langpacks 根现在有机制层数据文件 sensitive-modules.txt，不能当语言列）
  echo "| class | $(printf '%s' "$LANGS" | sed 's/ / | /g') |"
  echo "|---|$(printf '%s' "$LANGS" | awk '{for(i=1;i<=NF;i++)printf "---|"}')"
  for c in $(ls "$SK"/classes/patterns/*.pattern 2>/dev/null | sed 's|.*/||; s|-[^-]*\.pattern$||' | LC_ALL=C sort -u); do
    line="| $c "
    for l in $LANGS; do
      if [ -f "$SK/classes/patterns/$c-$l.pattern" ]; then line="$line| ✓ " ; else line="$line| ✗ " ; fi
    done
    echo "$line|"
  done
  echo ""
  echo "（本 run 实际扫过的语言: $LANGS）"
  echo ""
  echo "## 3 未覆盖文件类型（全库后缀 − 已入清单后缀 的差集——差集里的类型零卡零检测）"
  COVSUF=$( { cat "$SK"/langpacks/*/includes.txt 2>/dev/null; printf '%s\n' '*.yml' '*.yaml' '*.jinja2' '*.xml' '*.md' '*.txt' '*.json' '*.lock' '*.log' '*.gitignore'; } | sed -n 's/^\*\.\([A-Za-z0-9]*\)$/\1/p' | LC_ALL=C sort -u | tr '\n' ' ')
  find "$SRC" -type f -not -path '*/.git/*' 2>/dev/null | \
    sed -n 's/.*\.\([A-Za-z0-9]*\)$/\1/p' | LC_ALL=C sort | uniq -c | sort -rn | \
    awk -v cov="$COVSUF" 'BEGIN{n=split(cov,c," "); for(i=1;i<=n;i++) k[c[i]]=1} !($2 in k){print "- ."$2" ×"$1"（零检测）"}'
  echo "- 上表为空=目标库无清单外代码类型；已入清单后缀=$COVSUF"
  echo ""
  echo "## 3b generated 清单（A-067/A-068：role=generated 只免 term 卡，sink/source grep 照跑；命中非零须人工签字豁免）"
  echo "| file | sink模式命中 | 人工签字 |"
  echo "|---|---|---|"
  NG=0
  while IFS= read -r gf; do
    [ -n "$gf" ] || continue
    NG=$((NG+1))
    n=$(awk -F'\t' -v f="$gf" 'NR>1 && index($3,f":")==1' "$S/inventories/sink_inventory.tsv" 2>/dev/null | wc -l | tr -d ' ')
    echo "| $gf | $n | （空=未豁免） |"
  done < <(awk -F'\t' 'NR>1 && $6=="generated"{print $2}' "$S/inventories/file_inventory.tsv")
  [ "$NG" -eq 0 ] && echo "| （无 generated 文件） | - | - |"
  echo ""
  echo "## 4 blocked/partial/deferred 恢复入口（C-Inv15 结构化：状态+缺口原因+重派入口；deferred 同列）"
  awk -F'\t' 'NR>1 && ($5=="blocked"||$5=="partial"||$5=="deferred"){print "- "$1" ["$5"] 缺口: "$6" → 重派入口: 分片 "$1"（重派=2b ext/普通分支按 kind；blocked 的 at:file:line 见 reason）"}' "$S/checks.tsv" | head -30
  echo "- deferred 卡（ext 专属——证据需带外输入）: $(awk -F'\t' 'NR>1 && $5=="deferred"' "$S/checks.tsv" | wc -l | tr -d ' ') 张；空=无"
  echo ""
  echo "## 4b K 规则分布（C-010①：refuted/no_path/not_applicable/blocked 按 K 规则归因计数）"
  awk -F'\t' 'NR>1 && $6~/^k[0-9]/{k[substr($6,1,index($6,":")-1)]++} END{for(x in k) print "| "x" | "k[x]" |"; if(!length(k)) print "| （无 K 消卡在案） | 0 |"}' "$S/checks.tsv" | LC_ALL=C sort
  echo "（K1 uncontrolled→refuted / K1b intended→not_applicable / K2 kills→blocked / K3 no_edge / K4 dead——只关 band2 卡）"
  echo ""
  echo "## 4c dangling joins 与 guard 离群（B-093/B-145：发散输入全口径——无对端/未知防护段如实披露）"
  echo "- joins.tsv: $(tail -n +2 "$S/joins.tsv" 2>/dev/null | wc -l | tr -d ' ') 行 ｜ follow-up 卡（origin_ref=JN-*）: $(awk -F'\t' '$2=="ext" && $4~/^JN-/' "$S/checks.tsv" 2>/dev/null | wc -l | tr -d ' ') 张 ｜ dangling: $( (wc -l < "$S/tmp/joins-dangling.txt" 2>/dev/null || echo 0) | tr -d ' ') 行（egress/ingress 无对端——L2 frontier 已入发散输入）"
  sed 's/^/  - dangling /' "$S/tmp/joins-dangling.txt" 2>/dev/null | head -20
  echo "- guard 离群源（guards 五段含 unknown）: $(awk -F'\t' 'NR>1 && $7~/unknown/' "$S/inventories/source_inventory.tsv" 2>/dev/null | wc -l | tr -d ' ') / $(awk -F'\t' 'NR>1' "$S/inventories/source_inventory.tsv" 2>/dev/null | wc -l | tr -d ' ')"
  awk -F'\t' 'NR>1 && $7~/unknown/{print "  - 离群 "$1" "$3" guards="$7}' "$S/inventories/source_inventory.tsv" 2>/dev/null | head -20
  echo ""
  echo "## 4d 不变式评估覆盖矩阵（B-088⑬：INV 卡 × module × 终态——每格下场可查）"
  echo "| inv×module | 终态分布 |"; echo "|---|---|"
  awk -F'\t' '$2=="ext" && $1~/^CK-ext-INV-/{ k=$1; sub(/^CK-ext-/,"",k); print k"\t"$5 }' "$S/checks.tsv" 2>/dev/null | LC_ALL=C sort | \
    awk -F'\t' '{c[$1"|"$2]++; keys[$1]=1} END{for(x in keys){ line=""; for(s in c){ split(s,a,"|"); if(a[1]==x) line=line" "a[2]"="c[s] } print "| "x" |"line" |" } }' | LC_ALL=C sort
  [ "$(awk -F'\t' '$2=="ext" && $1~/^CK-ext-INV-/' "$S/checks.tsv" 2>/dev/null | wc -l | tr -d ' ')" -eq 0 ] && echo "| （无 INV ext 卡——L2 不变式轨未发卡或已全闭合清档） | - |"
  echo ""
  echo "## 5 G1 锚点与 CVE/advisory 种子行"
  cat "$S/audit/g1.md" 2>/dev/null || echo "- G1 未跑"
  awk -F'\t' '$2=="G1"{print "- 种子行 "$1" verdict_state="$7" loc="$6}' "$S/candidates.tsv" 2>/dev/null
  echo "- 种子行闭合规则（A-086）：只有本地证据独立支持/证伪才许改 state（closed-by-evidence/refuted-by-evidence）；邻近 finding 不替代闭合"
  echo ""
  echo "## 6 ext 卡与不变式轨"
  echo "- ext 卡: $(awk -F'\t' '$2=="ext"' "$S/checks.tsv" | wc -l | tr -d ' ')（含 INV 卡 $(awk -F'\t' '$2=="ext" && $1~/INV/' "$S/checks.tsv" | wc -l | tr -d ' ')，INV 按 invariant×module 发卡）"
  EXT_T=$(awk -F'\t' '$2=="ext"' "$S/checks.tsv" | wc -l | tr -d ' ')
  EXT_C=$(awk -F'\t' '$2=="ext" && $5!="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
  EXT_D=$(awk -F'\t' '$2=="ext" && $5=="deferred"' "$S/checks.tsv" | wc -l | tr -d ' ')
  echo "- ext 闭合率: ${EXT_C}/${EXT_T}（ext 不计入分母覆盖率，单独披露——A-057）｜ deferred: ${EXT_D}（零 deferred 为理想终态口径，非零如实披露）"
  echo "- 弱源入账未发卡: weak=$(awk -F'\t' 'NR>1 && $4=="weak"' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ') ｜ persisted_read=$(awk -F'\t' 'NR>1 && $4=="persisted_read"' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ')（demand 追踪卡 $(awk -F'\t' '$2=="fw" && $1~/^CK-fw-P/' "$S/checks.tsv" | wc -l | tr -d ' ') 张） ｜ external_message=$(awk -F'\t' 'NR>1 && $4=="external_message"' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ') ｜ lib_api=$(awk -F'\t' 'NR>1 && $4=="lib_api"' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ')（库模式公共 API 面：入清单不预发 fw 卡——fw 通道只剩 demand 追踪卡，如实披露）"
  echo "- family 修正 diff: $( (wc -l < "$S/audit/family-corrections.tsv" 2>/dev/null || echo 0) | tr -d ' ') 行（audit/family-corrections.tsv）"
  echo "- refreeze 记录: $( (wc -l < "$S/audit/refreeze.log" 2>/dev/null || echo 0) | tr -d ' ') 行（audit/refreeze.log；ext 卡不触发 refreeze）"
  echo ""
  echo "## 7 降级与平台缺口（如实披露）"
  cat "$S/audit/coverage-degraded.log" 2>/dev/null | sed 's/^/- /' || echo "- 无降级记录"
  echo "- 级联收益 K1/K1b/K2/K3/K4（uncontrolled→refuted / intended→not_applicable / kills→blocked（reason 记 at:file:line 恢复入口）/ no_edge→no_path / dead(reflection_checked 非空)→no_path——只关 band2 卡，机械匹配只认 scope 两列）"
  RLOGN=$(grep -c '^RETRACT' "$S/audit/retract.log" 2>/dev/null); : "${RLOGN:=0}"
  echo "- 撤销留痕: ${RLOGN} 行（audit/retract.log——翻案→派生事实级联撤销→K 关闭卡重置 unchecked；L1 回升仅此通道合法）"
  echo "- role 分布: $(awk -F'\t' 'NR>1{v[$6]++} END{for(k in v) printf "%s=%s ",k,v[k]}' "$S/inventories/file_inventory.tsv")（term 卡只发 role∈{app,config}；secrets 例外：test/vendor 路径 sink 照发 bw 卡）"
  echo "- ext deferred: $(awk -F'\t' '$2=="ext" && $5=="deferred"' "$S/checks.tsv" | wc -l | tr -d ' ')（证据需带外输入，如实披露不阻塞交付）"
  echo "- guard 三跳复核（B-082）: bound=$(awk -F'\t' '$2=="bound"' "$S/audit/guard-bind-review.log" 2>/dev/null | wc -l | tr -d ' ') ｜ unbound=$(awk -F'\t' '$2=="unbound"' "$S/audit/guard-bind-review.log" 2>/dev/null | wc -l | tr -d ' ')（audit/guard-bind-review.log；unbound=绑定失效族如实披露，不翻账）"
  echo "- CALIBRATION 草案（知识闭环）: $(awk 'NR>1' "$S/calibration-drafts.tsv" 2>/dev/null | wc -l | tr -d ' ') 行（$S/calibration-drafts.tsv——真值外新发现/pattern 误报/处置晋升三路候补；LLM 判读一次+人工批准后按 gensift-dev/registers/calibration.md 入册）"
  echo "- 对称反转复核（B-020）: 已抽样 $(awk 'END{print NR-1}' "$S/audit/reversal-sampled.tsv" 2>/dev/null || echo 0) 张 ｜ 已复核 $(awk 'END{print NR-1}' "$S/audit/reversal-reviewed.tsv" 2>/dev/null || echo 0) 张 band0/1 refuted/no_path 卡（reversed $(awk -F'\t' '$2=="reversed"{n++} END{print n+0}' "$S/audit/reversal-reviewed.tsv" 2>/dev/null) 张——卡重置 unchecked 重走五步，旧 finding 的 mf 行 lifecycle=withdrawn（行保留）+文件撤 audit/reversed-*；已抽样>已复核=派发后未回收，如实披露）"
  echo ""
  echo "## 7b 处置统计（§10.2——C-047/C-010：FP 率/accept 存量/过期清单）"
  NGD=$(tail -n +2 "$SK"/feedback/dispositions.tsv 2>/dev/null | wc -l | tr -d ' ')
  RLD=$(tail -n +2 "$S"/feedback/dispositions.tsv 2>/dev/null | wc -l | tr -d ' ')
  echo "- 处置库: 全局 ${NGD} 行（\$SK/feedback/）+ 本 run ${RLD} 行（\$S/feedback/——A4 落行，批后合并: gensift-dev/feedback-global/merge-pending.sh）"
  DST=$(awk -F'\t' 'FILENAME==ARGV[1]{ if(FNR>1){ tot++; mf[$2]=1 } next }
    FILENAME==ARGV[2]{ if($1 in mf) c[$2]++ }
    END{ printf "%d %d %d %d %d %d %d %d", tot, c["false-positive"]+0, c["accepted-risk"]+0, c["known-issue"]+0, c["intended-behavior"]+0, c["compensating-control"]+0, c["duplicate"]+0, c["fixed"]+0 }' "$S/machine-fields.tsv" "$S/tmp/disp-rep.tsv" 2>/dev/null)
  : "${DST:=0 0 0 0 0 0 0 0}"
  set -- $DST
  DTOT=${1:-0}; DFP=${2:-0}; DAR=${3:-0}; DKI=${4:-0}; DIB=${5:-0}; DCC=${6:-0}; DDUP=${7:-0}; DFX=${8:-0}
  echo "- 处置命中（在役 join，含已过期）: false-positive=${DFP-0}｜accepted-risk=${DAR-0}｜known-issue=${DKI-0}｜intended-behavior=${DIB-0}｜compensating-control=${DCC-0}｜duplicate=${DDUP-0}｜fixed=${DFX-0}"
  echo "- FP 率: $(awk -v fp="${DFP-0}" -v tot="${DTOT-0}" 'BEGIN{printf "%.1f", (tot>0?fp*100.0/tot:0)}')%（false-positive ${DFP-0} / 在役 ${DTOT-0}——操作者反馈口径，非 ground truth；G2 抽检另计）"
  echo "- accept 存量: $(( ${DAR-0} + ${DKI-0} ))（accepted-risk ${DAR-0} + known-issue ${DKI-0}——标注型不抑制；门禁计存量不计新增，gate.json 投影 P2 二期）"
  EXPN=$(awk -F'\t' '$3=="expired"{n++} END{print n+0}' "$S/tmp/disp-rep.tsv" 2>/dev/null); : "${EXPN:=0}"
  echo "- 过期处置: ${EXPN} 行（复核到期已过——降级 hint 抑制力失效，待复核不自动删除，C-043；清单如下）"
  awk -F'\t' '$3=="expired"{print "  - "$1" "$2" 到期="$4" 批准="$5}' "$S/tmp/disp-rep.tsv" 2>/dev/null | head -20
  [ "$EXPN" -eq 0 ] && echo "  - （无过期处置在库）"
  echo ""
  echo "## 8 库模式与入口画像"
  LB=$(ls "$S"/recon/app-or-lib.md "$S"/recon/lib-or-app.md 2>/dev/null | head -1)
  if [ -n "$LB" ]; then
    echo "- 库/应用判定: $(head -3 "$LB" | tr '\n' '；')"
  else
    echo "- 库/应用判定: （recon 未产出——分母按应用模式计）"
  fi
  if grep -q '^verdict: lib' "$S/recon/app-or-lib.md" 2>/dev/null; then
    echo "- 分母强度: 机械+语义混合（库模式——source=公共 API 面/调用方传入点/共享类型，guards 语义弱，如实声明）"
  else
    echo "- 分母强度: 机械枚举（应用模式）"
  fi
  echo "- framework 回填: $(awk -F'\t' 'NR>1 && $5!="unknown"' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ')/$(awk -F'\t' 'NR>1' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ')（unknown=未识别）"
  echo "- guards 五段仍 unknown 的入口数: $(awk -F'\t' 'NR>1 && $7~/unknown/' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ') / $(awk -F'\t' 'NR>1' "$S/inventories/source_inventory.tsv" | wc -l | tr -d ' ')"
  echo "- 未交付候选（delivery_state=pending/其他）:"
  awk -F'\t' 'NR>1 && $8!="delivered" && $8!="degraded"{print "  - "$1" verdict="$7" delivery="$8" loc="$6}' "$S/candidates.tsv" 2>/dev/null
  awk -F'\t' 'NR>1 && $8=="degraded"{print "  - "$1" delivery=degraded（Verifier 两轮未产出合法裁决）"}' "$S/candidates.tsv" 2>/dev/null
  echo "- 平台: 双分支——bash 可用走 POSIX 块（SKILL.md 发起）/ Windows 原生走 .ps1（phases/win-init.md 发起）；黄金等价已验（gensift-dev/replays/golden 58+ 块逐块双跑）"
  echo "- 战果口径（C-016）：确认修复率为最硬证据；复现已披露 CVE 仅辅助（无法排除训练记忆）——修复验证用例=finding 第 7 节验收用例（5d Reporter 纪律），修复回归以该用例重跑为准"
  MODC2=$(awk -F'\t' 'NR>1 && $5 ~ /^mod:/{ v=substr($5,5); print v }' "$S/inventories/file_inventory.tsv" 2>/dev/null | LC_ALL=C sort -u | wc -l | tr -d ' ')   # F1：只认 mod: 语义模块（与 J1 同口径）
  echo "- 组合件（D-055 存在性投影）: combinations.md $([ -s "$S/combinations.md" ] && echo "在档 $(wc -l < "$S/combinations.md" | tr -d ' ') 行（W5 阶段性刷新——语义层，G3 软保证）" || { [ "$MODC2" -lt 2 ] && echo "N/A（单模块——组合件通道未开，与 J1 同口径不记降级）" || echo "未产出（降级在案——audit/coverage-degraded.log）"; })"
  echo "- 拼链账本（B-122/B-142）: joins.tsv $(tail -n +2 "$S/joins.tsv" 2>/dev/null | wc -l | tr -d ' ') 行（Egress=契约=Ingress；assumptions→follow-up 卡 $(awk -F'\t' '$2=="ext" && $4~/^JN-/' "$S/checks.tsv" 2>/dev/null | wc -l | tr -d ' ') 张；dangling 见 4c）"
  echo "- 偏差记录（B-141/B-214，登记在案）：findings/*+machine-fields 由主循环 5a 机械投影产出（设计 §9 归 Reporter 单写）——骨架与证据链是纯投影非创作，语义扩写归 Reporter 5d；语义合并/joins/combinations 的语义判定归 Reporter、账本迁移归主循环协议命令（两写者分工已在 reporter.md 同步）"
  echo "- 未实现机制: 基准矩阵 M2-M4 分级资产（任务11 终审联动，C-015）｜ gate.json 门禁投影（C-045 P2 二期——标注型计存量不计新增）——CALIBRATION 草案通道已落（$S/calibration-drafts.tsv 三路候补+gensift-dev/registers/calibration.md 入册格式）；处置账本 dispositions §10.2 已落（feedback/dispositions.tsv 八列账本+2e 信封 join+live/report/coverage 三处投影+批后合并通道）；G2 闭卷/G3 双跑/语义合并/joins/combinations 已落（audit/g2.md、audit/stability-diff.md、2d 合并轮、phases/joins.md）"
  echo ""
  echo "## 9 调度与派发口径"
  echo "- band2 路径（v1.4.0-S5 已裁决入设计）: band2 bw 卡同走 2b Analyzer 五步 + 2c Summarizer 级联燃料——宁多勿漏，成本在 run-estimate 披露"
  echo "- 排序保底（v1.4.0-S6 已裁决入设计）: 每轮固定补 fw/term/ext 各 1 张——band0 主导 + 完备性保底"
  # D4-A 队尾降权披露（v2.1-P1）：test/demo 角色 bw 卡不剔除（覆盖红线）但 score=-1 全局排尾——数量与占比在此交代
  TDN=$(awk -F'\t' 'FILENAME==ARGV[1]{ if(FNR>1){ split($3,b,":"); sf[$1]=b[1] } next }
    FILENAME==ARGV[2]{ if(FNR>1 && ($6=="test"||$6=="demo")) td[$2]=1; next }
    FILENAME==ARGV[3]{ if(FNR>1 && $2=="bw"){ tot++; if(($3 in sf) && (sf[$3] in td)) n++ } }
    END{ print n+0, tot+0 }' "$S/inventories/sink_inventory.tsv" "$S/inventories/file_inventory.tsv" "$S/checks.tsv")
  set -- $TDN; TD_A=${1:-0}; TD_T=${2:-0}; TD_P=0; [ "$TD_T" -gt 0 ] && TD_P=$((TD_A * 100 / TD_T))
  echo "- D4-A test/demo 队尾降权（v2.1）: bw 卡中 test/demo 角色文件 ${TD_A}/${TD_T} 张（${TD_P}%）——不剔除（覆盖红线），score=-1 全局排尾；存量会话自动生效（checks 不动，step1 过滤）"
  # D4-D 负向降权在案快照（终态重算同口径——step1 每轮 tmp 信号的一致性对账面）
  NNF=$(wc -l < "$S/tmp/sig-negfile.tsv" 2>/dev/null | tr -d ' '); : "${NNF:=0}"
  NNC=$(wc -l < "$S/tmp/sig-negcls.tsv" 2>/dev/null | tr -d ' '); : "${NNC:=0}"
  echo "- D4-D 负向降权（v2.1）: 文件级证伪密度命中 ${NNF} 文件（refuted≥80%∧≥3 → 剩余卡 −30）｜ 同理由聚类命中 ${NNC} 组（同文件同类 refuted≥3 → −20）｜ suspicion uncontrolled +25（D4-D 校准）"
  PTOT=$(awk -F'\t' 'NR>1 && $2!="ext"' "$S/checks.tsv" | wc -l | tr -d ' ')
  PPAR=$(awk -F'\t' 'NR>1 && $2!="ext" && $5=="partial"' "$S/checks.tsv" | wc -l | tr -d ' ')
  PPCT=0; [ "$PTOT" -gt 0 ] && PPCT=$((PPAR * 100 / PTOT))
  echo "- partial/blocked 阈值（D-086）: partial $PPAR/$PTOT = ${PPCT}%——>10% 阻断全闭合宣称（EXIT_CODE=2）；≤10% 质量缺口如实披露不阻断；blocked 不计缺口（K2 kills 有恢复入口的合法态）"
  if [ -f "$S/audit/plateau.flag" ]; then
    echo "- Plateau 强制停轮（B-074/D-087）: $(cat "$S/audit/plateau.flag")——剩余 unchecked 如实披露，不许谎称全绿"
  else
    echo "- Plateau: 未触发（mf 指纹轨迹见 audit/mf-fp.log）"
  fi
} > "$S/coverage.md"

echo "done" > "$S/STATE"
# 退出码（C-017，语义记录于 README）：0=全闭合 ｜ 1=L1 违例（step0 已写，此处保序不覆盖）｜
# 2=degraded 存在 / plateau 强制停轮 / partial 缺口>10%（D-086）/ 未闭合残留 ｜
# 3=门未过（v1.4.0-S14）：I2 冻结 FAIL / G2 闭卷 FAIL（下场不可指认或 CVE 污染）/ G3 双跑 FAIL（重合度<0.8）
EC=0
if grep -q '^I2 冻结: FAIL' "$S/audit/invariants.md" 2>/dev/null; then
  EC=3
elif grep -q '^结果: FAIL' "$S/audit/g2.md" 2>/dev/null || grep -q '^I18 双跑稳定: FAIL' "$S/audit/invariants.md" 2>/dev/null; then
  EC=3
elif [ -f "$S/EXIT_CODE" ] && [ "$(cat "$S/EXIT_CODE" 2>/dev/null)" = "1" ]; then
  EC=1
else
  U_E=$(awk -F'\t' 'NR>1 && $2!="ext" && $5=="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
  UE_E=$(awk -F'\t' 'NR>1 && $2=="ext" && $5=="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
  DEG=$(grep -c . "$S/audit/coverage-degraded.log" 2>/dev/null); : "${DEG:=0}"
  TOT_E=$(awk -F'\t' 'NR>1 && $2!="ext"' "$S/checks.tsv" | wc -l | tr -d ' ')
  PAR_E=$(awk -F'\t' 'NR>1 && $2!="ext" && $5=="partial"' "$S/checks.tsv" | wc -l | tr -d ' ')
  PCT_E=0; [ "$TOT_E" -gt 0 ] && PCT_E=$((PAR_E * 100 / TOT_E))
  if [ "$U_E" -gt 0 ] || [ "$UE_E" -gt 0 ] || [ "$DEG" -gt 0 ] || [ -f "$S/audit/plateau.flag" ] || [ "$PCT_E" -gt 10 ]; then EC=2; fi
fi
echo "$EC" > "$S/EXIT_CODE"
echo "- 退出码: $EC（0=全闭合 1=L1违例 2=有披露未全闭合 3=I2 FAIL——语义见 README）" >> "$S/coverage.md"
echo "EXIT_CODE=$EC（0=全闭合 1=L1违例 2=有披露未全闭合 3=I2 FAIL——语义见 README）"
```

### 指标计算与报告（A-018——三指标量化，门内禁声约束）

```bash
. "$S/env.sh"
# 三指标=召回/误报/稳定（§0 红线）。门内禁声（§16）：G1/G2/G3 全绿前报告只写事实计数，不声称指标结论
# 锚点召回是事实投影（种子行口径）；误报需 G2 闭卷人工抽检；稳定需 G3 双跑 stability-diff.md——二者未跑一律禁声
SEED_T=$(awk -F'\t' '$2=="G1"' "$S/candidates.tsv" 2>/dev/null | wc -l | tr -d ' ')
SEED_C=$(awk -F'\t' '$2=="G1" && $7=="closed-by-evidence"' "$S/candidates.tsv" 2>/dev/null | wc -l | tr -d ' ')
SEED_R=$(awk -F'\t' '$2=="G1" && $7=="refuted-by-evidence"' "$S/candidates.tsv" 2>/dev/null | wc -l | tr -d ' ')
G1ST=$(grep -c '结果: PASS' "$S/audit/g1.md" 2>/dev/null); : "${G1ST:=0}"
{ echo ""
  echo "## 指标（A-018 三指标量化——门内禁声约束下）"
  echo "- 召回（锚点事实计数）: 锚点闭合 ${SEED_C}/${SEED_T}（另锚点证伪 ${SEED_R}）｜G1 门: $([ "$G1ST" -gt 0 ] && echo PASS || echo "N/A（无锚点输入）")——种子行口径，非全量召回声明"
  echo "- 误报: G2 闭卷抽检未跑——禁声（precision 需人工标注抽检，机械层不出数值）"
  if [ -f "$S/audit/stability-diff.md" ] && grep -q '^G3: ' "$S/audit/stability-diff.md" 2>/dev/null && ! grep -q '^G3: N.A.' "$S/audit/stability-diff.md" 2>/dev/null; then
    echo "- 稳定: G3 双跑在档——diff 与 confirmed 重合度见 audit/stability-diff.md"
  else
    echo "- 稳定: G3 双跑未跑——禁声"
  fi
  if [ "$G1ST" -gt 0 ] && [ -f "$S/audit/stability-diff.md" ] && grep -q '^G3: PASS' "$S/audit/stability-diff.md" 2>/dev/null; then
    echo "- 三门状态：G1 PASS ｜ G3 在档——指标结论按 stability-diff.md + G2 抽检记录出具（M4 基准后接指标计算）"
  else
    echo "- 门内禁声：G2/G3 未全绿，本报告不声称召回/误报/稳定指标（§16——设计失败可证伪）"
  fi
} >> "$S/report.md"

# I16（C-Inv16，report 写后复核）：报告概要分组计数 == machine-fields 在役分组计数——报告数字=账本投影
B16=$(awk -F'\t' 'NR==FNR{ if(FNR>1 && $13==""){g[$3]++} next }
  /^\| (confirmed|unconfirmed|refuted|dismissed) \| [0-9]+ \|$/ {
    split($0,a,"|"); v=a[2]; gsub(/^ +| +$/,"",v); rep[v]=a[3]+0 }
  END{ c=0; for(k in g) if(rep[k]!=g[k]) c++; for(k in rep) if(!(k in g)) c++; print c+0 }' "$S/machine-fields.tsv" "$S/report.md" 2>/dev/null)
echo "I16 报告投影: $([ "$B16" = "0" ] && echo PASS || echo "FAIL($B16)")｜边界: —" | tee -a "$S/audit/invariants.md"

# C-064：完成声明 = 全部不变量与门的原始输出留档 report 附录（不存在"模型宣布完成"的合法路径）
{ echo ""
  echo "## 附录：不变量与门的原始输出（C-064——逐行原文留档，不摘要不改写）"
  echo "### audit/invariants.md"; cat "$S/audit/invariants.md" 2>/dev/null
  echo "### audit/g2.md（G2 闭卷对账）"; cat "$S/audit/g2.md" 2>/dev/null || echo "（未产出）"
  echo "### audit/stability-diff.md（G3——双跑时）"; cat "$S/audit/stability-diff.md" 2>/dev/null || echo "（单跑未产出）"
} >> "$S/report.md"
```

### mermaid 投影（A-142：账本→图，一条命令供人看，不喂回任何账本）

```bash
. "$S/env.sh"
{ echo "# 账本 mermaid 投影（机械生成——仅供人读；禁止作为任何账本/判定的输入回灌）"
  echo '```mermaid'
  echo "flowchart LR"
  # 节点：在役 finding（id 带 severity/class）+ sink/source 实体
  tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$13==""{printf "  %s[\"%s %s %s\"]\n",$1,$1,$4,$5}' | head -200
  # 边：joins（egress →|join_id+confidence| ingress；dangling/带假设点标注）
  tail -n +2 "$S/joins.tsv" 2>/dev/null | awk -F'\t' '{ e=($2=="NA")?"dangling":$2; i=($4=="NA")?"dangling":$4
    printf "  %s -->|\"%s %s%s\"| %s\n",e,$1,$5,($6!=""?" ⚠":"") ,i }' | head -100
  echo '```'
} > "$S/audit/graph-mermaid.md"
echo "mermaid 投影: $(wc -l < "$S/audit/graph-mermaid.md" | tr -d ' ') 行（audit/graph-mermaid.md——只读件）"
```

### 脱敏扫描（C-006：session 含源码级敏感数据，共享前处置）

```bash
. "$S/env.sh"
# 不变量 9 的代价：账本/分片保留源码原文（含 secrets 明文）——共享 session 前先跑本扫描按敏感等级处置
{ echo "# 脱敏扫描（C-006——session 目录按含源码级敏感数据等级处置；归档共享前必跑）"
  echo "- 扫描口径: findings/combinations/shards/audit 中 ≥32 位连续字母数字+/ 串（潜在密钥/token）"
  N=0
  for df in "$S"/findings/*.md "$S"/combinations.md "$S"/shards/*.tsv "$S"/facts.tsv "$S"/machine-fields.tsv; do
    [ -f "$df" ] || continue
    c=$(grep -cE '[A-Za-z0-9+/]{32,}' "$df" 2>/dev/null); : "${c:=0}"   # 守卫形态：零命中时 || echo 0 双写 "0\n0"（任务11 终审B P2 同族，顺手同修）
    [ "$c" -gt 0 ] && { echo "  - $(basename "$df"): ${c} 处"; N=$((N+c)); }
  done
  echo "- 命中合计: ${N} 处——非零时共享前逐处确认（掩码改造会破坏不变量 9 的全文相等契约，处置=按敏感等级隔离归档而非改账本）"
  echo "- 处置声明: 本扫描只计数不改动；secrets 类 finding 在 5d 已掩码交付，原文仅存 session（README 敏感等级口径）"
  echo "## 编码契约自检（C-057——账本文本契约 UTF-8 无 BOM、LF 行尾）"
  BOMN=0
  for df in "$S"/*.tsv "$S"/audit/*.tsv; do
    [ -f "$df" ] || continue
    if [ "$(head -c 3 "$df" | od -An -tx1 | tr -d ' \n')" = "efbbbf" ]; then
      echo "  - $(basename "$df"): BOM 命中"; BOMN=$((BOMN+1))
    fi
    if grep -q $'\r' "$df" 2>/dev/null; then
      echo "  - $(basename "$df"): CR 命中（非 LF 行尾）"; BOMN=$((BOMN+1))
    fi
  done
  echo "- BOM/CR 命中: ${BOMN}（bash 写出本无 BOM——命中=写侧污染，修写入方不改账本）"
} > "$S/audit/desensitize-scan.md"
echo "脱敏扫描: $(grep -c '处——' "$S/audit/desensitize-scan.md" | tr -d ' ') 类命中（audit/desensitize-scan.md）"
```

### 处置反馈通道（A4——操作者动作，主循环外；读全局写本 run 批后合并——C-028）

```bash
. "$S/env.sh"
# A4 落行协议（§10.1/§10.2——C-028）：人工对单条 finding 裁决后向本 run 处置库落一行（七值封闭枚举）。
# 读全局（$SK/feedback/——批后合并的已批准行）+ 写本 run（$S/feedback/——待人工批准后合并：
#   bash gensift-dev/feedback-global/merge-pending.sh "$S"，--pkg 入包为发布路径）。
# 占位符按实际裁决代入后执行：{finding_id}=machine-fields 在役行 id；{value}=七值之一（C-033..C-039）；
# {reason}=须含 file:line 或决策记录编号（C-040）；{scope}=双段"类|触发条件"（C-041——抑制 join 双键匹配，
#   防一张宽处置压制同类真阳性）；{approver}=dev/sec/risk（C-042 谁裁决）；{expiry}=复核到期日 YYYY-MM-DD
#   （C-043——到期未复核自动降级 hint 级：抑制力失效，投影层显示"已过期待复核"，不自动删除）
FID="{finding_id}"; DVAL="{value}"; DREASON="{reason}"; DSCOPE="{scope}"; DAPP="{approver}"; DEXP="{expiry}"
FP=$(awk -F'\t' -v f="$FID" '$1==f{print $2; exit}' "$S/machine-fields.tsv" 2>/dev/null)
[ -n "$FP" ] || { echo "❌ finding 不在册: $FID（处置对象=稳定指纹——须为 machine-fields 行）"; exit 1; }
case "$DVAL" in
  false-positive|intended-behavior|compensating-control|accepted-risk|known-issue|duplicate|fixed) ;;
  *) echo "❌ disposition 非七值封闭枚举: $DVAL"; exit 1 ;;
esac
printf '%s' "$DREASON" | grep -qE ':[0-9]+|[A-Z]{2,6}-[0-9]+' || { echo "❌ reason 须引用证据 file:line 或决策记录编号（C-040）"; exit 1; }
case "$DSCOPE" in
  *'|'*) ;;
  *) echo "❌ scope 须双段 类|触发条件（C-041）"; exit 1 ;;
esac
printf '%s' "$DEXP" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' || { echo "❌ review_expiry 须 YYYY-MM-DD（C-043）"; exit 1; }
mkdir -p "$S/feedback"
[ -f "$S/feedback/dispositions.tsv" ] || printf 'fingerprint\tdisposition\treason\tscope\tsource\tdate\treview_expiry\trun_origin\n' > "$S/feedback/dispositions.tsv"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$FP" "$DVAL" "$DREASON" "$DSCOPE" "$DAPP" "$(date +%F)" "$DEXP" "${S##*/}" >> "$S/feedback/dispositions.tsv"
echo "DISP-ROW $FID｜fp=$FP｜$DVAL｜到期=$DEXP（抑制型下次 2e 信封即生效且须复核理由仍成立；标注型不抑制；fixed 型同指纹复现→NOTICE——批后合并走 merge-pending.sh）"
```
