# 宿主对账命令片段库（协议内声明，非自研代码）

> 定位：本文件登记检测协议中所有"确定性对账"所用的宿主命令，作为协议文本的统一引用来源。这些命令由宿主执行，GenSource 不实现任何产品代码。
> v0.3.9 平台双轨：每条机械命令给出 POSIX 权威形式与 PowerShell 翻译件（Windows 宿主）；两者语义由黄金夹具自检钉死（见 §0）。
> 原则：对账常数一律从冻结清单动态推导，禁止硬编码数字。

## 0. 平台前置与金标自检（v0.3.9）

1. **执行环境声明**：宿主在能力档案声明对账执行环境二选一——POSIX shell（bash+coreutils）或 PowerShell 5.1+；未声明 → 阶段0 blocked。
2. **金标自检前置**：任何宿主执行 Gate-1 之前，必须先以契约随附黄金夹具自检（`gate-1.py --session contracts/gate-selftest/fixture --source contracts/gate-selftest/fixture-src --expect contracts/gate-selftest/expected-gate.txt`），输出 SELFTEST: PASS 才可对真实 session 开跑；否则该环境判 blocked。
3. **机器产物七规约**（双平台字节级一致的前提）：UTF-8 无 BOM；换行恒为 LF（解析对 CRLF 透明）；路径一律相对 source root 正斜杠；排序一律 UTF-8 字节序（等价 LC_ALL=C）；时间戳 UTC ISO 8601；确定性 ID 的 hash 输入规范化为「file:line:sink_type」正斜杠形式；解析容忍行首尾空白与 CR。
4. **会话内引用一律相对 session_dir**，盘符/绝对路径不得进入任何机器产物。
4b. **临时文件一律写入 {session_dir}/.tmp/**（v0.7.2 跨平台铁律）：禁用系统 temp 目录（/tmp 在 Windows 不存在、$env:TEMP 在部分容器只读）——所有对账临时文件先 `mkdir -p {session_dir}/.tmp`（POSIX）或 `New-Item -ItemType Directory -Force {session_dir}/.tmp`（PowerShell）再写入。
5. **命令分级**：A 类判定关键（§4/§4b/§4c/§6/§7/§7a/§8）必须双轨且夹具钉死；B 类流程必需（§1/§2/§3/§5/§7c/§9）双轨示例、输出入机器产物时须双平台等价；C 类探索性（SKILL.md 中的阅读命令）标注任选、不入机器产物。**注**：§4/§4b/§7a 的 bash 历史参考形式已被跨平台 python 脚本取代（gate-1.py 承担 §4 对账、derive_checkpoints.py 承担 §4b 机械闭合），PowerShell 翻译件不再补充。

## 1. 文件全量枚举（阶段0，环1）——B 类

POSIX：
```bash
cd {project_path} && find . -type f -not -path './.git/*' | sed 's|^./||' | LC_ALL=C sort > {session_dir}/file_inventory.tsv
total=$(wc -l < {session_dir}/file_inventory.tsv)
```
PowerShell 翻译件（输出须与 POSIX 等价：相对路径正斜杠 + 字节序排序）：
```powershell
Set-Location {project_path}
Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch '\.git\\' } | ForEach-Object { $_.FullName.Substring((Get-Location).Path.Length + 1).Replace('\','/') } | Sort-Object { [System.Text.Encoding]::UTF8.GetBytes($_) -join ',' } | Set-Content -Encoding UTF8 {session_dir}/file_inventory.tsv
```

## 2. sink 双轨模式全扫（阶段0，环2）——B 类

按 knowledge/sinks/_index.md 的每类跨语言 grep 模式逐类执行（信号级类不入 sink_inventory，见 sinks/_index.md 信号分级）：

POSIX：
```bash
cd {project_path} && grep -rnE '{sink 类模式}' --include='*' . | LC_ALL=C sort > {session_dir}/logs/sinks_{type}.log
# 0 命中时写头标：echo "ZERO_HITS_WARRANT_REVIEW" > sinks_{type}.log
```
PowerShell 翻译件：
```powershell
Get-ChildItem -Recurse -File | Select-String -Pattern '{sink 类模式}' | ForEach-Object { "$($_.Path):$($_.LineNumber):$($_.Line)" } | Sort-Object { [System.Text.Encoding]::UTF8.GetBytes($_) -join ',' } | Set-Content -Encoding UTF8 {session_dir}/logs/sinks_{type}.log
```

## 3. 入口通道全扫——B 类

13 通道逐通道执行，同上（POSIX/PS 双轨）；0 命中写 ZERO_HITS_WARRANT_REVIEW 头标。

## 4. 对账等式（Gate-1 逐条执行，A 类；E1-E16 历史最小集，实际以 gate-1.py 全方程为准；完整形式见 §4c 一体块）

本节给出每条等式的可独立执行形式（调试用）；正式判定只认 §4c 一体块输出。

```bash
# E1 planned==terminal：未检查行数必须为 0
awk -F'\t' '$6=="未检查" {n++} END {print n+0}' {session_dir}/check_point_ledger.tsv
# E2/E3 sink/source 覆盖（join -v 2）
join -v 2 <(awk -F'\t' 'NR>1 && $2=="backward" {print $1}' {session_dir}/check_point_ledger.tsv | sort -u) <(tail -n +2 {session_dir}/sink_inventory.tsv | cut -f1 | sort -u) | wc -l   # 必须为 0
join -v 2 <(awk -F'\t' 'NR>1 && $2=="forward" {print $1}' {session_dir}/check_point_ledger.tsv | sort -u) <(tail -n +2 {session_dir}/source_inventory.tsv | cut -f1 | sort -u) | wc -l   # 必须为 0
# E4 audit 双向覆盖（audit_log.tsv 的 backward 行 basis_id 与 sink_inventory 双向差集均为空）
join -v 2 <(awk -F'\t' 'NR>1 && $3=="backward" {print $2}' {session_dir}/audit_log.tsv | sort -u) <(tail -n +2 {session_dir}/sink_inventory.tsv | cut -f1 | sort -u) | wc -l   # 缺 audit 的 sink 数，必须 0
join -v 1 <(awk -F'\t' 'NR>1 && $3=="backward" {print $2}' {session_dir}/audit_log.tsv | sort -u) <(tail -n +2 {session_dir}/sink_inventory.tsv | cut -f1 | sort -u) | wc -l   # 未知 basis 的 audit 行数，必须 0
# E5 四相等（E5b/E5c 按列名取列，python3 单行为权威，禁 jq）
ls {session_dir}/findings/V*.md | wc -l
python3 -c 'import json;print(len(json.load(open("{session_dir}/findings/machine-fields.json"))))'
python3 -c 'import csv;r=csv.reader(open("{session_dir}/candidates.tsv"),delimiter="\t");h=next(r);i=h.index("verdict");print(sum(1 for x in r if x[i]=="confirmed"))'
grep -cE '\[查看\]\(findings/V[0-9]+\.md\)' {session_dir}/report.md
# E6 failed 清单去真空（文件必须存在；行数==blocked 行数；blocked basis_id 全部登记）
wc -l < {session_dir}/failed_wus.txt
awk -F'\t' 'NR>1 && $6=="blocked" {n++} END {print n+0}' {session_dir}/check_point_ledger.tsv
join -v 1 <(awk -F'\t' 'NR>1 && $6=="blocked" {print $1}' {session_dir}/check_point_ledger.tsv | sort -u) <(sort -u {session_dir}/failed_wus.txt) | wc -l   # 未登记的 blocked basis_id，必须 0
# E7 账本零残留
grep -c '未检查' {session_dir}/check_point_ledger.tsv   # 必须为 0
# E8 反伪闭合（not_applicable 理由合法性，backward/forward）
awk -F'\t' 'NR>1 && ($2=="backward"||$2=="forward") && $6=="not_applicable" && $7 !~ /^false_rule_hit:|^disproved_safe:|^cluster_conclusion:/ {n++} END {print n+0}' {session_dir}/check_point_ledger.tsv   # 必须为 0
# E9 簇产物存在
ls {session_dir}/clusters/*.md | wc -l   # 必须 > 0
# E10 全终态理由封闭：disproved 须 cluster_conclusion:/disproved_safe:/false_rule_hit:；blocked 须 budget:/user_decision:/permission:
awk -F'\t' 'NR>1 && ($2=="backward"||$2=="forward") && $6=="disproved" && $7 !~ /^(cluster_conclusion:|disproved_safe:|false_rule_hit:)/ {n++} END {print n+0}' {session_dir}/check_point_ledger.tsv
awk -F'\t' 'NR>1 && $6=="blocked" && $7 !~ /^(budget:|user_decision:|permission:)/ {n++} END {print n+0}' {session_dir}/check_point_ledger.tsv
# E11 候选 ID 反查（python3：sink_seq/source_seq 反查冻结清单排序位置 + sig8 复核）
python3 - <<'PYEOF'
import csv,hashlib,sys
S='{session_dir}'
def rows(f):
    r=list(csv.reader(open(S+'/'+f),delimiter='\t'))
    h=r[0];return h,[x for x in r[1:] if x]
h,cs=rows('candidates.tsv')
def col(h,name):return h.index(name)
hsi,sinks=rows('sink_inventory.tsv');hso,srcs=rows('source_inventory.tsv')
sinks=sorted(sinks,key=lambda x:int(x[col(hsi,'sort_order')]))
srcs=sorted(srcs,key=lambda x:int(x[col(hso,'sort_order')]))
bad=0
for c in cs:
    cid=c[col(h,'candidate_id')];loc=c[col(h,'location')];st=c[col(h,'sink_type')]
    p=cid.split('-')
    if len(p)!=4 or p[0]!='C':bad+=1;continue
    sseq,sseq2,sig=p[1],p[2],p[3]
    ok_loc=False
    if 1<=int(sseq)<=len(sinks) and sinks[int(sseq)-1][col(hsi,'file:line')]==loc:ok_loc=True
    if 1<=int(sseq2)<=len(srcs) and srcs[int(sseq2)-1][col(hso,'file:line')]==loc:ok_loc=True
    if not ok_loc:bad+=1;continue
    f,l=loc.rsplit(':',1)
    want=hashlib.md5((f+':'+l+':'+st).encode()).hexdigest()[:8]
    want2=hashlib.md5((f+':'+l).encode()).hexdigest()[:8]
    if sig not in (want,want2):bad+=1
print(bad)
PYEOF
# E12 产物存在性（v0.11.1 与 gate-1.py 一致：audit_log.tsv / verification-summary.md / failed_wus.txt / findings/machine-fields.json / candidates.tsv / check_point_ledger.tsv / report.md / knowledge_graph/{nodes,edges}.json + clusters/*.md>0；machine-coverage.tsv 已废弃）
# E13 信号级禁入：sink_inventory 不得含信号级 7 类
grep -cE 'SINK-(SENSITIVE-EXPOSE|LOGGING-INSUFF|AUTHN-BYPASS|BRUTE-FORCE|OBSERVABLE-DIFF|STATE-CONCURRENT|MEM-INDEX)' {session_dir}/sink_inventory.tsv   # 必须为 0
# E14 引用闭包（verification-summary 锚点⊆candidates；confirmed 三 ref 非空；V*.md id==machine-fields id）——完整实现见 §4c 一体块
# E16 对抗表存在（每个 clusters/*.md 必须含「## 攻击模式对抗表」标题）
for f in {session_dir}/clusters/*.md; do grep -q '^## 攻击模式对抗表' "$f" || echo MISSING:$f; done | wc -l   # 必须为 0
```

## 4b. 文件终态机械闭合（v0.3.6，预筛规则第1/2类，不经过 LLM）——A 类（执行形式已由 derive_checkpoints.py 承担，本节 bash 为历史参考）

```bash
# 1) binary_flag=binary 或 type 为 image/binary 且无 sink 命中 → not_applicable（prefilter_no_exec:）
# 2) type 为 doc（纯文档）且无 sink 命中且无入口特征 → not_applicable（prefilter_no_exec:）
# 3) 其余文件 → 深扫（LLM），不得机械闭合
cut -f2 {session_dir}/sink_inventory.tsv | sed 's/:[0-9]*$//' | sort -u > {session_dir}/.tmp/files_with_sinks
cut -f2 {session_dir}/source_inventory.tsv | sed 's/:[0-9]*$//' | sort -u > {session_dir}/.tmp/files_with_entries
awk -F'\t' -v OFS='\t' '
  FNR==1 { f++ }
  f==1 && FNR==1 { next }
  f==1 { ftype[$1]=$2; fbin[$1]=$5; next }
  f==2 { hassink[$1]=1; next }
  f==3 { hasentry[$1]=1; next }
  f==4 && FNR==1 { print; next }
  f==4 && $2=="terminal" && ($1 in ftype) && !($1 in hassink) && !($1 in hasentry) && (fbin[$1]=="binary" || ftype[$1]=="image" || ftype[$1]=="binary" || ftype[$1]=="doc") {
    tag = (fbin[$1]=="binary" || ftype[$1]=="image" || ftype[$1]=="binary") ? "binary" : ftype[$1];
    $6="not_applicable"; $7="prefilter_no_exec:" tag ":0命中证据"
  }
  f==4 { print }
' {session_dir}/file_inventory.tsv {session_dir}/.tmp/files_with_sinks {session_dir}/.tmp/files_with_entries {session_dir}/check_point_ledger.tsv > {session_dir}/check_point_ledger.tsv.tmp \
  && mv {session_dir}/check_point_ledger.tsv.tmp {session_dir}/check_point_ledger.tsv
awk -F'\t' 'NR>1 && $2=="terminal" && $6=="未检查" {n++} END {print "剩余未检查 terminal 行数:" n+0}' {session_dir}/check_point_ledger.tsv
```
PowerShell 等价：Move-Item -Force 原子替换（若文件被编辑器占用则失败，需先关闭句柄）；逻辑与上逐条对应。

## 4c. Gate-1 对账（v0.4.0：宿主工具 gate-1.py，禁止 LLM 执行或手写判定栏）

```bash
# 宿主在会话结束后执行（POSIX 或 PowerShell 的 python3 均可）：
python3 {skill_dir}/contracts/gate-1.py --session {session_dir} --source {project_path}
# 自检前置（能力档案阶段）：以黄金夹具自检，输出必须 SELFTEST: PASS
python3 {skill_dir}/contracts/gate-1.py --session {skill_dir}/contracts/gate-selftest/fixture --source {skill_dir}/contracts/gate-selftest/fixture-src --expect {skill_dir}/contracts/gate-selftest/expected-gate.txt
```

- 产出 gate_record.md（24 项对账 + gate_result），判定由脚本输出生成，**LLM 禁止创建/编辑 gate_record、禁止自报 gate_result、禁止在报告里自绘对账表**；
- 任何 FAIL → 按 gate 生命周期 rework 后重跑覆盖更新；宿主重放 diff 不一致 → 整跑作废（铁律 #4）；
- 原 POSIX/PowerShell 命令块自 v0.4.0 起降级为历史参考（git 历史可见），不再作为执行形式。
- v0.10.1：gate 每次跑自动重投影 knowledge_graph/{nodes,edges}.json（图=账本投影，自愈）+ E56-E59 四方程（图节点投影完整性/图边投影完整性/图投影确定性/图边端点存在）。

## 4d. 图投影（v0.10.1 doc 99：账本=真相，图=投影）——A 类

```bash
# 图由脚本投影维护（LLM 禁止手写图）；独立重投影与对账：
python3 {skill_dir}/contracts/build_graph.py --session {session_dir}
# 校验图文件与账本投影一致（E58 的独立形式，不一致 exit 1）：
python3 {skill_dir}/contracts/build_graph.py --check --session {session_dir}
```

- `knowledge_graph/nodes.json`（6 类节点：sink/source/file/checkpoint/candidate/finding，id 带类型前缀）+ `edges.json`（3 类边：flow/basis/derived）；
- 剪枝/扫雷在图状态上可见：类级剪枝 → 节点 status=pruned + pruned_by/pruned_reason；flow 边 direction 随 WU 翻转；`graph_snapshot.tsv` 每批追加 graph_nodes/graph_edges 计数；
- schema 权威 `data-structures/knowledge-graph.md`；边端点存在性由 gate E59 机械校验（悬空边=FAIL）。

## 5. 分片串行合并（三铁律）——B 类（历史参考——WU 分片现行唯一 schema 为 batches/B{NNN}/WU-NNNN.tsv（5 列 TSV））

```bash
ls {session_dir}/batches/B*/shard.json | wc -l   # 合并前 count 临时文件数 == 批数
python3 -c 'import json,glob,sys; d={}; [d.update(json.load(open(f))) for f in sorted(glob.glob("{session_dir}/batches/B*/shard.json"))]; json.dump(d, open("{session_dir}/merged.json","w"))'
```
PowerShell：ConvertFrom-Json/ConvertTo-Json 合并，键冲突语义与上一致。

## 6. 确定性 ID 派生（sig8）——A 类

```bash
# 常规：单 source + 单 sink 命中
python3 -c 'import hashlib,sys; print(hashlib.md5(sys.argv[1].encode()).hexdigest()[:8])' "{file}:{line}:{sink_type}"
# fallback：无 sink 候选（业务逻辑/横向差异）——省略 sink_type
python3 -c 'import hashlib,sys; print(hashlib.md5(sys.argv[1].encode()).hexdigest()[:8])' "{file}:{line}"
```
PowerShell 等价：[System.BitConverter]::ToString([System.Security.Cryptography.MD5]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes('{file}:{line}:{sink_type}'))).Replace('-','').Substring(0,8).ToLower()

派生规则（与 data-structures/candidate-finding.md 一致）：多 source/多 sink 取冻结清单 UTF-8 字节序排序序号最小者；无 sink 候选的 sink_seq 取该文件终态检查点排序序。

## 7. run_fingerprint——A 类

```bash
# 机器字段核心 6 字段（candidate_id/location/sink_type/severity/root_cause_group_id/verdict）排序后哈希；新增字段（confidence/evidence_grade/runtime_tier）不入 fingerprint（保持跨版本可比）
python3 -c 'import json,hashlib; d=json.load(open("{session_dir}/findings/machine-fields.json")); core=[{k:x[k] for k in ("candidate_id","location","sink_type","severity","root_cause_group_id","verdict")} for x in d]; core.sort(key=lambda x:x["candidate_id"].encode()); print(hashlib.sha256(json.dumps(core,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:16])'
```
PowerShell 等价：ConvertTo-Json -Compress 后 SHA256（System.Security.Cryptography.SHA256），字段与排序键同上。

## 7a. 五层闭合命令（L2 簇覆盖 + L3 验证覆盖）——A 类（gate-1.py 已承担，本段 bash 为历史参考）

```bash
ls {session_dir}/clusters/*.md | wc -l   # L2 必须 > 0
awk -F'\t' 'NR>1 && ($2=="backward"||$2=="forward") && $6=="not_applicable" && $7 !~ /^false_rule_hit:|^disproved_safe:|^cluster_conclusion:/ {n++} END {print n+0}' {session_dir}/check_point_ledger.tsv   # L2 反伪闭合，必须 0
cut -f5 {session_dir}/check_point_ledger.tsv | tr ';' '\n' | grep -v '^$' | sort -u > {session_dir}/.tmp/set_ledger
cut -f1 {session_dir}/candidates.tsv | tail -n +2 | sort -u > {session_dir}/.tmp/set_candidates
grep -oE 'C-[0-9]{5}-[0-9]{5}-[0-9a-f]{8}' {session_dir}/verification-summary.md | sort -u > {session_dir}/.tmp/set_verified
python3 -c 'import json; print("\n".join(sorted(x["candidate_id"] for x in json.load(open("{session_dir}/findings/machine-fields.json")))))' > {session_dir}/.tmp/set_mf
diff {session_dir}/.tmp/set_ledger {session_dir}/.tmp/set_candidates; diff {session_dir}/.tmp/set_candidates {session_dir}/.tmp/set_verified; diff {session_dir}/.tmp/set_verified {session_dir}/.tmp/set_mf   # 三处一致
```

## 7b. gate_record.md（Gate-1 强制落盘产物）

```text
每轮 Gate-1 执行后写入（缺文件 = Gate 未执行，宿主判 rework，禁止任何 gate_result 声明）：

| # | 等式 | 输出 | 判定 |
|---|---|---|---|
| 1..16 | E1-E16 | 命令输出 | 成立/FAIL |

判定为 FAIL 的等式：gate_result 只能 rework 或 blocked（禁止 pass_with_gaps 掩盖等式失败）。
gate_result=pass 后由独立 Gate-2 子代理抽查（证据引用可解析、随机 3 条 confirmed 回源码、对抗表抽查），结论写入 run-state 的 gate2_notes，不改变 gate 判定。
```

## 7c. 聚簇命令（检查点两级闭合）——B 类（gate-1.py 已承担，本段 bash 为历史参考）

```bash
awk -F'\t' 'NR>1 {print $3"\t"$4}' {session_dir}/sink_inventory.tsv | sort -u | wc -l   # 簇数（信号级类不入清单）
# 每簇一个深扫分片 + 一个结论文件（clusters/{cluster_id}.md：代表性实例五段证据链 + 攻击模式对抗表 + 终态映射）；簇内全部检查点据簇结论落终态，未聚簇的 sink/source 检查点不得落任何终态（E10 强制）
```

## 8. YAML 单文档校验（run-state.md 行级机械校验）——A 类

```bash
# 不依赖 yaml 库：文档开头必须是键值行（缩进 0 的 'key:'），顶层键不得重复
head -1 {session_dir}/run-state.md | grep -qE '^[A-Za-z_][A-Za-z0-9_]*:' || echo BAD_HEAD   # 必须无输出
grep -nE '^[A-Za-z_][A-Za-z0-9_]*:' {session_dir}/run-state.md | sed 's/:.*//' | sort | uniq -d | wc -l   # 重复顶层键数，必须 0
```
PowerShell 等价：Get-Content 首行正则 + Group-Object 计数重复。

## 9. 检测概况分组计数（深扫/预筛排除）——B 类（v0.11.1：浅扫已废除，light_scan 计数恒 0）

```bash
awk -F'\t' '$2=="terminal" && $3=="deep_scan" {n++} END {print n+0}' {session_dir}/check_point_ledger.tsv
awk -F'\t' '$2=="terminal" && $3=="light_scan" {n++} END {print n+0}' {session_dir}/check_point_ledger.tsv   # 已废：浅扫/light_scan 计数已废
awk -F'\t' '$2=="terminal" && $3=="prefilter" {n++} END {print n+0}' {session_dir}/check_point_ledger.tsv
```
PowerShell 等价：Import-Csv/Get-Content 分组 Where-Object 计数。

> 未分析数 = terminal_state=blocked 的文件终态行数，与 failed_wus.txt 一致并逐条列入报告。

> 无 python3 环境时的降级：POSIX 块中 E5b/E5c/E11/E14/§5-§7 依赖 python3；无 python3 的宿主判 blocked（诚实受阻），禁止以 LLM 手写对账降级替代（unverified_accounting 路径自 v0.3.9 起关闭）。