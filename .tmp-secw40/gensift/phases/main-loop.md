<!-- 引用件：由入口 SKILL.md「阶段索引」进入，按轮执行。每轮严格按 step0–step6 顺序执行，禁止跳过或合并；每轮 step0 开始前重读入口页 SKILL.md 的循环纪律卡（防上下文压缩后丢失纪律）。本件不引用其他引用件。 -->

## 主循环（step0–step6，每轮一轮）

### step0 前置检查（上一轮投影是否完成）

```bash
. "$S/env.sh"
# 旧会话 schema 迁移（断点续跑兼容——v2 两轴 schema 之前的会话；R11 回放发现，幂等：表头非旧形态即零动作）：
# candidates.tsv 旧 7 列（cand_id/card_id/sink_seq/loc 错位存于 source_seq/class_id/summary/state 单轴）。
# 不迁移后果：① 3d 以 9 列追加 → 同文件双 schema 混写（$6/$7/$8 语义随行漂移）② 旧 open 候选不满足
# $7=="open"&&$8=="pending" → 静默退出 2e 验证队列 ③ 旧 CD-00001 形态违反 I14 三型可反推口径。
# 迁移映射：loc←旧第4列；verdict_state←旧 state；delivery_state（open→pending，其余→delivered）；
# cand_id 按 sink_seq 重写为 CD-{sink:05d}-00000（可反推；无 sink_seq 的行保形不重写）。
if [ -f "$S/candidates.tsv" ] && [ "$(head -1 "$S/candidates.tsv")" = "$(printf 'cand_id\tcard_id\tsink_seq\tsource_seq\tclass_id\tsummary\tstate')" ]; then
  awk -F'\t' 'BEGIN{OFS="\t"}
    FNR==1 { print "cand_id","card_id","sink_seq","source_seq","class_id","loc","verdict_state","delivery_state","summary"; next }
    NF>=7 {
      cid=$1
      if($3 ~ /^SINK-[0-9]+$/) cid=sprintf("CD-%05d-00000", substr($3,6)+0)
      dv=($7=="open")?"pending":"delivered"
      print cid,$2,$3,"",$5,$4,$7,dv,$6
    }' "$S/candidates.tsv" > "$S/tmp/cd.mig" && mv "$S/tmp/cd.mig" "$S/candidates.tsv"
  echo "旧会话 candidates.tsv 已迁移至 9 列两轴 schema（$(awk 'NR>1' "$S/candidates.tsv" | wc -l | tr -d ' ') 行——cand_id 按 sink_seq 重写为可反推形态）"
fi
# facts.tsv 旧 12 列仅补表头尾列（origin_card 为第 13 尾列，行级按位读取不受空尾影响——只对齐 schema 声明）
if [ -f "$S/facts.tsv" ] && [ "$(head -1 "$S/facts.tsv")" = "$(printf 'fact_id\ttype\tloc\tevidence\tevidence_hash\tstatus\tscope_type\tscope_ref\treflection_checked\tused_facts\tconfirmer\trevision')" ]; then
  { printf 'fact_id\ttype\tloc\tevidence\tevidence_hash\tstatus\tscope_type\tscope_ref\treflection_checked\tused_facts\tconfirmer\trevision\torigin_card\n'
    tail -n +2 "$S/facts.tsv"; } > "$S/tmp/ft.mig" && mv "$S/tmp/ft.mig" "$S/facts.tsv"
fi
# D6 partial 回收通道（P8：partial 曾是终态无恢复通道——126 行真分析被账本丢弃）：
# partial 卡若分片已含合法 TERM（迟到落盘 / 3a 净化后可读）→ 按 3c 同口径重新迁移并清 partial；
# attempt 列保留作审计痕迹（3f 计费历史不抹）；留痕 audit/partial-recovered.log（幂等：state 离开 partial 后不再命中；
# L1 无涉——partial 本就不在 unchecked 分母，迁移只会减少 partial 计数）
if [ -f "$S/checks.tsv" ]; then
  for ck in $(awk -F'\t' 'NR>1 && $5=="partial"{print $1}' "$S/checks.tsv" 2>/dev/null); do
    f="$S/shards/A-$ck.tsv"
    [ -f "$f" ] || continue
    tline=$(grep '^TERM:' "$f" | head -1)
    tline=${tline//"<TAB>"/$'\t'}   # 迟到分片防御净化——与 3a/3c 同规则（见 3c 注）
    st=$(printf '%s\n' "$tline" | cut -f1 | sed 's/^TERM://')
    [ -n "$st" ] || continue
    knd=$(awk -F'\t' -v id="$ck" '$1==id{print $2; exit}' "$S/checks.tsv")
    # 终态白名单与 3c/3f 同口径（两处必须一致——C-001 纪律）；partial 自身无回收意义跳过
    case "$st" in
      candidate|refuted|not_applicable|no_path|blocked) ;;
      deferred) [ "$knd" = "ext" ] || continue ;;
      *) continue ;;
    esac
    rs=$(printf '%s\n' "$tline" | cut -f2)
    fu=$(printf '%s\n' "$tline" | cut -f3)
    awk -F'\t' -v id="$ck" -v st="$st" -v rs="${rs:-}" -v fu="${fu:-}" \
      'BEGIN{OFS="\t"} $1==id{$5=st; if(rs!="")$6=rs; if(fu!="")$7=fu} {print}' \
      "$S/checks.tsv" > "$S/tmp/ck.tmp" && mv "$S/tmp/ck.tmp" "$S/checks.tsv"
    printf 'PARTIAL-RECOVERED\t%s\t%s\t%s\n' "$ck" "$st" "$(date '+%F %T')" >> "$S/audit/partial-recovered.log"
    echo "D6 partial 回收: $ck → $st（分片迟到 TERM 已入账——attempt 保留作审计痕迹）"
  done
fi
# 首轮跳过
R=$(cat "$S/audit/round_count" 2>/dev/null || echo 0)
if [ "$R" -gt 0 ]; then
  # 检查上一轮的四个投影标记
  for mark in 5a 5b 5c 5d; do
    if [ ! -f "$S/audit/mark-${mark}-R$((R-1))" ]; then
      echo "❌ 上一轮 R$((R-1)) 未完成 step${mark} 投影——先补投影再取卡"
      echo "补法：执行下方 step5 的完整命令块"
      exit 1
    fi
  done
  # L1 单调性：分母卡（origin_ref 空）unchecked 只许不增（违例即停——不吸收为新基线）
  # 追加通道不计入：ext 卡与 step1b demand 追踪卡（origin_ref 非空）是合法增量——两本账分开（A-058 同口径）
  # 回升豁免仅 retract（B-058）：3e 翻案撤销会把 K 关闭卡重置回 unchecked，额度=自上次检查以来
  # audit/retract.log 新增的 RETRACT-RESET 行数（留痕即额度，日志是单一事实源）；其余回升仍然拦
  PREV=$(cat "$S/audit/last_unchecked" 2>/dev/null || echo 9999999)
  CUR=$(awk -F'\t' 'NR>1 && $2!="ext" && $4=="" && $5=="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
  PREVR=$(cat "$S/audit/last_retract_count" 2>/dev/null || echo 0)
  CURR=$(grep -c '^RETRACT-RESET' "$S/audit/retract.log" 2>/dev/null); : "${CURR:=0}"
  ALLOW=$((CURR - PREVR)); [ "$ALLOW" -lt 0 ] && ALLOW=0
  if [ $((CUR - PREV)) -gt "$ALLOW" ]; then
    echo "❌ L1 单调性违反: unchecked $PREV → $CUR（retract 豁免 $ALLOW 后仍超——分母被动过）"
    echo "$PREV" > "$S/audit/last_unchecked"
    # C-017 退出码 1：L1 违例（技能缺陷级）；STATE=aborted-l1 防 Stop hook 继续逼跑
    echo "1" > "$S/EXIT_CODE"; echo "aborted-l1" > "$S/STATE"
    exit 1
  fi
  echo "$CUR" > "$S/audit/last_unchecked"
  echo "$CURR" > "$S/audit/last_retract_count"

  # L3 卡顿换道（B-060/B-072）：近 3 轮分母 unchecked 环形记录——3 轮全相等即"不降"
  # （L1 禁增 ⇒ 不降=相等；任一 unchecked→candidate/refuted/partial/blocked 迁移都会降 CUR，
  #  故相等同时覆盖 B-072 的"无新 candidate 且无 refuted 变化"口径）⇒ 本轮换 fw/term 道（step1 联动）
  printf '%s\n' "$CUR" >> "$S/audit/last3.txt"
  tail -3 "$S/audit/last3.txt" > "$S/tmp/l3.tmp" && mv "$S/tmp/l3.tmp" "$S/audit/last3.txt"
  if [ "$(wc -l < "$S/audit/last3.txt" | tr -d ' ')" -eq 3 ] \
     && [ "$(LC_ALL=C sort -u "$S/audit/last3.txt" | wc -l | tr -d ' ')" -eq 1 ] \
     && [ "$CUR" -gt 0 ]; then
    echo "$R" > "$S/tmp/stall_lane"
    echo "STALL R$R unchecked=$CUR 近3轮不降→本轮 dispatch_list 换 fw/term 道（L3 卡顿换道）" >> "$S/audit/stall.log"
    echo "⚠ L3 卡顿：近 3 轮 unchecked=$CUR 不降——step1 本轮全改派 fw/term 类，audit/stall.log 已留痕"
  else
    rm -f "$S/tmp/stall_lane"
  fi

  # 循环内周期不变量（B-077 跑全口径）：I2/I4 每轮快查留痕（只记不拦——FAIL 由终态口径处置）；
  # I3 三向与 G1 预检的跑全口径 = phase0 0.5/0.5c 预检 + 终态全量（terminal）——分母不可静默缩小
  { printf 'R%s\t' "$R"
    if (cd "$S/inventories" 2>/dev/null && $HASH -c frozen.sha256 >/dev/null 2>&1); then printf 'I2:PASS\t'; else printf 'I2:FAIL\t'; fi
    B4=$(awk -F'\t' '$1~/^CK-/ && $5!~/^(unchecked|candidate|refuted|not_applicable|no_path|blocked|partial|deferred)$/' "$S/checks.tsv" 2>/dev/null | wc -l | tr -d ' ')
    printf 'I4:%s\n' "$([ "$B4" = "0" ] && echo PASS || echo "FAIL($B4)")"
  } >> "$S/audit/invariants-loop.log"
fi
```

### step1 取卡（优先级排序）

```bash
. "$S/env.sh"
# 首轮 facts.tsv 尚未创建——预建表头防 awk fatal（fatal 会清空 bw 队列）
[ -f "$S/facts.tsv" ] || printf "fact_id\ttype\tloc\tevidence\tevidence_hash\tstatus\tscope_type\tscope_ref\treflection_checked\tused_facts\tconfirmer\trevision\torigin_card\n" > "$S/facts.tsv"
# D3' 派发宽度：缺省 4，发起参数 width=N 经 env.sh 贯通到本块（8 卡上限已删——提速走批轮不加宽单轮；
# 旧会话 env.sh 无 WIDTH 变量，此处兜底缺省 4；非正整数一律回落 4）
: "${WIDTH:=4}"; case "$WIDTH" in ''|*[!0-9]*|0) WIDTH=4 ;; esac

# ── 信号预计算（B-049 四项公式补齐：全部机械可算字段，LLM 零判断）──
# B-052/D-077 无净化预判：sanitizer 模式文件（classes/patterns/*.pattern 头 `# role: sanitizer`
# ——设计 §5 模式归属表的 sanitizer 归属）同类 ERE 命中 sink 文件 ⇒ 净化预判存在（不加 +20）；
# 未命中 ⇒ +20。当前仓库 sanitizer 模式文件为空集 ⇒ 全体 +20（排序常数平移，如实披露；模式文件落地即自动分化）
: > "$S/tmp/sig-sanit.tsv"
while IFS=$'\t' read -r card ref; do
  loc=$(awk -F'\t' -v r="$ref" '$1==r{print $3; exit}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
  [ -n "$loc" ] || continue
  f=${loc%:*}; cls=$(awk -F'\t' -v r="$ref" '$1==r{print $4; exit}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
  [ -n "$cls" ] || continue
  for patf in "$SK"/classes/patterns/*.pattern; do
    [ -f "$patf" ] || continue
    grep -q '^# role: *sanitizer' "$patf" || continue
    pbase=$(basename "$patf" .pattern); [ "${pbase%-*}" = "$cls" ] || continue
    while IFS=$'\t' read -r pid ere note; do
      [ -n "$ere" ] || continue
      if grep -qE -- "$ere" "$SRC/$f" 2>/dev/null; then printf '%s\t1\n' "$card" >> "$S/tmp/sig-sanit.tsv"; break 2; fi
    done < <(awk -F'\t' '$1!~/^#/ && $1!="" && $1!="pattern_id"' "$patf")
  done
done < <(awk -F'\t' 'NR>1 && $2=="bw" && $5=="unchecked"{print $1"\t"$3}' "$S/checks.tsv")

# B-053 常量实参 −30：sink 行最深调用组的实参域（剥引号串后）无任何标识符 ⇒ 全字面量 ⇒ 常量实参信号。
# 出处与局限：设计 §7 信号表的 grep 级启发——变量透传/拼接不命中，宁漏信号不加噪
: > "$S/tmp/sig-const.tsv"
while IFS=$'\t' read -r card ref; do
  loc=$(awk -F'\t' -v r="$ref" '$1==r{print $3; exit}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
  [ -n "$loc" ] || continue
  f=${loc%:*}; ln=${loc##*:}
  q=$(awk -v n="$ln" 'NR==n{print; exit}' "$SRC/$f" 2>/dev/null)
  args=$(printf '%s\n' "$q" | sed -n 's/^.*(\([^()]*\)).*$/\1/p')
  args2=$(printf '%s' "$args" | sed 's/"[^"]*"//g')
  if [ -n "$args" ] && ! printf '%s' "$args2" | grep -qE '[A-Za-z_][A-Za-z0-9_.]*'; then
    printf '%s\t1\n' "$card" >> "$S/tmp/sig-const.tsv"
  fi
done < <(awk -F'\t' 'NR>1 && $2=="bw" && $5=="unchecked"{print $1"\t"$3}' "$S/checks.tsv")

# D4-D 负向降权（P4 反馈环饿死——公式此前只有正向加分，证伪结论不改变后续派单）：
# ①文件级证伪密度：该文件已闭合 bw 卡中 refuted 占比≥80% 且 ≥3 张 → 该文件剩余卡 -30
# ②同理由聚类：同文件同类 refuted≥3 → 该 (文件,类) 剩余卡 -20
# 机械口径：闭合=state∉{unchecked}（candidate/blocked/partial 都算"已看过不算证伪"，只有 refuted 计入分子）
: > "$S/tmp/sig-negfile.tsv"; : > "$S/tmp/sig-negcls.tsv"
awk -F'\t' -v nf="$S/tmp/sig-negfile.tsv" -v nc="$S/tmp/sig-negcls.tsv" '
FILENAME==ARGV[1] { if(FNR>1){ split($3,bf,":"); sfile[$1]=bf[1]; scls[$1]=$4 } next }
FNR>1 && $2=="bw" {
  f=($3 in sfile)?sfile[$3]:""; if(f=="") next
  if($5!="unchecked") closed[f]++
  if($5=="refuted"){ ref[f]++; refc[f"\t"scls[$3]]++ }
}
END{
  for(f in ref) if(ref[f]>=3 && closed[f]>0 && ref[f]*100>=closed[f]*80) print f > nf
  for(k in refc) if(refc[k]>=3) print k > nc
}' "$S/inventories/sink_inventory.tsv" "$S/checks.tsv"
# 双侧字节对齐：awk for-in / PS hashtable 枚举序都未定义——两文件排序定序（消费方只做集合查找，序无语义）
LC_ALL=C sort -o "$S/tmp/sig-negfile.tsv" "$S/tmp/sig-negfile.tsv"
LC_ALL=C sort -o "$S/tmp/sig-negcls.tsv" "$S/tmp/sig-negcls.tsv"

# D4-B② 安全敏感模块名词典（langpacks 机制层数据文件——排序信号不是检测规则，不算知识冻结）：
# sink 文件路径或 module 命中词典 ⇒ +10（冷启动概率信号：facts=0 时敏感命名模块先派）
SENS=$(awk '$0!~/^#/ && $0!~/^[ \t]*$/ {printf "%s%s", sep, tolower($0); sep="|"}' "$SK/langpacks/sensitive-modules.txt" 2>/dev/null)

# L3 换道分支（step0 卡顿判定联动 B-060/B-072）：bw 道卡顿 ⇒ 本轮全派 fw/term
if [ -f "$S/tmp/stall_lane" ]; then
  awk -F'\t' 'NR>1 && $5=="unchecked" && ($2=="fw"||$2=="term")' "$S/checks.tsv" | head -"$WIDTH" | cut -f1 > "$S/tmp/dispatch_list.txt"
  echo "⚠ L3 换道生效（R$(cat "$S/tmp/stall_lane" 2>/dev/null)）：本轮 dispatch_list 全为 fw/term 类"
  cat "$S/tmp/dispatch_list.txt"
else
# 四项公式（B-049）：priority = 100·band_score + suspicion + centrality + cve_adj（v2.1 增补冷启动/负向信号）
#   suspicion（B-052/D-077 无净化预判 +20｜B-053 常量实参 −30｜关联 hint 态 uncontrolled 事实 +25——D4-D 校准：
#     +10 从未实质重排过派单，提到 +25 让它能压过 band1 基分以下的噪声）
#   centrality（B-055：入口未鉴权 +20——join source_inventory.auth；核心模块 +10——join file_inventory.module；
#     D4-B① lib_api 引用密度 +5/条 封顶 +20——join source_inventory.entry_type=lib_api，冷启动公共攻击面信号）
#   cve_adj（B-056：已披露 CVE 锚点文件 +15——join candidates.tsv G1 种子 loc；advisory 未提供时全 0，如实无信号）
#   v2.1 增补：D4-B② 安全敏感模块名词典 +10（langpacks/sensitive-modules.txt——排序信号非检测规则）；
#     D4-D 负向降权 ①文件级证伪密度 −30 ②同理由聚类 −20（见上方 sig-neg 预计算）；
#     D4-A test/demo 角色 score=-1 全局排尾（不剔除——覆盖红线；module 列 D4-B③ 回填后 mod +10 近似常数平移，如实披露）
awk -F'\t' -v sens="$SENS" '
NR==FNR { if(FNR>1) { band[$1]=$6; split($3,bb,":"); sfile[$1]=bb[1]; scls[$1]=$4 } next }
FILENAME==ARGV[2] { if($2=="uncontrolled" && $6!="rejected" && $6!="retracted") { split($3,a,":"); susp[a[1]]=1 } next }
FILENAME==ARGV[3] { if(FNR>1){ if($6=="unauth"){ split($3,c2,":"); unauth[c2[1]]=1 } if($4=="lib_api"){ split($3,c3,":"); napi[c3[1]]++ } } next }
FILENAME==ARGV[4] { if(FNR>1){ if($5!="-" && $5!=""){ mod[$2]=1; modv[$2]=$5 } role[$2]=$6 } next }
FILENAME==ARGV[5] { if(FNR>1 && $2=="G1") { f=$6; sub(/:[0-9]*$/,"",f); cvef[f]=1 } next }
FILENAME==ARGV[6] { const[$1]=1; next }
FILENAME==ARGV[7] { sanit[$1]=1; next }
FILENAME==ARGV[8] { negf[$1]=1; next }
FILENAME==ARGV[9] { negc[$0]=1; next }
# 主循环只排 bw 卡（四项公式以 sink band 为主分）；fw/term 不入公式，走下方保底插卡（B-051 口径）
FILENAME==ARGV[10] && FNR>1 && $5=="unchecked" && $2=="bw" {
  b=($3 in band)?band[$3]:1
  score=(b==0?100:b==1?60:10)
  f=($3 in sfile)?sfile[$3]:""
  c=($3 in scls)?scls[$3]:""
  if(f in susp) score=score+25
  if(!($1 in sanit)) score=score+20
  if($1 in const) score=score-30
  if(f in unauth) score=score+20
  if(f in mod) score=score+10
  if(f in cvef) score=score+15
  if(f in napi) score=score+((napi[f]>4)?20:napi[f]*5)
  if(sens!="" && (tolower(f) ~ sens || ((f in modv) && tolower(modv[f]) ~ sens))) score=score+10
  if(f in negf) score=score-30
  if((f "\t" c) in negc) score=score-20
  # F2 绝对队尾（审查修复轮）：普通卡负分钳到 0（负向信号只在非负区间内降位——band2 重罚卡也不沉到 test 之下）；
  # test/demo 不参与四项公式加总，直接 clamp -1——任何普通卡 ≥0 > -1，排尾无例外
  if(score<0) score=0
  if(f in role && (role[f]=="test"||role[f]=="demo")) score=-1
  printf "%s\t%d\n",$1,score
}' "$S/inventories/sink_inventory.tsv" "$S/facts.tsv" \
  "$S/inventories/source_inventory.tsv" "$S/inventories/file_inventory.tsv" \
  "$S/candidates.tsv" "$S/tmp/sig-const.tsv" "$S/tmp/sig-sanit.tsv" \
  "$S/tmp/sig-negfile.tsv" "$S/tmp/sig-negcls.tsv" "$S/checks.tsv" | \
  sort -t$'\t' -k2,2rn | head -"$WIDTH" | cut -f1 > "$S/tmp/next_cards.txt"
# 每轮派发宽度 head -"$WIDTH"（D3'：缺省 4，发起参数 width=N 贯通 env.sh）。出处：v2.1 用户裁决
# （9 过宽——并发不加宽，提速由批轮承担）；宿主并发强可在发起时调高，超宽部分下轮自然续取（无卡丢失）

# 补充 fw/term/ext 卡（每轮各至少 1 张防饥饿——设计 v1.4.0-S6 完备性保底：每轮保底 fw/term/ext 各 1）
awk -F'\t' 'NR>1 && $5=="unchecked" && $2=="fw"' "$S/checks.tsv" | head -1 | cut -f1 >> "$S/tmp/next_cards.txt"
awk -F'\t' 'NR>1 && $5=="unchecked" && $2=="term"' "$S/checks.tsv" | head -1 | cut -f1 >> "$S/tmp/next_cards.txt"
# ext 补充（N2）：ext 卡无 band 不入四项公式主池——与 fw/term 同型防饥饿补充，
# 保证每轮 ext unchecked 至少进 1 张（否则 ext 回主循环后永无派发通道，只能靠 plateau 兜底退出）
awk -F'\t' 'NR>1 && $5=="unchecked" && $2=="ext"' "$S/checks.tsv" | head -1 | cut -f1 >> "$S/tmp/next_cards.txt"

# 保序去重（不破坏 band 优先级）
awk '!seen[$0]++' "$S/tmp/next_cards.txt" > "$S/tmp/dispatch_list.txt"
# D4-A 队尾披露：test/demo 角色 bw 未闭合卡计数（存量会话自动生效——checks 不动，step1 过滤即降权；
# 总量占比与终态口径见 terminal coverage §9；P1：bw 卡吞 test/demo 文件的修复放射）
TDT=$(awk -F'\t' 'FILENAME==ARGV[1]{ if(FNR>1){ split($3,b,":"); sf[$1]=b[1] } next }
  FILENAME==ARGV[2]{ if(FNR>1 && ($6=="test"||$6=="demo")) td[$2]=1; next }
  FILENAME==ARGV[3]{ if(FNR>1 && $2=="bw" && $5=="unchecked" && ($3 in sf) && (sf[$3] in td)) n++ }
  END{ print n+0 }' "$S/inventories/sink_inventory.tsv" "$S/inventories/file_inventory.tsv" "$S/checks.tsv")
[ "$TDT" -gt 0 ] && echo "D4-A: test/demo 角色 bw 卡 $TDT 张全局排尾（score=-1 不剔除——覆盖红线守住）"
cat "$S/tmp/dispatch_list.txt"
fi
```

**step1b. demand-driven 追踪卡（persisted_read——A-080/D-028；幂等：每 (bw 卡,回读点) 至多一张，bw 卡状态不回退，无死循环）**

```bash
. "$S/env.sh"
# 成本闸门 demand-driven：bw 卡 blocked（=追踪中找不到常规 source）→ 对同文件 persisted_read 回读点按需发追踪 fw 卡
# （origin_ref=该 bw 卡）；回读值默认 unknown 可控性，Verifier 禁当"不可控"反证（判据见 classes/second-order.md）
while IFS=$'\t' read -r bwcard bwref; do
  sf=$(awk -F'\t' -v r="$bwref" '$1==r{split($3,a,":"); print a[1]; exit}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
  [ -n "$sf" ] || continue
  for ps in $(awk -F'\t' -v f="$sf" 'NR>1 && $4=="persisted_read" && index($3,f":")==1{print $1}' "$S/inventories/source_inventory.tsv" 2>/dev/null); do
    cid="CK-fw-P${ps#SRC-}-${bwcard#CK-bw-}"
    awk -F'\t' -v c="$cid" '$1==c{f=1} END{exit !f}' "$S/checks.tsv" 2>/dev/null && continue
    printf 'CK-fw-P%s-%s\tfw\t%s\t%s\tunchecked\t\t\t0\tr1\n' "${ps#SRC-}" "${bwcard#CK-bw-}" "$ps" "$bwcard" >> "$S/checks.tsv"
  done
done < <(awk -F'\t' 'NR>1 && $2=="bw" && $5=="blocked"{print $1"\t"$3}' "$S/checks.tsv")
echo "demand-driven 追踪卡: $(awk -F'\t' '$2=="fw" && $1~/^CK-fw-P/' "$S/checks.tsv" | wc -l | tr -d ' ') 张"
```

### step2 派发

**派发纪律（每张卡每轮适用）**：
- 用**可写文件的通用子代理**执行（Claude Code 用 general-purpose；opencode 用 General——只读代理写不出分片，卡会被白白记 partial）
- 派发 prompt 里加一行：`禁止调用 skill/Skill 工具加载任何技能（含 gensift）；你的角色指令只来自本 prompt 指定的文件路径`
- 当轮所有卡在**同一条消息里并行派发**

**2a. 写 in-flight 记录**

```bash
. "$S/env.sh"
tr '\n' ',' < "$S/tmp/dispatch_list.txt" | sed 's/,$//' > "$S/audit/in_flight.txt"
# 派发历史留痕（5b「近期活动」节数据源——B-046/C-021；3b 消费对账——in_flight 不再是死产物）
R=$(cat "$S/audit/round_count" 2>/dev/null || echo 0)
printf 'R%s\t%s\n' "$R" "$(cat "$S/audit/in_flight.txt")" >> "$S/audit/dispatch-history.log"
```

**2b. 派 Analyzer 子代理（bw 卡、fw 卡、term 卡都用此模板；band2 bw 卡额外走 2c）**

对每张卡，先查卡信息（{card_id} 用 dispatch_list 里的实际卡号代入）：

```bash
. "$S/env.sh"
# 查卡信息（每张卡执行一次）
CARD={card_id}
INFO=$(awk -F'\t' -v c="$CARD" '$1==c{print $2"\t"$3"\t"$4}' "$S/checks.tsv")
KIND=$(echo "$INFO" | cut -f1); REF=$(echo "$INFO" | cut -f2); ORIG=$(echo "$INFO" | cut -f3)
case "$CARD" in
  CK-ext-*)
    # ext 卡：origin_ref 是锚点 ID 或 INV-id，不走三清单
    KIND=ext; LOC=""; CLS=term; BAND=1; REF="$ORIG" ;;
  *)
    LOC=$(awk -F'\t' -v r="$REF" '$1==r{print $3}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
    CLS=$(awk -F'\t' -v r="$REF" '$1==r{print $4}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
    BAND=$(awk -F'\t' -v r="$REF" '$1==r{print $6}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
    # bw 卡信封补 api 列（任务9.1 信封对齐——sink_inventory.api=命中 pattern_id 串，Analyzer 净化预判的机械输入）
    API=$(awk -F'\t' -v r="$REF" '$1==r{print $5; exit}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
    # fw 卡从 source 清单查 loc/guards/family（class 固定 term——fw 无固有类，判据读 term.md）
    if [ -z "$LOC" ] && [ "$KIND" = "fw" ]; then
      LOC=$(awk -F'\t' -v r="$REF" '$1==r{print $3}' "$S/inventories/source_inventory.tsv" 2>/dev/null)
      GRD=$(awk -F'\t' -v r="$REF" '$1==r{print $7}' "$S/inventories/source_inventory.tsv" 2>/dev/null)
      FAM=$(awk -F'\t' -v r="$REF" '$1==r{print $8}' "$S/inventories/source_inventory.tsv" 2>/dev/null)
    fi
    [ -z "$LOC" ] && LOC=$(awk -F'\t' -v r="$REF" '$1==r{print $2}' "$S/inventories/file_inventory.tsv" 2>/dev/null)
    ;;
esac
[ -z "$CLS" ] && CLS=term
[ -z "$BAND" ] && BAND=1
# D-081 白名单机械枚举：同文件 sink 清单 seq + 本卡 ID（信封直接喂锚点清单，不是行为规则）——
# 白名单外的 file:line/seq 引用一律非法（analyzer.md「你会收到」承诺的落地侧）
WL=""
if [ -n "$LOC" ]; then
  lfile=${LOC%:*}
  WL=$(awk -F'\t' -v f="$lfile" 'NR>1 && index($3,f":")==1{printf "%s ",$1}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
fi
WL="${WL}${CARD}"
# B-075 重派原因注入：attempt>0 的卡从 3f 失败账本（audit/attempt-failures.log）取最近一次失败原因
FR=""
ATT=$(awk -F'\t' -v id="$CARD" '$1==id{print $8; exit}' "$S/checks.tsv"); : "${ATT:=0}"
[ "$ATT" -gt 0 ] 2>/dev/null && FR=$(awk -F'\t' -v c="$CARD" '$1==c{r=$2} END{print r}' "$S/audit/attempt-failures.log" 2>/dev/null)
```

然后派子代理，prompt（{CARD}/{KIND}/{LOC}/{CLS}/{BAND}/{GRD}/{FAM}/{REF}/{FR}/{API}/{WL} 用上方实际值代入；同类派发字节级相同前缀——固定头三行不变，易变信息只在尾部变量块，A-107）：
```
你是 GenSift Analyzer。读取 {SK}/agents/analyzer.md 并严格遵守。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）。
完成后只返回一行：分片路径 + 行数
——以上固定前缀（A-107：同类派发字节级相同；易变信息只在下方尾部变量块）——
卡：{CARD}｜kind={KIND}｜loc={LOC}｜class={CLS}｜band={BAND}
[bw 卡附] api（命中 pattern 串）：{API}
[fw 卡附] 入口 guards 五段：{GRD}｜family：{FAM}（同族差分参照=audit/guard-family-diff.md）
[ext 卡附] origin_ref：{REF}（锚点 ID 或 INV-id；INV 型读 {SK}/invariants/ 对应 .inv 中该条）
源码根：{SRC}。类页面：{SK}/classes/{CLS}.md（term/fw/ext 卡读 {SK}/classes/term.md）
ID 白名单（机械枚举——同文件清单 seq+本卡）：{WL}（白名单外 file:line/seq 引用一律非法，D-081）
写分片到 {S}/shards/A-{CARD}.tsv
[attempt>0 附] 上次派发失败原因：{FR}——本次必须消除该失败原因后再交付（B-075 结构化重派）
```

**2c. band2 的 bw 卡 → 批量派 Summarizer（事实供 K1 级联；卡本身的终态仍由 2b Analyzer 或 K1 产生）**

```bash
. "$S/env.sh"
# 本轮派发中的 band2 bw 卡按类聚簇（{R} 为当前轮号）
R=$(cat "$S/audit/round_count" 2>/dev/null || echo 0)
for CARD in $(cat "$S/tmp/dispatch_list.txt"); do
  INFO=$(awk -F'\t' -v c="$CARD" '$1==c{print $2"\t"$3}' "$S/checks.tsv")
  REF=$(echo "$INFO" | cut -f2)
  BAND=$(awk -F'\t' -v r="$REF" '$1==r{print $6}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
  CLS=$(awk -F'\t' -v r="$REF" '$1==r{print $4}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
  [ "$BAND" = "2" ] && echo "$CLS $CARD"
done | LC_ALL=C sort > "$S/tmp/band2_batch.txt"
cat "$S/tmp/band2_batch.txt"
```

对每个类（{CLS} 与卡列表用上方实际值代入）派 Summarizer（固定前缀+尾部变量块——A-107）：
```
你是 GenSift Summarizer。读取 {SK}/agents/summarizer.md 并严格遵守。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）。
完成后只返回一行。
——以上固定前缀（A-107）——
类：{CLS}｜源码根：{SRC}｜卡列表：{该类卡号逗号串}
写分片到 {S}/shards/SUM-{CLS}-R{R}.tsv（带轮号，重派不覆盖旧分片）。
```

Confirmer 的派发在 step3 事实入账（3e）之后统一进行——见 3e 末尾（时序：FT-id 先分配，复核后派发）。

**2d. 语义合并轮触发（open 候选 ≥25——B-021/D-110；先去重再验证，验证前执行）**

```bash
. "$S/env.sh"
# 触发计数（S8 两列：verdict_state=open 且 delivery_state=pending；种子行 G1 除外——种子只由本地证据闭合）
PEND25=$(awk -F'\t' 'NR>1 && $7=="open" && $8=="pending" && $2!="G1"{n++} END{print n+0}' "$S/candidates.tsv" 2>/dev/null)
echo "待验证候选: $PEND25（≥25 触发合并轮——B-021/D-110：先去重再验证，省的是验证派发预算）"
if [ "$PEND25" -ge 25 ]; then
  awk -F'\t' 'NR>1 && $7=="open" && $8=="pending" && $2!="G1"{print $1"\t"$5"\t"$6}' "$S/candidates.tsv" > "$S/tmp/merge_input.txt"
  cat "$S/tmp/merge_input.txt"
fi
```

触发时派一个 Reporter 合并轮（可写通用子代理；固定前缀+尾部变量块——A-107；{R} 为当前轮号）：

```
你是 GenSift Reporter（语义合并轮）。读取 {SK}/agents/reporter.md 的「语义合并」节并严格遵守。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）。
完成后只返回一行：分片路径 + 吸收数。
——以上固定前缀（A-107）——
输入：{S}/tmp/merge_input.txt（cand_id/class/loc）｜machine-fields.tsv 只读 join（同 sink 侧定级）。
判据唯一：修复 canonical 也能同时修掉每个被吸收候选才可合并；不许因共享子系统/CWE/路由族/sink 族/攻击话术相似而合并。
同 sink 取最高级；高严重度合并保留全部证据链；不产新事实、不改 delivery_state（S8）。
写分片到 {S}/shards/MERGE-R{R}.tsv（带轮号，重派不覆盖），格式：
MERGE:{canonical cand_id}
ABSORB:{被吸收 cand_id}<TAB>{判据一句话}
不合并的候选不写行。
```

**2d-consume. MERGE 分片消费（机械回写——语义判定归 Reporter，账本迁移归协议命令；幂等：已 merged 不重复记账）**

```bash
. "$S/env.sh"
for mgf in "$S"/shards/MERGE-*.tsv; do
  [ -f "$mgf" ] || continue
  canon=""
  while IFS=$'\t' read -r head rest; do
    case "$head" in
      MERGE:*) canon=${head#MERGE:} ;;
      ABSORB:*)
        [ -n "$canon" ] || continue
        ac=${head#ABSORB:}
        # 幂等守卫：已是 merged-into（任意目标）则跳过；canonical 不得吸收自身
        [ "$ac" != "$canon" ] || continue
        awk -F'\t' -v c="$ac" '$1==c && $7!~/^merged-into/{f=1} END{exit !f}' "$S/candidates.tsv" 2>/dev/null || continue
        # S8 两列：verdict_axis 迁移 merged-into-{canonical}；delivery_state 不动（B-021/D-110）
        awk -F'\t' -v c="$ac" -v tgt="merged-into-${canon}" 'BEGIN{OFS="\t"} $1==c{$7=tgt} {print}' \
          "$S/candidates.tsv" > "$S/tmp/cd.tmp" && mv "$S/tmp/cd.tmp" "$S/candidates.tsv"
        printf 'MERGED\t%s\tinto\t%s\t%s\n' "$ac" "$canon" "${rest:-}" >> "$S/audit/merge.log"
        # 陈旧 V 分片同批撤档（审查必修：5a 见 V 分片即交付——superseded 状态拦不住复活，
        # 吸收时必须撤片，与 3g 翻案撤 reversed-V-* 同式；无 mf 行的 pending 候选同样撤，防当轮 2e 已派分片后吸收复活）
        [ -f "$S/shards/V-$ac.tsv" ] && mv "$S/shards/V-$ac.tsv" "$S/audit/superseded-V-$ac.tsv"
        # 被吸收候选已有在役 finding：lifecycle=superseded_by + 撤档留痕 + 勘误节追加（B-198/C-003/A-140；
        # C-Inv06 吸收不另起行——行保留不删，身份永续）
        cls=$(awk -F'\t' -v c="$ac" '$1==c{print $5; exit}' "$S/candidates.tsv" 2>/dev/null)
        loc3=$(awk -F'\t' -v c="$ac" '$1==c{print $6; exit}' "$S/candidates.tsv" 2>/dev/null)
        fex=""
        if [ -n "$loc3" ]; then
          fb=$(basename "${loc3%:*}"); fb=${fb%.*}
          case "${loc3##*:}" in ''|*[!0-9]*) fex="-${fb}" ;; *) fex="-${fb}-L${loc3##*:}" ;; esac
        fi
        fid="F-${ac}-${cls}${fex}"
        if [ -f "$S/machine-fields.tsv" ] && awk -F'\t' -v f="$fid" '$1==f && $13==""{x=1} END{exit !x}' "$S/machine-fields.tsv"; then
          awk -F'\t' -v f="$fid" 'BEGIN{OFS="\t"} $1==f && $13==""{$13="superseded_by"} {print}' \
            "$S/machine-fields.tsv" > "$S/tmp/mf.tmp" && mv "$S/tmp/mf.tmp" "$S/machine-fields.tsv"
          if [ -f "$S/findings/$fid.md" ]; then
            arc="$S/audit/superseded-$fid.md"; k=1
            while [ -f "$arc" ]; do k=$((k+1)); arc="$S/audit/superseded-$fid-$k.md"; done
            mv "$S/findings/$fid.md" "$arc"
            # 勘误节只追加不删除（A-140/B-018：原文不可改写；投影随 5b/终态重算自动更新——永不永久不一致）
            { echo ""; echo "## 勘误（errata——只追加，原文未改写）"
              echo "- $(date '+%F %T') lifecycle=superseded_by（语义合并：被 ${canon} 吸收——${rest:-同修复点}）——撤档留痕不蒸发；report/live 投影按 lifecycle 滤行"
            } >> "$arc"
          fi
        fi
        # canonical 已交付：also-reported-by 回填（B-024/B-203；未交付时 5a 落行从 merge.log 回填）
        ccls=$(awk -F'\t' -v c="$canon" '$1==c{print $5; exit}' "$S/candidates.tsv" 2>/dev/null)
        cloc=$(awk -F'\t' -v c="$canon" '$1==c{print $6; exit}' "$S/candidates.tsv" 2>/dev/null)
        cfex=""
        if [ -n "$cloc" ]; then
          cfb=$(basename "${cloc%:*}"); cfb=${cfb%.*}
          case "${cloc##*:}" in ''|*[!0-9]*) cfex="-${cfb}" ;; *) cfex="-${cfb}-L${cloc##*:}" ;; esac
        fi
        cfid="F-${canon}-${ccls}${cfex}"
        if [ -f "$S/machine-fields.tsv" ] && awk -F'\t' -v f="$cfid" '$1==f && $13==""{x=1} END{exit !x}' "$S/machine-fields.tsv"; then
          awk -F'\t' -v f="$cfid" -v add="$ac" 'BEGIN{OFS="\t"} $1==f && $13=="" && index(","$9",",","add",")==0{$9=$9 ($9?",":"") add} {print}' \
            "$S/machine-fields.tsv" > "$S/tmp/mf.tmp" && mv "$S/tmp/mf.tmp" "$S/machine-fields.tsv"
        fi
        ;;
    esac
  done < "$mgf"
done
[ -f "$S/audit/merge.log" ] && echo "合并轮: 累计吸收 $(grep -c '^MERGED' "$S/audit/merge.log") 条（audit/merge.log——canonical 落 also-reported-by，被吸收已交付行 superseded_by 撤档）"
```

**2e. 派 Verifier（上一轮 step3d 落账的候选）**

```bash
. "$S/env.sh"
# 找待验证候选（verdict_state=open 且 delivery_state=pending——S8 两列；种子行 card_id=G1 除外——
# CVE/advisory 种子保持 open 待本地证据独立闭合，禁喂给 Verifier）
# V 分片存在但无 VERDICT 行=空口复核，删掉重派；重派上限 2 次后转 degraded（delivery 轴）
awk -F'\t' 'NR>1 && $7=="open" && $8=="pending" && $2!="G1"{print $1}' "$S/candidates.tsv" 2>/dev/null | while read -r cand; do
  vf="$S/shards/V-$cand.tsv"
  if [ -f "$vf" ]; then
    if grep -q '^VERDICT:' "$vf" 2>/dev/null; then continue; fi
    mkdir -p "$S/audit/verify_attempts"
    n=$(cat "$S/audit/verify_attempts/$cand" 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > "$S/audit/verify_attempts/$cand"
    if [ "$n" -ge 2 ]; then
      mv "$vf" "$S/audit/degraded-V-$cand.tsv"
      echo "DEGRADED-V ${cand} 两次空口复核" >> "$S/audit/coverage-degraded.log"
      awk -F'\t' -v c="$cand" 'BEGIN{OFS="\t"} $1==c{$8="degraded"} {print}' \
        "$S/candidates.tsv" > "$S/tmp/cd.tmp" 2>/dev/null && mv "$S/tmp/cd.tmp" "$S/candidates.tsv"
      continue
    fi
    rm -f "$vf"
  fi
  echo "$cand"
done > "$S/tmp/to_verify.txt"
cat "$S/tmp/to_verify.txt"
```

**2e-env. 派发信封构造（机器字段 + OBS 引文 + 处置行 join——S4-A 白名单/B-028/C-044）**

对每个待验证候选，先机械构造派发信封（盲性由命令保证——只传机器字段、A 分片 OBS 引文行与 fingerprint 命中的处置行，不传 Analyzer 叙述/结论——S4-A 按设计 §6 白名单；{cand_id} 用 to_verify.txt 里的实际候选号代入）：

```bash
. "$S/env.sh"
CAND={cand_id}
awk -F'\t' -v c="$CAND" '$1==c{print "候选："c"｜sink="$3"｜source="$4"｜class="$5"｜loc="$6; exit}' "$S/candidates.tsv"
# S4-A：信封按设计白名单补 A 分片的 OBS 引文行（仅引文、≤5 行——不含 TERM/FACT 叙述；
# 盲=不见发现者结论与叙述，非不见观察引文；summary 列明确排除）
CARD=$(awk -F'\t' -v c="$CAND" '$1==c{print $2; exit}' "$S/candidates.tsv" 2>/dev/null)
grep '^OBS:' "$S/shards/A-$CARD.tsv" 2>/dev/null | head -5
# D-104 位置角色词表投影：OBS 行的配对 ROLE 行（root_control/guard/sink_anchor/entry/data_flow）一并进信封
grep '^ROLE:' "$S/shards/A-$CARD.tsv" 2>/dev/null | head -5
# 处置 join（B-028/C-044——§10.2）：fingerprint 命中的处置行进信封，当数据读不跳过分析。
# 指纹与 5a 同式逐字节对齐（path+行内容+class，不含行号——C-032 跨 run 身份；两处必须同式，C-001 纪律）
DLOC=$(awk -F'\t' -v c="$CAND" '$1==c{print $6; exit}' "$S/candidates.tsv" 2>/dev/null)
DCLS=$(awk -F'\t' -v c="$CAND" '$1==c{print $5; exit}' "$S/candidates.tsv" 2>/dev/null)
[ -z "$DCLS" ] && DCLS="term"
DLF=${DLOC%:*}; DLN=${DLOC##*:}
case "$DLN" in ''|*[!0-9]*) DQ="" ;; *) DQ=$(awk -v n="$DLN" 'NR==n{print; exit}' "$SRC/$DLF" 2>/dev/null) ;; esac
DFP=$( { printf '%s\n%s\n%s\n' "$DLF" "$DQ" "$DCLS"; } | $HASH | cut -c1-16)
# 双库读取（C-028 读全局写本 run）：$SK/feedback=批后合并的已批准全局行；$S/feedback=本 run A4 落行（批后待合并）
# 双键匹配（C-041）：fingerprint 命中 ∧ scope 类段=候选类——防一张宽处置压制同类真阳性
# 到期降级（C-043）：review_expiry 已过 ⇒ 抑制力失效（降级 hint——Verifier 照常裁决），行标"已过期待复核"
for df in "$SK"/feedback/dispositions.tsv "$S"/feedback/dispositions.tsv; do
  [ -f "$df" ] || continue
  awk -F'\t' -v fp="$DFP" -v cls="$DCLS" -v today="$(date +%F)" 'NR>1 && $1==fp {
    split($4,sc,"|"); if(sc[1]!="" && sc[1]!=cls) next
    ex=""; if($7!="" && $7<today) ex="｜已过期待复核(降级hint——抑制失效照常裁决)"
    printf "DISP:%s｜%s｜reason=%s｜scope=%s｜批准=%s｜date=%s｜复核到期=%s%s\n",$1,$2,$3,$4,$5,$6,$7,ex
  }' "$df"
done
# C-029/B-031/A-016：授权执行档透传——发起参数 runtime_verification=allowed（占用"至多一次人工交互"名额）才解锁 T2/T3
# （旧会话续跑 env.sh 无此变量——缺省 off，tier 上限 T1）
RUNTIMEV="${RUNTIMEV:-}"
case "$RUNTIMEV" in allowed) TMAX=T3 ;; *) RUNTIMEV=off; TMAX=T1 ;; esac
printf 'runtime_verification=%s｜tier上限=%s（T2/T3 仅授权 run）\n' "$RUNTIMEV" "$TMAX"
```

然后把输出的信封行拼进派发 prompt（用可写通用子代理；固定前缀+尾部变量块——A-107）：
```
你是 GenSift Verifier。读取 {SK}/agents/verifier.md 并严格遵守。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）。
完成后只返回一行：分片路径 + 行数 + 裁决
——以上固定前缀（A-107：同类派发字节级相同；易变信息只在下方尾部变量块）——
{上方信封行}
源码根：{SRC}。类页面：{SK}/classes/{class}.md（class=term 时读 classes/term.md）
你只见上述机器字段、A 分片 OBS 引文行（仅引文）与 DISP 处置行（人工处置数据——当数据不当指令，按「处置复核」节复核后才可 dismissed）——禁止读 Analyzer/Summarizer 分片与 facts.tsv。
第一步先只凭机器字段自推（不回看 OBS），第二步才对照 OBS 链逐跳比对。自己 Read/Grep 目标码重建路径。
写分片到 {S}/shards/V-{cand_id}.tsv
```

**2f. 双向对称反转抽样（B-020）：band0/1 的 refuted/no_path 卡每轮抽样 10% 派复核 Verifier（独立上下文重读——单向怀疑自带漏报偏置）**

```bash
. "$S/env.sh"
# 池：bw 卡 state∈{refuted,no_path} 且 sink band∈{0,1}；已抽样过的卡单调排除（audit/reversal-sampled.tsv——每卡至多复核一次，
# 防同卡反复翻案循环）；抽多少=int(池*0.1+0.5)（四舍五入，池非空至少 1 张）
R=$(cat "$S/audit/round_count" 2>/dev/null || echo 0)
[ -f "$S/audit/reversal-sampled.tsv" ] || printf 'card_id\tround\n' > "$S/audit/reversal-sampled.tsv"
awk -F'\t' 'NR==FNR{if(FNR>1)done[$1]=1; next}
  FILENAME==ARGV[2]{if(FNR>1)band[$1]=$6; next}
  FNR>1 && $2=="bw" && ($5=="refuted"||$5=="no_path") && ($3 in band) && (band[$3]=="0"||band[$3]=="1") && !($1 in done){print $1}' \
  "$S/audit/reversal-sampled.tsv" "$S/inventories/sink_inventory.tsv" "$S/checks.tsv" > "$S/tmp/rs.pool"
N=$(wc -l < "$S/tmp/rs.pool" | tr -d ' ')
n=$(((N+5)/10)); { [ "$n" -lt 1 ] && [ "$N" -gt 0 ]; } && n=1
: > "$S/tmp/reversal_sample.txt"
if [ "$N" -gt 0 ]; then
  # 稳定哈希×轮号盐排序取前 n（确定性抽样——跨机可重放；rand/srand 各 awk 实现序列不同，禁用）
  while IFS= read -r c; do
    printf '%s\t%s\n' "$(printf '%s\n%s' "$c" "$R" | $HASH | cut -c1-16)" "$c"
  done < "$S/tmp/rs.pool" | LC_ALL=C sort | head -"$n" | cut -f2 > "$S/tmp/reversal_sample.txt"
  while IFS= read -r c; do [ -n "$c" ] && printf '%s\tR%s\n' "$c" "$R" >> "$S/audit/reversal-sampled.tsv"; done < "$S/tmp/reversal_sample.txt"
fi
echo "2f 抽样: 池=$N 取=$n"
cat "$S/tmp/reversal_sample.txt"
```

对每个抽中卡号，先机械构造复核信封（只传机器字段；被复核结论的原因叙述不提供——防锚定）：

```bash
. "$S/env.sh"
CARD={card_id}
INFO=$(awk -F'\t' -v c="$CARD" '$1==c{print $2"\t"$3"\t"$5; exit}' "$S/checks.tsv")
LOC=$(awk -F'\t' -v r="$(echo "$INFO" | cut -f2)" '$1==r{print $3; exit}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
CLS=$(awk -F'\t' -v r="$(echo "$INFO" | cut -f2)" '$1==r{print $4; exit}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
BAND=$(awk -F'\t' -v r="$(echo "$INFO" | cut -f2)" '$1==r{print $6; exit}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
printf '复核卡：%s｜kind=%s｜loc=%s｜class=%s｜band=%s｜prior_state=%s（原因叙述不提供——防锚定）\n' \
  "$CARD" "$(echo "$INFO" | cut -f1)" "$LOC" "${CLS:-term}" "$BAND" "$(echo "$INFO" | cut -f3)"
```

然后派复核 Verifier（可写通用子代理，同消息并行；{CARD} 用实际卡号；固定前缀+尾部变量块——A-107）：
```
你是 GenSift 复核 Verifier（对称反转复核——独立上下文重读）。读取 {SK}/agents/verifier.md 并严格遵守（分片名按本 prompt：RV-{CARD}.tsv）。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）；禁读 Analyzer/Verifier 分片与 facts.tsv。
完成后只返回一行：分片路径 + 行数 + REVIEW 结论。
——以上固定前缀（A-107）——
{上方信封行}
源码根：{SRC}。类页面：{SK}/classes/{class}.md（class=term 时读 classes/term.md）
任务：这张卡已被裁"路径不存在/已关闭"。做对称反转——先只凭机器字段自己 Read/Grep 重建路径（≥3 次实际读源码），再回答"为什么它其实是洞"：给得出具体 payload 与请求形态才算反转成立；确实无路径 → 维持。
写分片到 {S}/shards/RV-{CARD}.tsv，格式：
SELF:{file}:{line}<TAB>{全文}
RUBRIC:{判据编号}<TAB>{x|空}
REVIEW:reversed|upheld<TAB>{理由}
```

### step3 收卡

**3a. 引文机械归一化（覆盖 A/V/RV/CONF 分片——OBS/SELF 引文 + FACT evidence；C-058 写行前机械转义）——逐行单命令形态，零自研程序**

```bash
. "$S/env.sh"
# 账本文本契约（C-058）：写行前对引文机械转义（TAB→\t、反斜杠→\\；read 逐行无 \n 场景），
# I9/confirmer 引文核对按同式还原——转义与还原同源，账本永存全文语义（C-059 全行不截断）
esc(){ printf '%s' "$1" | awk '{e=$0; gsub(/\\/,"\\\\",e); gsub(/\t/,"\\t",e); print e}'; }
for f in "$S"/shards/A-*.tsv "$S"/shards/V-*.tsv "$S"/shards/RV-*.tsv "$S"/shards/CONF-*.tsv; do
  [ -f "$f" ] || continue
  : > "$f.norm"
  while IFS= read -r line; do
    # 真宿主摄入净化（实跑教训 2026-08-25）：①字面 <TAB> 记法→真实制表符（子代理按格式文档记法直写）
    # ②loc 绝对路径→相对源码根（否则 $SRC/$file 拼接破碎，归一化/I9/指纹全错）
    # ③D6 格式方差修复（P8 实证 CK-bw-00005/00008——完整分析被记"无TERM"熔断成 partial）：
    #   a) `TERM<TAB>state…`/`RUBRIC<TAB>id…` 无冒号形态 → 分隔 TAB 置换为冒号（`^TERM\t`→`TERM:`——
    #      补完即合法账本行，保留；只插冒号留 TAB 会把 state 挤到第 2 列，3c 仍读出空态）。
    #      裸标签行（无冒号**也无 TAB**，如整行只有 `TERM`）不可修复——按原样入 raw（F3：bash 侧曾产
    #      `TERM:TERM`/ps1 侧 `TERM:` 的双侧发散，统一为跳过修复、原行保留，两侧字节等价）
    #   b) `CARD*`/`DEFINE*` 自创头行剥除（分析员复述卡号/判据的叙事行，非账本行——前缀匹配：CARD:CK-x/DEFINE C1 都命中；
    #      合法标签 OBS:/ROLE:/FACT:/TERM:/SELF:/RUBRIC:/VERDICT:/REVIEW:/MERGE:/ABSORB: 无一以 CARD/DEFINE 开头，零误伤）
    line=${line//"<TAB>"/$'\t'}
    head=${line%%$'\t'*}
    # S8 变体（2026-08-27 真跑实证 CK-bw-00030/31）：`TERM:<TAB>state…`——冒号后先 TAB 再状态
    # （前缀/首字段混淆的镜像形态；3c 读出空态拒收）。机械修复：剥冒号后首个 TAB（state 回到第 1 字段）
    case "$line" in
      TERM:$'\t'*) line="TERM:"${line#TERM:$'\t'}; head="TERM:" ;;
      RUBRIC:$'\t'*) line="RUBRIC:"${line#RUBRIC:$'\t'}; head="RUBRIC:" ;;
    esac
    case "$head" in
      TERM|RUBRIC) if [ "$head" != "$line" ]; then line="$head:"${line#"$head"$'\t'}; head="$head:"; fi ;;
      CARD*|DEFINE*) continue ;;
    esac
    case "$head" in OBS:*|SELF:*)
      loc=${head#*:}
      case "$loc" in "$SRC"/*) loc=${loc#"$SRC"/}; head="${head%%:*}:$loc" ;; esac
      ln=${loc##*:}; file=${loc%:*}
      case "$ln" in ''|*[!0-9]*) printf '%s\n' "$line" >> "$f.norm"; continue ;; esac
      q=$(awk -v n="$ln" 'NR==n{print; exit}' "$SRC/$file" 2>/dev/null)
      if [ -n "$q" ]; then printf '%s\t%s\n' "$head" "$(esc "$q")" >> "$f.norm"
      else printf '%s\n' "$line" >> "$f.norm"; fi
      ;;
    FACT:*)
      # FACT evidence（第 3 字段）同归一（C-Inv09：FACT 纳入引文比对的前置）——其余字段原样保留
      f2=$(printf '%s\n' "$line" | cut -f2); rest=$(printf '%s\n' "$line" | cut -f4-)
      case "$f2" in "$SRC"/*) f2=${f2#"$SRC"/} ;; esac
      fln=${f2##*:}; ffile=${f2%:*}
      case "$fln" in ''|*[!0-9]*) printf '%s\n' "$line" >> "$f.norm"; continue ;; esac
      q=$(awk -v n="$fln" 'NR==n{print; exit}' "$SRC/$ffile" 2>/dev/null)
      if [ -n "$q" ]; then printf '%s\t%s\t%s\t%s\n' "$head" "$f2" "$(esc "$q")" "$rest" >> "$f.norm"
      else printf '%s\n' "$line" >> "$f.norm"; fi
      ;;
    *) printf '%s\n' "$line" >> "$f.norm" ;;
    esac
  done < "$f"
  mv "$f.norm" "$f"
done
```

**3b. 行数对账（派/收对照 + in_flight 消费 + C-Inv08 行数恒等式）**

```bash
. "$S/env.sh"
D=$(wc -l < "$S/tmp/dispatch_list.txt" 2>/dev/null | tr -d ' ')
G=0
for ck in $(cat "$S/tmp/dispatch_list.txt" 2>/dev/null); do
  [ -f "$S/shards/A-$ck.tsv" ] && G=$((G+1))
done
# in_flight 消费对账（2a 的派发记录不再是死产物）：in_flight 计数 vs 派 D vs 收 G——不一致即警告留痕
IF=0; [ -s "$S/audit/in_flight.txt" ] && IF=$(tr ',' '\n' < "$S/audit/in_flight.txt" | grep -c .)
echo "对账: 派 $D / 收 $G / in_flight $IF（缺失卡由 3f attempt 计数处置，不许静默）"
if [ "$IF" -ne "$D" ] || [ "$G" -ne "$D" ]; then
  echo "⚠ in_flight 对账不一致: in_flight=$IF 派=$D 收=$G（2a 记录与实际派发漂移——audit/reconcile.log 留痕）" | tee -a "$S/audit/reconcile.log"
fi
# C-Inv08 分片零丢失（行数恒等式）：本轮各 A 分片逐片行数落账 manifest（审计可复核的行数账本），
# Σ(manifest) == cat 本轮分片合计（cat shards|wc -l 对账）；0 行分片=内容丢失即警告（3f 按 attempt 计费处置）
R=$(cat "$S/audit/round_count" 2>/dev/null || echo 0)
: > "$S/audit/shard-manifest-R${R}.tsv"
SL=0
for ck in $(cat "$S/tmp/dispatch_list.txt" 2>/dev/null); do
  [ -f "$S/shards/A-$ck.tsv" ] || continue
  n=$(wc -l < "$S/shards/A-$ck.tsv" | tr -d ' ')
  printf '%s\t%s\n' "$ck" "$n" >> "$S/audit/shard-manifest-R${R}.tsv"
  [ "$n" -eq 0 ] && echo "⚠ 空分片: A-$ck.tsv 0 行（内容丢失——交 3f 计费）" | tee -a "$S/audit/reconcile.log"
  SL=$((SL+n))
done
echo "行数恒等式: manifest Σ=$SL（audit/shard-manifest-R${R}.tsv；逐片 wc -l 对账 cat 合计）"
printf '3b-lines R%s: 派=%s 收=%s in_flight=%s shardlines=%s\n' "$R" "$D" "$G" "$IF" "$SL" >> "$S/audit/reconcile.log"
```

**3c. 状态迁移（只处理本轮派发的卡；TERM 值白名单过滤）**

```bash
. "$S/env.sh"
# TERM:{state}<TAB>{reason}<TAB>{facts_used}（schema 单源=agents/analyzer.md——D-090：0.0 门投影检查对齐，
# 两处格式串逐字节一致；本块 cut -f1/-f2/-f3 即该三列的解析投影）
for ck in $(cat "$S/tmp/dispatch_list.txt" 2>/dev/null); do
  f="$S/shards/A-$ck.tsv"
  [ -f "$f" ] || continue
  tline=$(grep '^TERM:' "$f" | head -1)
  # 迟到分片防御净化（活会话实证 2026-08-27：子代理在 3a 之后落盘，字面 <TAB> 记法滞留账本——
  # state 列混成 not_applicable<TAB>reason 整段）。与 3a 同一条规则（文档记法→真实制表符），不是新知识；
  # 自创分隔符（如 <帽>）不可枚举——白名单拦下走 3f attempt 路径，audit-live.sh vitals 披露
  tline=${tline//"<TAB>"/$'\t'}
  st=$(printf '%s\n' "$tline" | cut -f1 | sed 's/^TERM://')
  [ -z "$st" ] && continue
  knd=$(awk -F'\t' -v id="$ck" '$1==id{print $2; exit}' "$S/checks.tsv")
  # 终态白名单（封闭枚举外的值当无 TERM 处理，走 3f attempt 路径——两块同口径）
  # deferred = ext 卡专属第七终态（A-059：证据需运行时/带外输入；bw/fw/term 卡禁用——卡顿一律 blocked）
  case "$st" in
    candidate|refuted|not_applicable|no_path|blocked|partial) ;;
    deferred) [ "$knd" = "ext" ] || continue ;;
    *) continue ;;
  esac
  rs=$(printf '%s\n' "$tline" | cut -f2)
  fu=$(printf '%s\n' "$tline" | cut -f3)
  awk -F'\t' -v id="$ck" -v st="$st" -v rs="${rs:-}" -v fu="${fu:-}" \
    'BEGIN{OFS="\t"} $1==id{$5=st; if(rs!="")$6=rs; if(fu!="")$7=fu} {print}' \
    "$S/checks.tsv" > "$S/tmp/ck.tmp" && mv "$S/tmp/ck.tmp" "$S/checks.tsv"
done
```

**3d. 候选落账（统一 cand_id 双命名空间可反推；sink_seq/source_seq 拆存数字——B-190/B-191/B-210/C-Inv14）**

```bash
. "$S/env.sh"
# 表头预建：candidates 九列（B-193 尾列 summary=候选一句话——A 分片 TERM reason 机械重排，盲信封明确排除）；
# joins 六列（A-045/B-195——第七账本件，J2 拼链轮落行；主代理以协议命令合并分片，B-122）
[ -f "$S/candidates.tsv" ] || printf "cand_id\tcard_id\tsink_seq\tsource_seq\tclass_id\tloc\tverdict_state\tdelivery_state\tsummary\n" > "$S/candidates.tsv"
[ -f "$S/joins.tsv" ] || printf "join_id\tegress_ref\tcontract_ref\tingress_ref\tconfidence\tassumptions\n" > "$S/joins.tsv"
# B-042 同轮盲确认清单：本轮新落账候选记 tmp/new_cands.txt（下方同轮 Verifier 派发的机械输入）
: > "$S/tmp/new_cands.txt"
awk -F'\t' 'NR>1 && $5=="candidate"{print $1"\t"$2"\t"$3"\t"$4}' "$S/checks.tsv" | \
while IFS=$'\t' read -r ck kind ref orig; do
  awk -F'\t' -v c="$ck" '$2==c{f=1} END{exit !f}' "$S/candidates.tsv" 2>/dev/null && continue
  num=$(printf '%s' "$ref" | sed 's/[^0-9]//g')
  sq=""; vq=""
  case "$ck" in
    CK-ext-*)
      cls="term"; loc=""
      case "$orig" in
        INV-*)
          # 不变式候选：独立命名空间 CD-INV-{inv_id}-{module}（可由 inv_id×module 反推；
          # module 取 file_inventory.module——ref 尾段即发卡时的 module 域值，
          # 单模块退化（'-' 或空）时用 core，S10 裁决）
          mod=${ref#"$orig"-}; [ "$mod" = "$ref" ] && mod=""
          case "$mod" in ""|"-") mod="core" ;; esac
          cid="CD-INV-${orig#INV-}-${mod}" ;;
        SINK-*)
          cid="CD-$(printf '%05d' $((10#${orig#SINK-})))-00000" ;;
        SRC-*)
          cid="CD-00000-$(printf '%05d' $((10#${orig#SRC-})))" ;;
        *)
          # 锚点不可解析到 sink/source 实体的 ext 卡：CD-X-{origin} 逃逸段（origin=锚点 ID；
          # 设计 v1.4.0-S10 正式化第三命名空间，I14 披露不参与反推，禁静默）
          cid="CD-X-${orig}" ;;
      esac ;;
    *)
    case "$kind" in
      bw)
        cls=$(awk -F'\t' -v r="$ref" '$1==r{print $4}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
        loc=$(awk -F'\t' -v r="$ref" '$1==r{print $3}' "$S/inventories/sink_inventory.tsv" 2>/dev/null)
        sq=$(printf '%05d' $((10#$num))); cid="CD-${sq}-00000" ;;
      fw)
        cls="term"; loc=$(awk -F'\t' -v r="$ref" '$1==r{print $3}' "$S/inventories/source_inventory.tsv" 2>/dev/null)
        vq=$(printf '%05d' $((10#$num))); cid="CD-00000-${vq}" ;;
      *)
        # term 卡候选：第三实体段 file_seq（设计 v1.4.0-S10：term=CD-F-{file_seq}，可由 file_seq 反推）
        cls="term"; loc=$(awk -F'\t' -v r="$ref" '$1==r{print $2}' "$S/inventories/file_inventory.tsv" 2>/dev/null)
        cid="CD-F-${num}" ;;
    esac ;;
  esac
  [ -z "$cls" ] && cls=term
  # cand_id 级去重（同实体多卡只落一行——demand 追踪卡与预发卡撞号时保留首行）
  awk -F'\t' -v c="$cid" '$1==c{f=1} END{exit !f}' "$S/candidates.tsv" 2>/dev/null && continue
  # B-193 summary：A 分片 TERM 行 reason 列机械重排（截 160 字符；空则如实空——盲信封明确排除该列）
  # （radiation-lens 第三处：迟到分片防御净化同规则——否则字面 <TAB> 行 cut -f2 恒空，summary 永久失明）
  summ=$(grep '^TERM:' "$S/shards/A-$ck.tsv" 2>/dev/null | head -1); summ=${summ//"<TAB>"/$'\t'}
  summ=$(printf '%s\n' "$summ" | cut -f2 | cut -c1-160)
  printf "%s\t%s\t%s\t%s\t%s\t%s\topen\tpending\t%s\n" "$cid" "$ck" "${sq:-}" "${vq:-}" "${cls}" "${loc}" "${summ:-}" >> "$S/candidates.tsv"
  echo "$cid" >> "$S/tmp/new_cands.txt"
done
```

**B-042 同轮盲确认（本轮新候选立即验证，不再等次轮 2e）**：对 `$S/tmp/new_cands.txt` 里每个候选，收卡后**当轮**立即派 Verifier——信封构造与派发模板复用 2e（`对每个待验证候选` 的信封块 + 2e 模板，盲性口径不变）；其 V 分片由本轮 5a 消费。Verifier 未写出合法分片时候选保持 open，次轮 2e 按既有重派/降级路径兜底。

**3e. 事实合并（per-FACT 幂等去重 + sort -m 协议合并 + 行数恒等式）+ Confirmer 派发 + retract 翻案传播**

```bash
. "$S/env.sh"
# 获取当前最大事实号（十进制安全；FT-0001 的数字部分从第 4 字符起）
LAST_FT=$(awk -F'\t' '$1~/^FT-/{t=substr($1,4)+0; if(t>m)m=t} END{print m+0}' "$S/facts.tsv" 2>/dev/null)
: "${LAST_FT:=0}"
N=$((10#$LAST_FT))

[ -f "$S/facts.tsv" ] || printf "fact_id\ttype\tloc\tevidence\tevidence_hash\tstatus\tscope_type\tscope_ref\treflection_checked\tused_facts\tconfirmer\trevision\torigin_card\n" > "$S/facts.tsv"
mkdir -p "$S/audit"

# FACT 契约 7 列（type,loc,evidence,scope_type,scope_ref,reflection_checked,used_facts——A-116/B-185）：
# dead/no_edge 必附 reflection_checked；派生事实必附 used_facts（来源 FT-id 逗号串）
# origin_card（B-217 lineage）：FACT 行入账时附产出卡（分片名派生：A-{card}.tsv→{card}、SUM-*→SUM 名）——
# 底层翻案/知识演化时按卡回溯；checks.origin_ref（第 4 列）与 candidates.card_id（第 2 列）为同一语义的既有落位
: > "$S/tmp/ft.raw"
# F2 迟到分片防御净化（review-radiation-lens 列位扫描出的第二消费方）：分片在 3a 之后落盘时，
# FACT 行带字面 <TAB>/绝对路径 loc 裸读入账会列错位，且次轮 3a 归一后同键（loc+evidence）不命中→双行。
# 与 3a FACT 分支同规则同字节：记法→真实制表符｜loc 绝对→相对｜evidence 回读源码行按账本转义形态
# （幂等——已归并行回读出同字节，键稳定不双计）
esc(){ printf '%s' "$1" | awk '{e=$0; gsub(/\\/,"\\\\",e); gsub(/\t/,"\\t",e); print e}'; }
for f in "$S"/shards/A-*.tsv "$S"/shards/SUM-*.tsv; do
  [ -f "$f" ] || continue
  oc=$(basename "$f" .tsv); oc=${oc#A-}
  while IFS= read -r fl; do
    fl=${fl//"<TAB>"/$'\t'}
    f2=$(printf '%s\n' "$fl" | cut -f2); rest=$(printf '%s\n' "$fl" | cut -f4-)
    case "$f2" in "$SRC"/*) f2=${f2#"$SRC"/} ;; esac
    fln=${f2##*:}; ffile=${f2%:*}
    q=""
    case "$fln" in ''|*[!0-9]*) ;; *) q=$(awk -v n="$fln" 'NR==n{print; exit}' "$SRC/$ffile" 2>/dev/null) ;; esac
    if [ -n "$q" ]; then
      printf '%s\t%s\t%s\t%s\t%s\n' "$(printf '%s\n' "$fl" | cut -f1)" "$f2" "$(esc "$q")" "$rest" "$oc" >> "$S/tmp/ft.raw"
    else
      printf '%s\t%s\n' "$fl" "$oc" >> "$S/tmp/ft.raw"
    fi
  done < <(grep '^FACT:' "$f" 2>/dev/null)
done
# per-FACT 幂等去重（D-088）：守卫从 basename 改为同 loc+evidence 去重——重派分片/SUM 换轮号不再双计，
# 被翻案（retracted）的事实也不会因原分片还在 shards/ 而复活（同键仍命中去重集）
awk -F'\t' -v base="$N" 'BEGIN{OFS="\t"}
NR==FNR { if(FNR>1) seen[$3 "\t" $4]=1; next }
/^FACT:/ {
  key=$2 "\t" $3
  if(key in seen) next
  seen[key]=1; n++
  printf "FT-%04d\t%s\t%s\t%s\t-\thint\t%s\t%s\t%s\t%s\tA\tr1\t%s\n", base+n, substr($1,6), $2, $3, $4, $5, $6, $7, $8
}' "$S/facts.tsv" "$S/tmp/ft.raw" > "$S/tmp/ft.new"
# evidence_hash（B-180）：入账时对 evidence 文本计算行内容哈希（前 16 位，按账本转义形态——与 I9 还原比对同字节）
# 整行读+显式切分（与终态 I9 同款形态）：`read c1..c5 rest` 的 IFS-TAB 折叠会吞空 evidence 列
# 致其后数据整体左移（ragged row——空 evidence 事实行状态/作用域列错位）；显式 %%/# 切分保位。
if [ -s "$S/tmp/ft.new" ]; then
  : > "$S/tmp/ft.hashed"
  while IFS= read -r line; do
    rest=$line
    c1=${rest%%$'\t'*}; rest=${rest#*$'\t'}
    c2=${rest%%$'\t'*}; rest=${rest#*$'\t'}
    c3=${rest%%$'\t'*}; rest=${rest#*$'\t'}
    c4=${rest%%$'\t'*}; rest=${rest#*$'\t'}   # c4=evidence（可为空——保位）；第 5 列为 '-' 占位随切分丢弃
    c5=${rest%%$'\t'*}; rest=${rest#*$'\t'}
    h=$(printf '%s' "$c4" | $HASH | cut -c1-16)
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$c1" "$c2" "$c3" "$c4" "$h" "$rest"
  done < "$S/tmp/ft.new" >> "$S/tmp/ft.hashed"
  mv "$S/tmp/ft.hashed" "$S/tmp/ft.new"
fi
# 协议合并形态（C-062）：cat/sort -m 追加账本，禁止逐字粘贴搬运；随后 wc -l 行数恒等式对账（A-134/C-Inv08）
BEFORE=$(wc -l < "$S/facts.tsv" | tr -d ' ')
LC_ALL=C sort -m "$S/tmp/ft.new" >> "$S/facts.tsv"
ADD=$(wc -l < "$S/tmp/ft.new" | tr -d ' ')
AFTER=$(wc -l < "$S/facts.tsv" | tr -d ' ')
echo "3e-merge before=$BEFORE add=$ADD after=$AFTER" >> "$S/audit/facts-merge.log"
if [ "$AFTER" -ne $((BEFORE + ADD)) ]; then
  echo "❌ 行数恒等式破坏: before=$BEFORE + add=$ADD ≠ after=$AFTER（账本损坏——终止）"
  exit 1
fi

# Confirmer 复核结果回写（VERDICT:{state}\t{FT-id}\t{理由}，FT-id 在第 2 列）
# retracted=翻案裁决（A-138）：不得直接改写既有结论性状态，被影响卡一律经下方级联撤销回 unchecked 重走五步
# rt.pre=本轮起点已撤集（先于 CONF 回写快照——陈旧 confirmed 分片会把派生撤销态翻回 confirmed，
# 留痕只记本轮真·新事件，同轮翻转不重复记行）
awk -F'\t' 'NR>1 && $6=="retracted"{print $1}' "$S/facts.tsv" > "$S/tmp/rt.pre"
for cf in "$S"/shards/CONF-*.tsv; do
  [ -f "$cf" ] || continue
  grep '^VERDICT:' "$cf" | while IFS=$'\t' read -r vd fid reason; do
    fid=$(printf '%s' "$fid" | tr -d '[:space:]')
    case "$fid" in FT-*) ;; *) continue ;; esac
    case "$vd" in
      VERDICT:confirmed) nst="confirmed" ;;
      VERDICT:rejected)  nst="rejected" ;;
      VERDICT:retracted) nst="retracted" ;;
      *) continue ;;
    esac
    OLDST=$(awk -F'\t' -v id="$fid" '$1==id{print $6; exit}' "$S/facts.tsv")
    # B-186：confirmed 时回写 confirmer 列（A=Analyzer 顺产 → CONF=独立复核落章；rejected/retracted 不改写出处）
    awk -F'\t' -v id="$fid" -v st="$nst" 'BEGIN{OFS="\t"} $1==id{$6=st; if(st=="confirmed") $11="CONF"} {print}' \
      "$S/facts.tsv" > "$S/tmp/ft.tmp" && mv "$S/tmp/ft.tmp" "$S/facts.tsv"
    # 翻案留痕（A-137）：仅在状态迁移时记一行（幂等——分片每轮都在，重复执行不重复留痕）；
    # retract.log 是撤销通道的单一事实源（step0 的 L1 回升额度也从这里数）
    if [ "$nst" = "retracted" ] && [ "$OLDST" != "retracted" ]; then
      printf 'RETRACT\t%s\t（confirmer 翻案：%s）\n' "$fid" "$reason" >> "$S/audit/retract.log"
    fi
  done
done

# retract 级联撤销（A-135/A-136——级联必须可逆，迭代至不动点）：
#   ① 派生事实（used_facts 引用任一 retracted id）一并 retracted——底层翻案级联撤销派生事实；
#     撤销覆盖陈旧 confirmed 裁决（基事实翻案后派生链即断，CONF 分片每轮重放也复活不了）；
#     基事实重新 confirmed 后派生事实自动随自身裁决恢复（overlay 每轮重算）
#   ② K 关闭卡（reason ^k[0-9] 且 $7 引用被撤 id）→ unchecked、$7 清空、attempt 保留（A-138）
# 列可变白名单（B-216）：facts 只动 $6，checks 只动 $5/$6/$7——loc/evidence 等引文位置列禁改
PASSR=0; CHG=1
while [ "$CHG" -gt 0 ] && [ "$PASSR" -lt 10 ]; do
  PASSR=$((PASSR+1)); CHG=0
  awk -F'\t' 'NR>1 && $6=="retracted"{print $1}' "$S/facts.tsv" > "$S/tmp/rt.ret"
  awk -F'\t' -v lf="$S/audit/retract.log" -v cf="$S/tmp/rt1.chg" 'BEGIN{OFS="\t"}
    FILENAME==ARGV[1] { pre[$1]=1; next }
    FILENAME==ARGV[2] { ret[$1]=1; next }
    FNR>1 && $6!="retracted" && $10!="" {
      m=split($10,u,",")
      for(i=1;i<=m;i++) if(u[i] in ret) {
        $6="retracted"; ch++
        if(!($1 in pre)) print "RETRACT-DERIVED\t"$1"\tuses\t"u[i] >> lf
        break
      }
    }
    { print }
    END { print ch+0 > cf }' "$S/tmp/rt.pre" "$S/tmp/rt.ret" "$S/facts.tsv" > "$S/tmp/ft.tmp" && mv "$S/tmp/ft.tmp" "$S/facts.tsv"
  awk -F'\t' -v lf="$S/audit/retract.log" -v cf="$S/tmp/rt2.chg" 'BEGIN{OFS="\t"}
    NR==FNR { if(FNR>1 && $6=="retracted") ret[$1]=1; next }
    FNR>1 && $6~/^k[0-9]/ && $7!="" {
      m=split($7,fu,",")
      for(i=1;i<=m;i++) if(fu[i] in ret) {
        print "RETRACT-RESET\t"$1"\tuses\t"fu[i] >> lf; ch++
        $5="unchecked"; $6="fact-retracted:"fu[i]; $7=""
        break
      }
    }
    { print }
    END { print ch+0 > cf }' "$S/facts.tsv" "$S/checks.tsv" > "$S/tmp/ck.tmp" && mv "$S/tmp/ck.tmp" "$S/checks.tsv"
  CHG=$(( $(cat "$S/tmp/rt1.chg" 2>/dev/null || echo 0) + $(cat "$S/tmp/rt2.chg" 2>/dev/null || echo 0) ))
done

# Confirmer 派发清单（status=hint 且未有 CONF 分片——status 在第 6 列；rejected/retracted 不再派）
awk -F'\t' '$6=="hint"{print $1"\t"$3}' "$S/facts.tsv" | while IFS=$'\t' read -r fid floc; do
  [ -f "$S/shards/CONF-$fid.tsv" ] && continue
  echo "$fid"
done > "$S/tmp/to_confirm.txt"
cat "$S/tmp/to_confirm.txt"
```

对清单里每条事实派一个 Confirmer 子代理（{FT-id} 用实际值；信封机械构造）：

```bash
. "$S/env.sh"
FT={FT-id}
awk -F'\t' -v id="$FT" '$1==id{print "复核事实："id"｜type="$2"｜loc="$3"｜scope="$7" "$8"｜reflection_checked="$9; exit}' "$S/facts.tsv"
# 信封对齐（任务9.1）：scope=entry_family 时机械附 family 全成员清单行（confirmer.md 复核单第 2 项
# 「逐成员核对 guards 五段」的机械输入——白名单承诺落地，非行为规则）
SROW=$(awk -F'\t' -v id="$FT" '$1==id{print $7"\t"$8; exit}' "$S/facts.tsv")
if [ "$(printf '%s' "$SROW" | cut -f1)" = "entry_family" ]; then
  awk -F'\t' -v fam="$(printf '%s' "$SROW" | cut -f2)" 'NR>1 && $8==fam{print "成员："$1"｜loc="$3"｜auth="$6"｜guards="$7}' "$S/inventories/source_inventory.tsv" 2>/dev/null
fi
```

```
你是 GenSift Confirmer。读取 {SK}/agents/confirmer.md 并严格遵守。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）。
完成后只返回一行。
——以上固定前缀（A-107）——
{上方信封行}｜完整 evidence 行读 {S}/facts.tsv 中该行。family 成员清单行如上（作用域项逐成员核对的机械输入）。
真读源码逐项复核。写分片到 {S}/shards/CONF-{FT-id}.tsv，格式：
OBS:{file}:{line}<TAB>{你实测的原文}
VERDICT:confirmed|rejected|retracted<TAB>{FT-id}<TAB>{理由}
```

**3f. attempt 计数（分片缺失 / 无 TERM / TERM 非法 同等计费——与 3c 白名单同口径）**

```bash
. "$S/env.sh"
R=$(cat "$S/audit/round_count" 2>/dev/null || echo 0)
for ck in $(cat "$S/tmp/dispatch_list.txt" 2>/dev/null); do
  f="$S/shards/A-$ck.tsv"
  reason=""
  [ -f "$f" ] || reason="分片缺失"
  if [ -z "$reason" ]; then
    # （radiation-lens 第三处：迟到分片防御净化同规则——否则 3c 已迁移的卡在此被按"TERM非法"计费，
    # att≥2 时还会把已迁移终态翻成 partial，正确分析被毁）
    tline=$(grep '^TERM:' "$f" | head -1); tline=${tline//"<TAB>"/$'\t'}
    st=$(printf '%s\n' "$tline" | cut -f1 | sed 's/^TERM://')
    knd=$(awk -F'\t' -v id="$ck" '$1==id{print $2; exit}' "$S/checks.tsv")
    okst=""
    case "$st" in
      candidate|refuted|not_applicable|no_path|blocked|partial) okst=1 ;;
      deferred) [ "$knd" = "ext" ] && okst=1 ;;   # ext 专属（A-059）——与 3c 同口径
    esac
    if [ -z "$okst" ]; then
      if [ -z "$st" ]; then reason="分片无TERM行"; else reason="TERM非法($st)"; fi
    fi
  fi
  if [ -n "$reason" ]; then
    # B-075 失败原因账本：逐卡逐轮留痕，2b 重派信封从这里注入"上次派发失败原因"
    printf '%s\t%s\tR%s\n' "$ck" "$reason" "$R" >> "$S/audit/attempt-failures.log"
    awk -F'\t' -v id="$ck" 'BEGIN{OFS="\t"} $1==id{$8=$8+1} {print}' \
      "$S/checks.tsv" > "$S/tmp/ck.tmp" && mv "$S/tmp/ck.tmp" "$S/checks.tsv"
    att=$(awk -F'\t' -v id="$ck" '$1==id{print $8}' "$S/checks.tsv")
    if [ "$att" -ge 2 ]; then
      awk -F'\t' -v id="$ck" -v rs="两次派发失败($reason)" 'BEGIN{OFS="\t"} $1==id{$5="partial";$6=rs} {print}' \
        "$S/checks.tsv" > "$S/tmp/ck.tmp" && mv "$S/tmp/ck.tmp" "$S/checks.tsv"
    fi
  fi
done
```

**3g. 复核收卡（B-020 对称反转）——REVIEW:reversed 走翻案通道，upheld 原状维持**

```bash
. "$S/env.sh"
# REVIEW:reversed → 卡重置 unchecked 重走五步（L1 回升额度走 retract.log 的 RETRACT-RESET 行——单一事实源，任务 4 通道复用）；
# 已交付 refuted 的候选：verdict_state 回 open 且 delivery_state 回 pending（S8 两列——重走验证）；
# 旧 finding 的 mf 行**保留不删、lifecycle=withdrawn**（S9：verdict 验证裁决不改写，翻案只动生命周期列），
# finding 文件移 audit/reversed-*（留痕不蒸发），陈旧 V 分片一并移 audit/reversed-V-*
# （否则当轮 5a 用它重建同一 refuted finding 把翻案抵消；且 2e 见分片已有 VERDICT 直接跳过重派）。
# 重派路径=候选 open+pending + shards/ 无 V 分片 → 2e 下轮正常派发（非本块职责）。
# REVIEW:upheld → 原状维持只留痕。REVIEW 缺失/非法 → 不记已处理、分片原地留存（该卡抽样名额已耗，
# 已抽样>已复核差值由终态 coverage 披露——无自动重派通道，不虚设）。
# 每卡只处理一次（reversal-reviewed.tsv 幂等记账——分片常驻 shards/，重放不重复翻案）
[ -f "$S/audit/reversal-reviewed.tsv" ] || printf 'card_id\tverdict\n' > "$S/audit/reversal-reviewed.tsv"
for rf in "$S"/shards/RV-*.tsv; do
  [ -f "$rf" ] || continue
  card=$(basename "$rf" .tsv); card=${card#RV-}
  awk -F'\t' -v c="$card" '$1==c{f=1} END{exit !f}' "$S/audit/reversal-reviewed.tsv" && continue
  rline=$(grep '^REVIEW:' "$rf" | head -1)
  rv=$(printf '%s\n' "$rline" | cut -f1 | sed 's/^REVIEW://')
  case "$rv" in reversed|upheld) ;; *) continue ;; esac
  reason=$(printf '%s\n' "$rline" | cut -f2)
  printf '%s\t%s\n' "$card" "$rv" >> "$S/audit/reversal-reviewed.tsv"
  echo "REVERSAL $rv $card（$reason）" >> "$S/audit/reversal-review.log"
  if [ "$rv" = "reversed" ]; then
    printf 'RETRACT-RESET\t%s\t（对称反转复核翻案：卡重走五步——%s）\n' "$card" "$reason" >> "$S/audit/retract.log"
    awk -F'\t' -v id="$card" 'BEGIN{OFS="\t"} $1==id{$5="unchecked";$6="reversal-review";$7=""} {print}' \
      "$S/checks.tsv" > "$S/tmp/ck.tmp" && mv "$S/tmp/ck.tmp" "$S/checks.tsv"
    cand=$(awk -F'\t' -v c="$card" '$2==c{print $1; exit}' "$S/candidates.tsv" 2>/dev/null)
    if [ -n "$cand" ]; then
      awk -F'\t' -v c="$cand" 'BEGIN{OFS="\t"} $1==c{$7="open";$8="pending"} {print}' \
        "$S/candidates.tsv" > "$S/tmp/cd.tmp" 2>/dev/null && mv "$S/tmp/cd.tmp" "$S/candidates.tsv"
      # 陈旧 V 分片先撤（5a/2e 同批消费此状态——顺序：分片撤→mf 行标 withdrawn→finding 文件撤）
      [ -f "$S/shards/V-$cand.tsv" ] && mv "$S/shards/V-$cand.tsv" "$S/audit/reversed-V-$cand.tsv"
      cls=$(awk -F'\t' -v c="$cand" '$1==c{print $5; exit}' "$S/candidates.tsv" 2>/dev/null)
      # C-001：与 5a 同一机械派生（loc → basename+行号；空退化）——两处必须逐字节同式
      loc3=$(awk -F'\t' -v c="$cand" '$1==c{print $6; exit}' "$S/candidates.tsv" 2>/dev/null)
      fex=""
      if [ -n "$loc3" ]; then
        fb=$(basename "${loc3%:*}"); fb=${fb%.*}
        case "${loc3##*:}" in ''|*[!0-9]*) fex="-${fb}" ;; *) fex="-${fb}-L${loc3##*:}" ;; esac
      fi
      fid="F-$cand-$cls$fex"
      if [ -f "$S/machine-fields.tsv" ] && awk -F'\t' -v f="$fid" '$1==f && $13==""{x=1} END{exit !x}' "$S/machine-fields.tsv"; then
        awk -F'\t' -v f="$fid" 'BEGIN{OFS="\t"} $1==f && $13==""{$13="withdrawn"} {print}' \
          "$S/machine-fields.tsv" > "$S/tmp/mf.tmp" && mv "$S/tmp/mf.tmp" "$S/machine-fields.tsv"
        # 撤档唯一：同 fid 多轮翻案再撤档时递增序号（首撤用基名，再撤 -2/-3…——防同名覆盖丢留痕）
        if [ -f "$S/findings/$fid.md" ]; then
          arc="$S/audit/reversed-$fid.md"; k=1
          while [ -f "$arc" ]; do k=$((k+1)); arc="$S/audit/reversed-$fid-$k.md"; done
          mv "$S/findings/$fid.md" "$arc"
          # 勘误节只追加不删除（A-140/B-018/C-003：原文不可改写；mf/report 投影随 5b/终态重算——永不永久不一致）
          { echo ""; echo "## 勘误（errata——只追加，原文未改写）"
            echo "- $(date '+%F %T') lifecycle=withdrawn（对称反转复核翻案：${reason}）——撤档留痕不蒸发，身份永续；重验证再交付走新行"
          } >> "$arc"
        fi
        echo "REVERSED-FINDING $fid lifecycle=withdrawn 撤至 audit/（复核翻案——待重验证再交付）" >> "$S/audit/coverage-degraded.log"
      fi
    fi
  fi
done
echo "3g 复核收卡: 已处理 $(awk 'END{print NR-1}' "$S/audit/reversal-reviewed.tsv" 2>/dev/null || echo 0) 张（reversed $(awk -F'\t' '$2=="reversed"{n++} END{print n+0}' "$S/audit/reversal-reviewed.tsv" 2>/dev/null)）"
```

### step4 级联（K 规则——只关 band2 卡；S4 级联引擎 K1/K1b/K2/K3/K4）

```bash
. "$S/env.sh"
# 机械匹配只认 facts 的 scope_type/scope_ref 两列（A-114）——事实 loc 只是证据出处，作用域以声明为准；
# 只有 scope_type=file 参与 K 级联（entry_id/entry_family 窄作用域不机械放大到全文件——过量剪枝防线）
# 剪枝事实必须 confirmed（C-Inv07：hint/rejected/retracted 一律不剪）；每消一卡 $7 回写实际消费的 FT-id 串（A-129）
# 列可变白名单（B-216）：只写 $5/$6/$7，attempt/$8 与卡身份列禁改
# K1  uncontrolled → refuted（必经且不可控=实报路径关闭）
# K1b intended     → not_applicable（设计内行为）
# K2  kills        → blocked，reason 记 at:file:line（A-063：净化存在，不引入新状态词，留恢复入口）
# K3  no_edge      → no_path
# K4  dead         → no_path（文件级消卡；reflection_checked 非空才许——grep 级"无调用方"不构成 dead，A-116）
krun(){ # $1=type $2=终态 $3=reason 前缀 $4=1 则附 at:loc $5=1 则要求 reflection_checked 非空
  awk -F'\t' -v ty="$1" -v st="$2" -v pfx="$3" -v atloc="$4" -v needrc="$5" '
FILENAME==ARGV[1] { if($2==ty && $6=="confirmed" && $7=="file" && (needrc!="1" || $9!="")) { f=$8; fids[f]=fids[f] (fids[f]?",":"") $1; if(atloc=="1") floc[f]=$3 } next }
FILENAME==ARGV[2] { if(FNR>1) { band[$1]=$6; split($3,bf,":"); sinkfile[$1]=bf[1] } next }
FNR>1 && $5=="unchecked" && $2=="bw" {
  ref=$3
  bd=(ref in band)?band[ref]:1
  sf=(ref in sinkfile)?sinkfile[ref]:""
  if(bd==2 && sf!="" && (sf in fids)) {
    rs=pfx; if(atloc=="1") rs=rs " at:" floc[sf]
    print $1 "\t" st "\t" rs "\t" fids[sf]
  }
}' "$S/facts.tsv" "$S/inventories/sink_inventory.tsv" "$S/checks.tsv" 2>/dev/null | \
while IFS=$'\t' read -r ck st reason fu; do
  awk -F'\t' -v id="$ck" -v st="$st" -v rs="$reason" -v fu="$fu" 'BEGIN{OFS="\t"} $1==id{$5=st;$6=rs;$7=fu} {print}' \
    "$S/checks.tsv" > "$S/tmp/ck.tmp" && mv "$S/tmp/ck.tmp" "$S/checks.tsv"
done
}
krun uncontrolled refuted        "k1:uncontrolled" 0 0
krun intended     not_applicable "k1b:intended"    0 0
krun kills        blocked        "k2:kills"        1 0
krun no_edge      no_path        "k3:no_edge"      0 0
krun dead         no_path        "k4:dead"         0 1
```

### step5 投影（不可跳过）

**5a. 处理 Verifier 结果 → finding 文件 + machine-fields + 回写卡状态**

```bash
. "$S/env.sh"
# VERDICT:{三态|dismissed}<TAB>{severity}<TAB>{cvss}<TAB>{tier}（schema 单源=agents/verifier.md——D-090：
# 0.0 门投影检查对齐；本块 cut -f1..-f4（+可选 5/6/7）即该格式的解析投影）
R=$(cat "$S/audit/round_count" 2>/dev/null || echo 0)
# B-204 pattern_version 随行落：与 G3 run-state 同式聚合哈希（两处必须同式——C-001 纪律；pattern 文件头
# 已带 # version: 行，聚合内容随头变化自动分版）
PV=$(cat "$SK"/classes/patterns/*.pattern 2>/dev/null | $HASH | cut -c1-16); : "${PV:=absent}"
[ -f "$S/machine-fields.tsv" ] || printf "finding_id\tfingerprint\tverdict\tseverity\tclass\tsink\tsource\ttier\talso-reported-by\tpattern_version\tknown_disclosed\thuman_triage\tlifecycle\tsuite\n" > "$S/machine-fields.tsv"
for vf in "$S"/shards/V-*.tsv; do
  [ -f "$vf" ] || continue
  # 解析 VERDICT 行（格式：VERDICT:{state}\t{severity}\t{cvss}\t{tier}）
  vline=$(grep '^VERDICT:' "$vf" | head -1)
  verdict=$(printf '%s\n' "$vline" | cut -f1 | sed 's/^VERDICT://')
  if [ -z "$vline" ] || { [ "$verdict" != "confirmed" ] && [ "$verdict" != "unconfirmed" ] && [ "$verdict" != "refuted" ] && [ "$verdict" != "dismissed" ]; }; then
    # V 分片存在但 VERDICT 缺失/非法：降级留痕，不静默蒸发
    cand_id=$(basename "$vf" .tsv); cand_id=${cand_id#V-}
    mv "$vf" "$S/audit/degraded-$(basename "$vf")"
    echo "DEGRADED-V ${cand_id} VERDICT缺失或非法" >> "$S/audit/coverage-degraded.log"
    awk -F'\t' -v c="$cand_id" 'BEGIN{OFS="\t"} $1==c{$8="degraded"} {print}' \
      "$S/candidates.tsv" > "$S/tmp/cd.tmp" 2>/dev/null && mv "$S/tmp/cd.tmp" "$S/candidates.tsv"
    continue
  fi
  sev=$(printf '%s\n' "$vline" | cut -f2)
  cvss=$(printf '%s\n' "$vline" | cut -f3)
  tier=$(printf '%s\n' "$vline" | cut -f4)
  # VERDICT 可选第 5/6 字段（5.3/D-111）：known_disclosed=yes（既往披露未修复——照常裁但标注）；
  # deferred-evidence-gap（有界邻接扫描无果——缺口不是反证）。缺省空=未标（4 字段旧分片兼容）
  kd=$(printf '%s\n' "$vline" | cut -f5); [ "$kd" = "yes" ] || kd=""
  gap=$(printf '%s\n' "$vline" | cut -f6)
  # C-044 可选第 7 字段：disp:{fingerprint}:{处置值}——dismissed 裁决引用的处置 ID（信封 DISP 行同键）
  dsp=$(printf '%s\n' "$vline" | cut -f7)
  cand_id=$(basename "$vf" .tsv); cand_id=${cand_id#V-}
  sink=$(awk -F'\t' -v c="$cand_id" '$1==c{print $3}' "$S/candidates.tsv" 2>/dev/null)
  srcq=$(awk -F'\t' -v c="$cand_id" '$1==c{print $4}' "$S/candidates.tsv" 2>/dev/null)
  loc=$(awk -F'\t' -v c="$cand_id" '$1==c{print $6}' "$S/candidates.tsv" 2>/dev/null)
  cls=$(awk -F'\t' -v c="$cand_id" '$1==c{print $5}' "$S/candidates.tsv" 2>/dev/null)
  [ -z "$cls" ] && cls="term"
  card=$(awk -F'\t' -v c="$cand_id" '$1==c{print $2}' "$S/candidates.tsv" 2>/dev/null)
  [ -n "$card" ] || card="unknown"
  # B-033/A-012：reasoning-only 类（类页面首部标 "> oracle: none" 的无 oracle 逻辑类）→ human triage 位
  HT=""
  grep -q '^> oracle: none' "$SK/classes/$cls.md" 2>/dev/null && HT="yes"
  # C-001 文件名定稿：F-{cand_id}-{class_id}-{basename}-L{行号}——全取不可变列（loc 机械派生；
  # loc 空或无行号时退化不加分段——G3 机械层逐字节稳定，severity 故意不进名）
  lfile=${loc%:*}; lline=${loc##*:}
  fex=""
  if [ -n "$loc" ]; then
    fb=$(basename "$lfile"); fb=${fb%.*}
    case "$lline" in ''|*[!0-9]*) fex="-${fb}" ;; *) fex="-${fb}-L${lline}" ;; esac
  fi
  fid="F-${cand_id}-${cls}${fex}"
  # 已交付去重：整字段相等（前缀 grep 会把 CD-00001-0000 误判为 CD-00001-00001 已交付、
  # CD-X-{origin} 同前缀锚点互吞——finding 静默丢失）；
  # 只查在役行（lifecycle 空）——withdrawn/superseded 行是历史留痕，翻案/吸收后重验证须允许再交付（S9）
  awk -F'\t' -v fid="$fid" '$1==fid && $13==""{f=1} END{exit !f}' "$S/machine-fields.tsv" 2>/dev/null && continue
  # 稳定指纹 = path + 行内容哈希 + class_id（B-197/B-211——不含行号：位置平移不换 ID；行号只用于取行内容）
  case "$lline" in
    ''|*[!0-9]*) q="" ;;
    *) q=$(awk -v n="$lline" 'NR==n{print; exit}' "$SRC/$lfile" 2>/dev/null) ;;
  esac
  fp=$( { printf '%s\n%s\n%s\n' "$lfile" "$q" "$cls"; } | $HASH | cut -c1-16)
  # 处置 join（§10.2 两层分离——B-028/C-044/C-045/C-046：投影层标注，verdict 列不动）
  # 抑制/标注型 → finding 头部标注（含到期日；已过期待复核=降级 hint，C-043）；
  # fixed 型 → 同指纹复现 = 回归 NOTICE 留痕（audit/disposition-notice.log——C-046，G3 双跑口径同判）
  DNOTE=""; FIXHIT=""
  for df in "$SK"/feedback/dispositions.tsv "$S"/feedback/dispositions.tsv; do
    [ -f "$df" ] || continue
    [ -z "$DNOTE" ] && DNOTE=$(awk -F'\t' -v fp="$fp" -v cls="$cls" -v today="$(date +%F)" 'NR>1 && $1==fp{
        split($4,sc,"|"); if(sc[1]!="" && sc[1]!=cls) next
        print $2 (($7!="" && $7<today)?"（已过期待复核）":"（到期 "$7"）"); exit }' "$df")
    [ -z "$FIXHIT" ] && awk -F'\t' -v fp="$fp" 'NR>1 && $1==fp && $2=="fixed"{f=1} END{exit !f}' "$df" && FIXHIT=1
  done
  [ -n "$FIXHIT" ] && printf 'NOTICE-REGRESSION\t%s\t%s\t%s\n' "$fid" "$fp" "$(date '+%F %T')" >> "$S/audit/disposition-notice.log"
  [ -n "$DNOTE" ] && printf 'NOTICE-ANNOTATED\t%s\t%s\t%s\n' "$fid" "$fp" "$DNOTE" >> "$S/audit/disposition-notice.log"
  fname="${fid}.md"
  # B-201/B-230（与 sink 列对偶）：mf.sink=sink 侧位置（bw 候选=loc；fw/term/INV 无 sink 侧=空如实）；
  # mf.source=source_seq 引用（原值——fw 候选为真实源；bw 候选补 00000 哨兵=与 cand_id 源段一致，
  # 不再用 loc 占位；INV/F/X 命名空间无源段=空如实）
  sinkpos=""
  [ -n "$sink" ] && sinkpos="$loc"
  case "$cand_id" in
    CD-[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9]) [ -n "$srcq" ] || srcq="00000" ;;
  esac
  # B-024/B-203：canonical 落行时回填 also-reported-by（merge.log 单一事实源——合并先于验证发生的路径）
  arb=""
  [ -f "$S/audit/merge.log" ] && arb=$(awk -F'\t' -v c="$cand_id" '$1=="MERGED" && $4==c{a=a (a?",":"") $2} END{print a}' "$S/audit/merge.log")
  # 骨架：证据全部内联（禁止"见分片"——finding 必须自包含）
  {
    echo "# ${cls} ｜ ${sev}"
    echo ""
    echo "severity: ${sev} ｜ CVSS: ${cvss} ｜ tier: ${tier} ｜ verdict: ${verdict}"
    echo "sink: ${sink} ｜ location: ${loc}"
    echo "card: ${card} ｜ shards: A-${card}.tsv + $(basename "$vf")"
    if [ "$kd" = "yes" ]; then echo "known-disclosed: yes（既往披露未修复——照常报告，B-034 标注）"; fi
    if [ -n "$gap" ]; then echo "deferred-evidence-gap: ${gap}（有界邻接扫描无果——缺口不是反证，D-111）"; fi
    if [ "$HT" = "yes" ]; then echo "oracle: none ｜ reasoning-only ｜ human triage: required（本类无机械/执行 oracle——最终裁决显式交人工，A-012/B-033）"; fi
    if [ -n "$DNOTE" ]; then echo "disposition: ${DNOTE}（§10.2 两层分离——处置标注，verdict 不因此改写）"; fi
    if [ -n "$FIXHIT" ]; then echo "regression-NOTICE: fixed 处置同指纹复现——回归检测（C-046，audit/disposition-notice.log）"; fi
    case "$dsp" in disp:*) echo "dismissed-cite: ${dsp#disp:}（抑制型复核成立——Verifier 裁决 dismissed 引用处置 ID，C-044）";; esac
    echo ""
    echo "## 1 概述"
    echo "<!--REPORTER-->"
    echo ""
    echo "## 2 证据链（机械投影，禁止删改）"
    echo ""
    echo "### Analyzer 观察（A-${card}.tsv）"
    if [ -f "$S/shards/A-${card}.tsv" ] && grep -q '^OBS:' "$S/shards/A-${card}.tsv"; then
      grep -E '^(OBS|ROLE):' "$S/shards/A-${card}.tsv" | sed 's/^/    /'
    else
      echo "    （无 OBS 行）"
    fi
    echo ""
    echo "### Analyzer 事实（A-${card}.tsv）"
    if [ -f "$S/shards/A-${card}.tsv" ] && grep -q '^FACT:' "$S/shards/A-${card}.tsv"; then
      grep '^FACT:' "$S/shards/A-${card}.tsv" | sed 's/^/    /'
    else
      echo "    （无 FACT 行）"
    fi
    echo ""
    echo "### Verifier 独立观察（$(basename "$vf")）"
    if grep -q '^SELF:' "$vf"; then
      grep '^SELF:' "$vf" | sed 's/^/    /'
    else
      echo "    （无 SELF 行）"
    fi
    echo ""
    echo "### Verifier 判定基线（$(basename "$vf")）"
    if grep -q '^RUBRIC:' "$vf"; then
      grep '^RUBRIC:' "$vf" | sed 's/^/    /'
    else
      echo "    （无 RUBRIC 行）"
    fi
    echo ""
    echo "### 终判"
    echo "    ${vline}"
    echo ""
    echo "## 3 净化分析"
    echo "<!--REPORTER-->"
    echo ""
    echo "## 4 利用前提"
    echo "<!--REPORTER-->"
    echo ""
    echo "## 5 PoC（tier: ${tier}）"
    echo "<!--REPORTER-->"
    echo ""
    echo "## 6 定级"
    echo "severity: ${sev} ｜ CVSS: ${cvss} ｜ tier: ${tier}（Verifier 终判，机械字段）"
    echo "<!--REPORTER-->"
    echo ""
    echo "## 7 根因修复（含验收用例）"
    echo "<!--REPORTER-->"
    echo ""
    echo "## 8 同类横向"
    echo "<!--REPORTER-->"
    echo ""
    echo "## 9 参考"
    echo "<!--REPORTER-->"
  } > "$S/findings/$fname"
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t\t%s\n" "$fid" "$fp" "$verdict" "$sev" "$cls" "$sinkpos" "$srcq" "$tier" "$arb" "$PV" "$kd" "$HT" "default" >> "$S/machine-fields.tsv"

  # 回写：仅 refuted/dismissed 是卡级终态写回 checks（封闭枚举不含 verified）；
  # confirmed/unconfirmed 的卡保持 candidate——verdict 归 machine-fields（判定与状态分离）
  if [ -n "$card" ] && { [ "$verdict" = "refuted" ] || [ "$verdict" = "dismissed" ]; }; then
    [ "$verdict" = "refuted" ] && new_st="refuted" || new_st="not_applicable"
    awk -F'\t' -v id="$card" -v st="$new_st" 'BEGIN{OFS="\t"} $1==id{$5=st;$6="verifier:"$6} {print}' \
      "$S/checks.tsv" > "$S/tmp/ck.tmp" && mv "$S/tmp/ck.tmp" "$S/checks.tsv"
  fi
  awk -F'\t' -v c="$cand_id" 'BEGIN{OFS="\t"} $1==c{$8="delivered"} {print}' \
    "$S/candidates.tsv" > "$S/tmp/cd.tmp" && mv "$S/tmp/cd.tmp" "$S/candidates.tsv"
done
# B-024/B-203 回填有两处：本块落行时（上方 arb——合并先于验证的常态路径）与 2d-consume 的
# canonical 已交付回写（跨轮时序）；merge.log 始终是吸收记账的单一事实源（C-Inv06 对账消费）
touch "$S/audit/mark-5a-R${R}"
```

**5b. live_findings_index.md 刷新（五节结构：第 0 节审计脉搏 + severity 降序发现表 / open 候选表 / 近期活动 / NOTICE——B-046/C-021/D2）**

```bash
. "$S/env.sh"
R=$(cat "$S/audit/round_count" 2>/dev/null || echo 0)
# 指纹留痕（Plateau 数据源——B-074/D-087）：machine-fields 内容 sha + 行数，每轮一条
MFSHA=$(tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | $HASH | cut -c1-16)
MFCNT=$(tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | wc -l | tr -d ' ')
printf 'R%s\t%s\t%s\n' "$R" "${MFSHA:-empty}" "${MFCNT:-0}" >> "$S/audit/mf-fp.log"
# 处置列预计算（C-047 live 处置列——§10.2 两层分离：join 投影，verdict 列不动；
# 双库=全局 $SK/feedback + 本 run $S/feedback；到期行显示"已过期待复核"——C-043 降级 hint）
: > "$S/tmp/disp-live.tsv"
for df in "$SK"/feedback/dispositions.tsv "$S"/feedback/dispositions.tsv; do
  [ -f "$df" ] || continue
  awk -F'\t' -v today="$(date +%F)" 'NR>1 && $1!=""{
    ex=($7!="" && $7<today)?"已过期待复核":$7
    printf "%s\t%s@%s\n",$1,$2,ex }' "$df" >> "$S/tmp/disp-live.tsv"
done
# D2 审计脉搏（P6）：live index 第 0 节纯机械投影——零发现轮次也回答"它在干什么、为什么没有发现"。
# 五要素：①闭合数 ②状态分布 ③交付面占比（P1 test 污染持续可见=E1 派单交付面占比的日常版：近 3 轮派单
# 的 bw 卡中非 test/demo 角色文件占比）④最接近 candidate 的卡（最近 3 张 reason 摘录；零候选时如实披露
# 最近闭合卡=为什么没有发现）⑤ETA+token 累计（轮数×宽度×子代理量级——0.8 同参数 90–900s/20k–80k）
P_T=$(awk -F'\t' 'NR>1' "$S/checks.tsv" | wc -l | tr -d ' ')
P_D=$(awk -F'\t' 'NR>1 && $5!="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
P_S=$(awk -F'\t' 'NR>1 && $5!="unchecked"{c[$5]++} END{printf "candidate=%d refuted=%d not_applicable=%d no_path=%d blocked=%d partial=%d deferred=%d", c["candidate"]+0,c["refuted"]+0,c["not_applicable"]+0,c["no_path"]+0,c["blocked"]+0,c["partial"]+0,c["deferred"]+0}' "$S/checks.tsv")
P_DISP=$(awk -F'\t' '
  FILENAME==ARGV[1] { if(FNR>1){ split($3,b,":"); sf[$1]=b[1]; kd[$1]=$2 } next }
  FILENAME==ARGV[2] { if(FNR>1 && ($6=="test"||$6=="demo")) td[$2]=1; next }
  { n=split($2,a,","); for(i=1;i<=n;i++){ c=a[i]; if(c in sf && kd[c]=="bw"){ tot++; if(!(sf[c] in td)) del++ } } }
  END{ printf "%d\t%d", del+0, tot+0 }' "$S/checks.tsv" "$S/inventories/file_inventory.tsv" <(tail -3 "$S/audit/dispatch-history.log" 2>/dev/null))
P_DEL=$(printf '%s' "$P_DISP" | cut -f1); P_TOT=$(printf '%s' "$P_DISP" | cut -f2)
P_PCT=0; [ "$P_TOT" -gt 0 ] && P_PCT=$((P_DEL * 100 / P_TOT))
P_ALLT=$(awk -F'\t' 'FILENAME==ARGV[1]{ if(FNR>1){ split($3,b,":"); sf[$1]=b[1] } next }
  FILENAME==ARGV[2]{ if(FNR>1 && ($6=="test"||$6=="demo")) td[$2]=1; next }
  FILENAME==ARGV[3]{ if(FNR>1 && $2=="bw" && ($3 in sf) && (sf[$3] in td)) n++ }
  END{ print n+0 }' "$S/inventories/sink_inventory.tsv" "$S/inventories/file_inventory.tsv" "$S/checks.tsv")
P_C=$(awk -F'\t' '$5=="candidate"{print $1"｜"$2"｜"substr($6,1,60)}' "$S/checks.tsv" | tail -3)
P_CH="最近 candidate 卡（card｜kind｜reason 摘录）"
if [ -z "$P_C" ]; then
  P_C=$(awk -F'\t' 'NR>1 && $5!="unchecked"{print $1"｜"$2"｜"$5"｜"substr($6,1,60)}' "$S/checks.tsv" | tail -3)
  P_CH="当前零 candidate——最近闭合卡（为什么没有发现：状态+原因摘录）"
fi
P_W="${WIDTH:-4}"; case "$P_W" in ''|*[!0-9]*|0) P_W=4 ;; esac
P_EST=$(sed -n 's/^- 预计轮次: \([0-9]*\).*/\1/p' "$S/run-estimate.md" 2>/dev/null | head -1)
[ -n "$P_EST" ] || P_EST=$(( (P_T + P_W - 1) / P_W ))
P_REM=$((P_EST - R)); [ "$P_REM" -lt 0 ] && P_REM=0
P_TKLO=$((R * P_W * 20)); P_TKHI=$((R * (P_W + 3) * 80))
P_ETALO=$((P_REM * 90 / 60)); P_ETAHI=$((P_REM * 900 / 60))
{ echo "# Live Findings"
  echo ""
  echo "## 0 审计脉搏（R$R 快照——机械投影：零发现时也回答在干什么/为什么没有）"
  echo "- 闭合: $P_D/$P_T 卡｜状态分布: $P_S"
  echo "- 交付面占比: 近3轮派单 $P_DEL/$P_TOT = $P_PCT%（test/demo 污染 $((P_TOT-P_DEL)) 张在队尾——D4-A；全账本 bw 卡 test/demo $P_ALLT 张）"
  echo "- 最接近 candidate: $P_CH"
  if [ -n "$P_C" ]; then printf '%s\n' "$P_C" | sed 's/^/  - /'; else echo "  - （尚无闭合卡）"; fi
  echo "- ETA: 剩余 ≈$P_REM 轮 × 90–900s ≈ $P_ETALO–$P_ETAHI 分钟｜token 累计 ≈ ${R}轮 × $P_W–$((P_W+3)) 子代理 × 20k–80k ≈ ${P_TKLO}k–${P_TKHI}k（0.8 同参数量级）"
  echo ""
  echo "## 1 当前发现（severity 降序——在役行）"
  echo "| id | severity | class | sink | verdict | disposition | 详情 |"
  echo "|---|---|---|---|---|---|---|"
  tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | \
    awk -F'\t' 'BEGIN{r["critical"]=5;r["high"]=4;r["medium"]=3;r["low"]=2;r["info"]=1}$13==""{print r[$4]+0"\t"$0}' | \
    LC_ALL=C sort -t$'\t' -k1,1rn | cut -f2- | \
    awk -F'\t' 'FILENAME==ARGV[1]{d[$1]=$2; next} {printf "| %s | %s | %s | %s | %s | %s | [打开](findings/%s.md) |\n",$1,$4,$5,$6,$3,(($2 in d)?d[$2]:"—"),$1}' "$S/tmp/disp-live.tsv" -
  WD=$(tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$13=="withdrawn"' | wc -l | tr -d ' ')
  [ "$WD" -gt 0 ] && echo "（已翻案撤销 ${WD} 条——lifecycle=withdrawn：mf 行留痕、文件撤 audit/reversed-*；不混入上表）"
  echo ""
  echo "## 2 open 候选（待验证投影——B-046；delivery_state=pending）"
  echo "| cand | card | class | loc | delivery |"
  echo "|---|---|---|---|---|"
  awk -F'\t' 'NR>1 && $8=="pending"{printf "| %s | %s | %s | %s | pending |\n",$1,$2,$5,$6}' "$S/candidates.tsv" 2>/dev/null
  echo "（空=当前无待验证候选；G1 种子行保持 open 属显式披露态）"
  echo ""
  echo "## 3 近期活动（近 3 轮派发尾巴——dispatch-history）"
  tail -3 "$S/audit/dispatch-history.log" 2>/dev/null || echo "（无派发记录）"
  echo ""
  echo "## 4 NOTICE（plateau/卡顿/降级机械状态行——C-020/C-021）"
  if [ -f "$S/audit/stall.log" ]; then echo "- ⚠ 卡顿换道在案: $(tail -1 "$S/audit/stall.log")"; else echo "- 卡顿: 无记录"; fi
  if [ -f "$S/audit/plateau.flag" ]; then echo "- ⚠ Plateau 强制停轮: $(cat "$S/audit/plateau.flag")"; else echo "- Plateau: 无"; fi
  NDG=$(grep -c . "$S/audit/coverage-degraded.log" 2>/dev/null); : "${NDG:=0}"
  echo "- 降级记录: ${NDG} 行（audit/coverage-degraded.log）"
  if [ -f "$S/audit/disposition-notice.log" ]; then
    NRG=$(grep -c '^NOTICE-REGRESSION' "$S/audit/disposition-notice.log" 2>/dev/null); : "${NRG:=0}"   # 守卫形态：grep -c 零命中 rc=1 时 || echo 0 会双写 "0\n0"（任务11 终审B P2，与 NDG 同式）
    NAN_=$(grep -c '^NOTICE-ANNOTATED' "$S/audit/disposition-notice.log" 2>/dev/null); : "${NAN_:=0}"
    echo "- ⚠ 处置 NOTICE: 回归 ${NRG} 条（fixed 同指纹复现——C-046）/ 标注 ${NAN_} 条（audit/disposition-notice.log）"
  fi
  echo ""
  TOTAL_CARDS=$(awk -F'\t' 'NR>1' "$S/checks.tsv" | wc -l | tr -d ' ')
  DONE=$(awk -F'\t' 'NR>1 && $5!="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
  CONFIRMED=$(tail -n +2 "$S/machine-fields.tsv" 2>/dev/null | awk -F'\t' '$3=="confirmed"' | wc -l | tr -d ' ')
  echo "进度: ${DONE}/${TOTAL_CARDS} ｜ confirmed: ${CONFIRMED}"
} > "$S/live_findings_index.md"
touch "$S/audit/mark-5b-R${R}"
```

**5c. progress_board.md 追加（无守卫——每执行一次=记账一轮；宿主层重试会产生幻影行，是诚实的重试痕迹；step0 的修复路径要求完整重跑 step5，四 mark 会对齐到当前轮号，一轮即收敛）**

```bash
. "$S/env.sh"
ROUND=$(cat "$S/audit/round_count" 2>/dev/null || echo 0)
ROUND=$((ROUND+1)); echo $ROUND > "$S/audit/round_count"
R=$ROUND
[ -f "$S/tmp/dispatch_list.txt" ] && D=$(wc -l < "$S/tmp/dispatch_list.txt" | tr -d ' ') || D=0
C=$(awk -F'\t' 'NR>1 && $5=="candidate"' "$S/checks.tsv" | wc -l | tr -d ' ')
CL=$(awk -F'\t' 'NR>1 && $5!="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
RM=$(awk -F'\t' 'NR>1 && $5=="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
if [ ! -f "$S/progress_board.md" ]; then
  printf '| 轮次 | 派卡 | 候选 | 闭合 | 剩余 |\n|---|---|---|---|---|\n' > "$S/progress_board.md"
fi
echo "| R$ROUND | $D | $C | $CL | $RM |" >> "$S/progress_board.md"
# NOTICE 行（C-020 W2：机械阈值触发，零 LLM 判断）——慢于预估 / 卡顿 / 级联撤销
EST_R=$(sed -n 's/^- 预计轮次: \([0-9]*\).*/\1/p' "$S/run-estimate.md" 2>/dev/null | head -1)
RT_NOW=$(grep -c '^RETRACT' "$S/audit/retract.log" 2>/dev/null); : "${RT_NOW:=0}"
{ if [ -n "$EST_R" ] && [ "$ROUND" -gt $((EST_R * 2)) ]; then
    echo "| NOTICE | R$ROUND | 慢于预估：已 $ROUND 轮 > 预估 ${EST_R}×2（run-estimate.md 口径） |  |  |"
  fi
  [ -f "$S/tmp/stall_lane" ] && echo "| NOTICE | R$ROUND | L3 卡顿换道生效（audit/stall.log——B-060/B-072） |  |  |"
  RT_PREV=$(cat "$S/audit/last_retract_notify" 2>/dev/null || echo 0)
  if [ "$RT_NOW" -gt "$RT_PREV" ]; then
    echo "| NOTICE | R$ROUND | 级联撤销发生：retract.log 本轮 +$((RT_NOW-RT_PREV)) 行（翻案级联——A-135） |  |  |"
  fi
} >> "$S/progress_board.md"
echo "$RT_NOW" > "$S/audit/last_retract_notify"
touch "$S/audit/mark-5c-R$((ROUND-1))"
```

**5d. Reporter 扩写 finding（派发 + 格式门）**

先枚举待扩写清单（含占位符即待扩写）：

```bash
. "$S/env.sh"
grep -l '<!--REPORTER-->' "$S"/findings/F-*.md 2>/dev/null > "$S/tmp/to_report.txt" || true
cat "$S/tmp/to_report.txt" 2>/dev/null
```

对清单里每个 finding（{fname} 为文件名）派一个 Reporter 子代理（可写通用子代理，同消息并行；固定前缀+尾部变量块——A-107）：

```
你是 GenSift Reporter。读取 {SK}/agents/reporter.md 并严格遵守。
禁止调用 skill/Skill 工具加载任何技能（含 gensift）。
只返回一行：finding 路径。
——以上固定前缀（A-107）——
任务：把 {S}/findings/{fname} 从骨架扩写为完整九节 finding，写回原文件。
硬规则：
- 第 2 节「证据链」是机械投影：一个字不许改、不许删、不许增
- 每个 <!--REPORTER--> 占位符替换为该节正文；证据引文只能取自第 2 节已有行
- 不引入骨架外新事实；不改 severity/verdict/tier
- secrets-crypto 类：任何 ≥32 位连续字母数字串一律掩码（AKIA****AB3F 式），原文以 file:line 指针交付
- 骨架头部含「oracle: none ｜ reasoning-only ｜ human triage」标注行的（无 oracle 逻辑类，machine-fields human_triage=yes）：第 9 节「参考」末尾加一行「reasoning-only 结论——待人工 triage 最终裁决（A-012）」，骨架标注行本身不删不改
- 类判据与修复参考：读 {SK}/classes/{cls}.md（第 10 节是修复方向）
- 完成后文件内不得残留任何 <!--REPORTER--> 标记
```

子代理返回后立即跑格式门：

```bash
. "$S/env.sh"
for f in "$S"/findings/F-*.md; do
  [ -f "$f" ] || continue
  ok=1
  grep -q '<!--REPORTER-->' "$f" 2>/dev/null && ok=0                       # 残留占位符=未扩写完
  grep -qE '见分片|见 V-|见 A-|见类页面' "$f" && ok=0                      # 禁止踢皮球
  grep -qE ':[0-9]+' "$f" || ok=0                                          # 必须有 file:line 引证
  [ "$(grep -c '^## ' "$f")" -ge 9 ] || ok=0                               # 九节齐
  # 类名从 machine-fields join 取（文件名里的 cand_id 形态多样，不可靠）
  cls=$(awk -F'\t' -v fid="$(basename "$f" .md)" '$1==fid{print $5; exit}' "$S/machine-fields.tsv" 2>/dev/null)
  if [ "$cls" = "secrets-crypto" ]; then
    # 掩码门只查第 3 节起（第 2 节证据链是机械投影禁改，源码原文必然含长串）
    if sed -n '/^## 3 /,$p' "$f" | grep -qE '[A-Za-z0-9+/]{32,}'; then ok=0; fi
  fi
  line="GATE-$([ "$ok" = "1" ] && echo PASS || echo FAIL) $(basename "$f")"
  grep -qxF "$line" "$S/audit/reporter-gate.md" 2>/dev/null || echo "$line" >> "$S/audit/reporter-gate.md"
done
# mark 用自增前的轮号（与 5a/5b/5c 的 R-1 口径一致）
touch "$S/audit/mark-5d-R$(( $(cat "$S/audit/round_count" 2>/dev/null || echo 0) - 1 ))"
```

GATE-FAIL 处置：同轮对该文件重派一次 Reporter；重派后仍 FAIL → 保留骨架交付（第 2 节证据已内联，是诚实的降级形态），在 `$S/audit/reporter-gate.md` 追加 `GATE-DEGRADED {fname}`。**不许因门失败而丢弃 finding 或跳过 5d mark。**

### step6 完成判定

```bash
. "$S/env.sh"
U=$(awk -F'\t' 'NR>1 && $2!="ext" && $5=="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
UE=$(awk -F'\t' 'NR>1 && $2=="ext" && $5=="unchecked"' "$S/checks.tsv" | wc -l | tr -d ' ')
UED=$(awk -F'\t' 'NR>1 && $2=="ext" && $5=="deferred"' "$S/checks.tsv" | wc -l | tr -d ' ')
echo "unchecked=$U（另有 ext 未闭合 $UE ｜ ext deferred $UED）"
# F3 交付物自洽：continue.log 是终态清单成员——零收口 run 也预建空账本件（touch 幂等，空文件=零收口如实），
# 「少任何一件=未完成」不再自相矛盾
touch "$S/audit/continue.log"
# D-086 partial≠blocked 二分阈值：partial=质量缺口（attempt 失败的合法披露态），
# blocked=有恢复入口的合法阻断态（K2 kills）——只有缺口占实体数 >10% 才阻断下游（全闭合宣称）；
# ≤10% 视为质量缺口如实披露不阻断。下游=完成判定/EXIT_CODE=2 口径（terminal 同判据）
TOT=$(awk -F'\t' 'NR>1 && $2!="ext"' "$S/checks.tsv" | wc -l | tr -d ' ')
PAR=$(awk -F'\t' 'NR>1 && $2!="ext" && $5=="partial"' "$S/checks.tsv" | wc -l | tr -d ' ')
PCT=0; [ "$TOT" -gt 0 ] && PCT=$((PAR * 100 / TOT))
if [ "$U" -gt 0 ] || [ "$UE" -gt 0 ]; then
  # Plateau（B-074，D-087 放宽口径）：machine-fields 指纹 3 轮集合不变 或 4 轮数量非递增，
  # 且轮数>2 且卡顿在案（last3 3 轮不降——缺口在缩就不算停滞，渐进收敛留窗口）→ 强制停轮如实报告
  RCUR=$(cat "$S/audit/round_count" 2>/dev/null || echo 0)
  PLAT=0; PM=""
  # STALLED 判读与 step0 同口径：3 轮全相等且值 >0（CUR=0,0,0 是分母已清，不是卡顿）
  STALLED=0
  if [ -f "$S/audit/last3.txt" ] && [ "$(wc -l < "$S/audit/last3.txt" | tr -d ' ')" -eq 3 ] \
     && [ "$(LC_ALL=C sort -u "$S/audit/last3.txt" | wc -l | tr -d ' ')" -eq 1 ] \
     && [ "$(head -1 "$S/audit/last3.txt" | tr -d ' ')" -gt 0 ]; then STALLED=1; fi
  if [ "$RCUR" -gt 2 ] && [ "$STALLED" -eq 1 ] && [ -f "$S/audit/mf-fp.log" ]; then
    MFL=$(wc -l < "$S/audit/mf-fp.log" | tr -d ' ')
    # 长度门（N3）：记录 ≥3 条才判"3 轮集合不变"（2 条相同不构成 3 轮）；≥4 条才判数量口径
    S3=$(tail -3 "$S/audit/mf-fp.log" | cut -f2 | LC_ALL=C sort -u | wc -l | tr -d ' ')
    if [ "$MFL" -ge 3 ] && [ "$S3" -eq 1 ]; then PLAT=1; PM="返工缺口集合 3 轮不变"; fi
    if [ "$PLAT" -eq 0 ] && [ "$MFL" -ge 4 ]; then
      NINCR=$(tail -4 "$S/audit/mf-fp.log" | cut -f3 | awk 'NR==1{p=$1;next} $1>p{bad=1} END{print bad+0}')
      if [ "$NINCR" = "0" ]; then PLAT=1; PM="返工缺口数量 4 轮非递增"; fi
    fi
  fi
  if [ "$PLAT" -eq 1 ]; then
    echo "⚠ Plateau 强制停轮（$PM，R$RCUR——B-074/D-087）：返工缺口停滞，不再回 step0"
    echo "R$RCUR $PM（mf 指纹见 audit/mf-fp.log）——强制停轮，剩余未闭合如实披露" > "$S/audit/plateau.flag"
    echo "→ 跳过 L2，直接【终态】（phases/terminal.md）——coverage 披露 plateau，EXIT_CODE=2 口径"
  else
    # D1-L3 批轮（P5 防自停）：每回合连续 N 轮再收口——收口≠总结，固定输出一行 GENSIFT-CONTINUE 续跑指令
    # （末行=续跑锚点：用户或宿主自动续跑机制把该行原样发回即续跑下一批；N 经发起参数 batch=N 与 width 同法
    #  贯通 env.sh，缺省 3；回合终结白名单见 SKILL.md 循环纪律卡第 9 条——中途总结=禁止，无总结步骤位）
    : "${BATCH:=3}"; case "$BATCH" in ''|*[!0-9]*|0) BATCH=3 ;; esac
    # 每轮只计一次（宿主层重试 step6 不重复计——与 5a-5d mark 同一幂等原则）：
    # batch_last_round 记上次计数的轮号，同轮重跑只读不增
    LASTBR=$(cat "$S/audit/batch_last_round" 2>/dev/null); LASTBR=${LASTBR:--1}
    BR=$(cat "$S/audit/batch_rounds" 2>/dev/null); BR=${BR:-0}
    if [ "$LASTBR" != "$RCUR" ]; then
      echo "$RCUR" > "$S/audit/batch_last_round"
      BR=$((BR+1)); echo "$BR" > "$S/audit/batch_rounds"
    fi
    if [ "$BR" -ge "$BATCH" ]; then
      echo 0 > "$S/audit/batch_rounds"
      K=$(awk -F'\t' '$3=="confirmed"' "$S/machine-fields.tsv" 2>/dev/null | wc -l | tr -d ' ')
      # F1：剩余计数含 ext（M=分母+ext 剩余总数，ext 计数括号披露）——ext-only 场景不再显示"剩余 0 卡"误导
      CLINE="GENSIFT-CONTINUE: 剩余 $((U + UE)) 卡(含 ext $UE)｜已 confirmed $K｜会话 $S"
      printf 'R%s\t%s\n' "$RCUR" "$CLINE" >> "$S/audit/continue.log"
      echo "→ 批轮收口（本回合已连跑 $BATCH 轮）：本轮序列到此让出回合——禁止总结，续跑=把最后一行原样发回"
      echo "$CLINE"
    else
      echo "→ 回到 step0（直接继续下一轮——批轮 $BR/$BATCH，不总结不收口；回合终结白名单见 SKILL.md 循环纪律卡）"
    fi
  fi
else
  [ "$UED" -gt 0 ] && echo "⚠ 完成(有披露)：ext deferred=$UED 待带外证据——coverage 披露，不许谎称全绿"
  if [ "$PCT" -gt 10 ]; then
    echo "⚠ D-086 质量缺口超阈值：partial $PAR/$TOT = ${PCT}% > 10%——不许宣称全闭合（coverage 披露，EXIT_CODE=2 口径）"
  else
    [ "$PAR" -gt 0 ] && echo "D-086 质量缺口披露：partial $PAR/$TOT = ${PCT}%（≤10% 不阻断，coverage 如实披露）"
  fi
  echo "→ L1 完成，进【L2 发散】"
fi
```
