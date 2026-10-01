#!/usr/bin/env python3
# v0.11.0 fixture 重建：与 gate E1-E72 新协议对齐
import csv, hashlib, json, os, sys

F = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(F, 'fixture')

def w_tsv(name, header, rows):
    with open(os.path.join(FIX, name), 'w', encoding='utf-8', newline='\n') as f:
        w = csv.writer(f, delimiter='\t')
        w.writerow(header)
        for r in rows:
            w.writerow(r)

# 1. check_point_ledger.tsv：删 fix_presence 5 行（v0.4.3 禁止派生，E33 机械禁止）
w_tsv('check_point_ledger.tsv',
      ['basis_id','direction','mechanism','check_point_id','candidate_ids','terminal_state','reason','concluded_at'],
      [['s1','backward','pattern_driven','CP-000001','C-00001-00001-1d832469','candidate','cluster_conclusion:clusters/SINK-DESERIALIZE.md','2026-08-14T00:05:00Z'],
       ['s2','backward','pattern_driven','CP-000002','','disproved','cluster_conclusion:clusters/SINK-CMD-EXEC.md','2026-08-14T00:05:00Z'],
       ['s3','backward','pattern_driven','CP-000003','','disproved','cluster_conclusion:clusters/SINK-XXE.md','2026-08-14T00:05:00Z'],
       ['r1','forward','pattern_driven','CP-000004','C-00001-00001-1d832469','candidate','cluster_conclusion:clusters/SINK-DESERIALIZE.md','2026-08-14T00:05:00Z'],
       ['r2','forward','pattern_driven','CP-000005','','disproved','cluster_conclusion:clusters/SINK-XXE.md','2026-08-14T00:05:00Z'],
       ['java/a/B.java','terminal','deep_scan','CP-000006','C-00001-00001-1d832469','candidate','cluster_conclusion:clusters/SINK-DESERIALIZE.md','2026-08-14T00:05:00Z'],
       ['java/c/D.java','terminal','deep_scan','CP-000007','','disproved','cluster_conclusion:clusters/SINK-XXE.md','2026-08-14T00:05:00Z'],
       ['docs/README.md','terminal','prefilter','CP-000008','','not_applicable','prefilter_no_exec:doc:0命中证据','2026-08-14T00:05:00Z']])

# 2. audit_log.tsv：删 fix_presence 行，保持时间戳单调（E70）
w_tsv('audit_log.tsv',
      ['check_point_id','basis_id','direction','result','evidence_type','evidence_ref','reviewed_at'],
      [['CP-000001','s1','backward','candidate','direct','java/a/B.java:10','2026-08-14T00:01:00Z'],
       ['CP-000002','s2','backward','disproved','direct','java/a/B.java:20','2026-08-14T00:02:00Z'],
       ['CP-000003','s3','backward','disproved','direct','java/c/D.java:5','2026-08-14T00:02:00Z'],
       ['CP-000004','r1','forward','candidate','direct','java/a/B.java:10','2026-08-14T00:03:00Z'],
       ['CP-000005','r2','forward','disproved','direct','java/c/D.java:30','2026-08-14T00:03:00Z'],
       ['CP-000006','java/a/B.java','terminal','candidate','direct','java/a/B.java:10','2026-08-14T00:04:00Z'],
       ['CP-000007','java/c/D.java','terminal','disproved','direct','java/c/D.java:5','2026-08-14T00:04:00Z'],
       ['CP-000008','docs/README.md','terminal','not_applicable','direct','docs/README.md:1','2026-08-14T00:04:00Z']])

# 3. candidates.tsv：16 列（C1）+ V01（E61）
w_tsv('candidates.tsv',
      ['candidate_id','location','sink_type','severity_hypothesis_initial','root_cause_group_id','lifecycle_state','verdict','cluster_ref','verification_record_ref','report_record_ref','created_at','discovery_source','path','start_line','end_line','discovery_reasoning_note'],
      [['C-00001-00001-1d832469','java/a/B.java:10','SINK-DESERIALIZE','critical','RCG-DESER-TEST','reported','confirmed','clusters/SINK-DESERIALIZE.md','verification-summary.md#C-00001-00001-1d832469','V01','2026-08-14T00:00:00Z','pattern_driven','java/a/B.java','10','10','从 source r2 追链到 sink readObject，逐跳证据见 flow_edges']])

# 4. flow_edges.tsv：r1 被 S1 剪（E62），reachable 边改为 r2（file 类未剪）；s2 补 no_path（E68）
w_tsv('flow_edges.tsv',
      ['source_id','sink_id','direction','hops','evidence_refs','judged_by','timestamp'],
      [['r2','s1','reachable','2','java/c/D.java:30,java/a/B.java:10','WU-0001','2026-01-01T00:00:00Z'],
       ['r2','s2','no_path','-','java/c/D.java:30','WU-0001','2026-01-01T00:00:00Z']])

# 5. run-state.md：gate2_notes 引用文件 + 注册枚举 skip_reason + 指纹重算
# v0.11.1: §7 A 类权威口径——sha256[:16] + json.dumps sort_keys + 按 candidate_id 排序（与 gate E51 完全一致）
core = [{'candidate_id': 'C-00001-00001-1d832469', 'location': 'java/a/B.java:10', 'sink_type': 'SINK-DESERIALIZE',
         'severity': 'critical', 'root_cause_group_id': 'RCG-DESER-TEST', 'verdict': 'confirmed'}]
import json
core.sort(key=lambda x: x['candidate_id'])
fp = hashlib.sha256(json.dumps(core, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
open(os.path.join(FIX, 'run-state.md'), 'w', encoding='utf-8', newline='\n').write(
    'run_id: fixture-run\n'
    'run_status: running\n'
    'current_capability: report-delivery\n'
    'gate_summary: null\n'
    'gate2_notes: "gate2_notes.md V0 pass V1 pass V2 pass V3 pass"\n'
    'runtime_verification: denied\n'
    'run_fingerprint: ' + fp + '\n'
    'a5_skip_reason: no_sinks_matched\n'
    'wu_skip_reason: fixture-small-target\n'
    'missing_check_skip_reason: fixture-small-target\n'
    'updated_at: 2026-08-14T00:00:00Z\n')

# 6. gate2_notes.md（E41 文件痕迹）
open(os.path.join(FIX, 'gate2_notes.md'), 'w', encoding='utf-8', newline='\n').write(
    '# A2 独立验证四门结论（复核对象：verification-summary.md）\n\n'
    'V0 事实源对账 pass：三清单/账本/候选交叉一致。\n'
    'V1 逐候选重建验证 pass：C-00001-00001-1d832469 从源码独立重建证据链成立。\n'
    'V2 负向对抗 pass：证伪尝试失败，无换皮贴标。\n'
    'V3 剪枝判据复核 pass：pruning_ledger 两行 a2_verified=true。\n')

# 7. reviews/{8}-review.md（E67）
reviews = os.path.join(FIX, 'reviews')
os.makedirs(reviews, exist_ok=True)
for st in ('0.5','1.2','1.3','1.4','1.5b','2.1','2.2','3.1'):
    open(os.path.join(reviews, st + '-review.md'), 'w', encoding='utf-8', newline='\n').write(
        '# review ' + st + '\n\nPASS：产物与源码逐条对拍一致，无批量闭合/换皮贴标。\n')

# 8. wu_manifest + batch_progress + 分片（E23/E43/E38/E71）
w_tsv('wu_manifest.tsv',
      ['wu_id','sink_type','sink_ids','sink_locations','sink_count','status','cluster_id','batch_num'],
      [['WU-0001','java/a/B.java','s1;s2','java/a/B.java:10;java/a/B.java:20','2','pending','CL-f4a1c2b3','B001']])
w_tsv('batch_progress.tsv',
      ['batch_num','status','wus_total','wus_done','findings_count'],
      [['B001','completed','1','1','1']])
os.makedirs(os.path.join(FIX, 'batches', 'B001'), exist_ok=True)
w_tsv(os.path.join('batches', 'B001', 'WU-0001.tsv'),
      ['sink_id','verdict','five_segment_evidence','evidence_refs','reviewed_at'],
      [['s1','candidate','source=r2 file|prop=readAll->readObject|sanitizers=none|sink=readObject|disproof_checked','java/c/D.java:30,java/a/B.java:10','2026-08-14T00:01:00Z'],
       ['s2','disproved','source=r2 file|prop=readAll->exec|sanitizers=execArgsConst|sink=Runtime.exec|disproof_checked','java/a/B.java:20','2026-08-14T00:02:00Z']])

# 9. graph_snapshot 计数更新（flow_edges=2 pruning=2）
w_tsv('graph_snapshot.tsv',
      ['batch','unchecked','candidate','disproved','not_applicable','blocked','flow_edges','pruning_rules','graph_nodes','graph_edges'],
      [['B001','0','1','1','10','0','2','2','20','11']])

# 9.4 v0.11.6 时序化新方程所需产物：capability-profile + threat-context + attack-surface-map
open(os.path.join(FIX, 'capability-profile.md'), 'w', encoding='utf-8', newline='\n').write(
    '# capability-profile（黄金夹具样例）\n\n- host: POSIX python3\n- runtime_verification: denied\n')
open(os.path.join(FIX, 'threat-context.md'), 'w', encoding='utf-8', newline='\n').write(
    '# threat-context（黄金夹具样例）\n\nconfirmation_policy=conservative_continue；user_confirmed=conservative_assumption_applied\n')
open(os.path.join(FIX, 'attack-surface-map.md'), 'w', encoding='utf-8', newline='\n').write(
    '# attack-surface-map（黄金夹具样例）\n\n## 命名类别扫描结果\n\n| 类别 | 命中数 |\n|---|---|\n| SINK-DESERIALIZE | 1 |\n')

# 9.5 v0.11.3 扫雷信息板（doc 115：fact/clue/break + 精查清单——E75/E76/E77 正例）
open(os.path.join(FIX, 'mine_scan_board.md'), 'w', encoding='utf-8', newline='\n').write(
    '# 扫雷信息板（每批追加；WU 派发时附带相关条目，DEFINE 判据必须对照）\n\n'
    '## fact（确定性事实——工具可复验，必须带 file:line 证据）\n\n'
    '| id | 内容 | 证据(file:line) | 发现 WU | 状态 |\n|---|---|---|---|---|\n'
    '| F-001 | 框架反序列化防护=ObjectInputFilter 类白名单，实现在 B.java 的 resolveClass | java/a/B.java:8 | WU-0001 | verified |\n\n'
    '## clue（判定线索——LLM 发现可独立复核的基准，结论仍独立下）\n\n'
    '| id | 内容 | 证据 | 适用 sink 类 | 状态 |\n|---|---|---|---|---|\n'
    '| C-001 | resolveClass() 对全部反序列化入口做类名校验 | java/a/B.java:8 | SINK-DESERIALIZE | verified |\n\n'
    '## break（已确认断点——负向级联；下游引用时仍需一次独立复核）\n\n'
    '| id | 路径段 | 证据 | 状态 |\n|---|---|---|---|\n'
    '| B-001 | r2 输入→exec 分支不流（execArgs 为常量拼接） | java/c/D.java:30 | verified |\n\n'
    '## 精查清单（雷邻：雷的 flow 链上游未查检查点）\n\n'
    '| checkpoint_id | 原因 | 关联雷(sink_id) |\n|---|---|---|\n'
    '| CP-000004 | 雷 C-00001-00001-1d832469 链上游 source 前向复核 | C-00001-00001-1d832469 |\n')

# 10. v0.11.3 E78: 对 14 子任务逐次跑 gate --subtask 生成真实 gate_run_log（防伪造 gate_progress 的对账源）
import subprocess as _sp
for _st in ('0.1','0.2','0.3','0.4','0.5','0.6','1.1','1.2','1.3','1.4','1.5b','2.1','2.2','3.1','3.2'):
    try:
        _sp.run(['python3', os.path.join(F, '..', 'gate-1.py'), '--session', FIX,
                 '--source', os.path.join(F, 'fixture-src'), '--subtask', _st],
                capture_output=True, timeout=120)
    except Exception:
        pass
print('fixture rebuilt; fingerprint=' + fp)
