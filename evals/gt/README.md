# evals/gt/ — GT 集版本化（索引+战场+锚+基线）

## 一、现状盘点（2026-10-19 勘）

| 件 | 现状 | 口径 |
|---|---|---|
| tests/range/ground-truth.json | 56 面 session-GT（20→50→56 三次扩编；23 漏洞类；post_auth 16 面；alt_forms 孪生键） | 黑盒会话召回：键=host+path（query 剥离/尾段数字归一）；EV 词证 marker；keying v7 |
| tests/golden 54 面 + run_golden.py | 金样字节回归（M01 hard 门） | 逐字节零漂移 |
| tests/evals/metrics-v1.json | L1-L3 指标注册（M09 authz-recall/M10 range-recall 等） | collect-first→数值基线合闸（P1-8） |
| tests/fixtures/G-r4..G-r27 | 真战会话夹具 24 件（各配 gold 测试钉 recall） | 防尺子漂移的回放锚 |
| GT-scorecard（D2 三臂） | **未建**（08-自动化与评测专家 P0-1 在册：ARTEX findings→GT 键 mapper+诱饵负对面+三臂登记） | 本目录为其地基件；三臂跑通后从度量页出数 |
| ZhuLong 伤疤集 | **本批入册**（zl-webface-v1/zl-supplychain-v1；usage-guide-zhulong.md Z:206-208+walk-zhulong-live.md §3 交叉互证） | 白盒源码锚（见下） |

召回基线对照：13 战 web 靶场均值 0.55-0.59/单战峰值 0.70（exceed-review 03/07）；
本批三场实测=battle-40 0.62/battle-41 0.62/battle-42 0.70（vs 既有 0.71 基线参考值：
battle-42 口径 39/56=0.696≈0.70，40/56 形=0.714——0.71 即此带；三场均值 0.645）。
误报（FP）基线首采：b40 FP=31（过度报告战，96 findings 行）/b41 FP=3/b42 FP=1
（FP 口径=活跃发现数−GT 命中数；合成靶场全真值=GT，重复报告/诱饵面命中皆计 FP）。

## 二、覆盖面缺口表（漏洞类×深度）

深度轴：L1 单请求 beacon（合成 range 已覆盖）→ L2 源码级白盒（本批 zl-* 开垦 7 类）
→ L3 链式/多步（**本批落成**：zl-chain-v1 源码链 2 条 + range-chain-v1 会话链 2 条）
→ L4 基础设施/容器（空白）。

| 漏洞类 | L1 合成会话 | L2 源码白盒 | L3 链式 | L4 基建 |
|---|---|---|---|---|
| sqli/xss/ssti/cmdi/cors/jwt/xxe/rfi/lfi/graphql/ratelimit/userenum/weakpass/upload/deser/redir/infoleak/traversal/idor/hauth/role/broken-access-control/ssrf | ✅ range-56（23 类） | ssrf✅ xss✅ traversal✅ broken-access-control✅ csrf✅ file-read✅（zl-*） | userenum→weakpass→idor✅（range-chain-01）weakpass→idor✅（range-chain-02） | ❌ |
| 任意目录读（CWE-552） | ❌ | ✅ zl-web-02 | ✅ zl-chain-02 首环 | ❌ |
| CSRF/DNS-rebinding（CWE-353） | ❌（合成 csrf 归 broken-access-control） | ✅ zl-web-03 | ❌ | ❌ |
| 凭据文件暴露（CWE-538） | ❌ | ✅ zl-sup-02 | ✅ zl-chain-02（读入→主钥→解封） | ❌ |
| 供给链/令牌准入（CWE-306） | ❌ | ✅ zl-sup-01 | ✅ zl-chain-01（令牌→注册→claim→回采 4 环） | ❌ |
| 可用性 DoS（CWE-248） | ❌ | ✅（修复锚 zl-sup-03） | ❌ | ❌ |
| 弱口令爆破/锁定 | weakpass✅ | 诱饵面✅（d03） | ✅（两链凭据环） | ❌ |
| 容器逃逸/orchestrator/云元数据实弹 | ❌ | ❌ | ❌ | ❌（最大空白） |
| 业务逻辑/竞态/反序列化真库 | ❌（**L3 种子已铸**： battlefields/range-bizflow-v1.json——改价/优惠券重用/取消后发货三链，种子态未注册，激活=GT 植入+夹具+注册三步齐） | ❌ | ❌ | ❌ |

优先补法建议（下批）：①L4 容器/编排面（BO9 sandbox 族伤疤扩容）②L3 链式再扩
（CSRF/rebinding 面+DoS 面成链）③held-out 冻结集（出题器 v1=P1-6 后训练/考试分家）。

## 二·五、chain-gt 战场口径（L3 链式——本批）

- **链=有序步骤组**：battlefield JSON `chains[].steps[]`，环序 `order` 1..N 连续，
  环环 verify_cmd（守卫同 source-gt：grep/test 段式只读，黑名单硬拒）；链/环 id 全局
  唯一（与 source-gt 行号同空间）。
- 两类锚：**源码链**（zl-chain-v1——锚根=verify_root 字段，缺省 snapshots/zl-repo，
  `--live` 时 live_anchor 战场切 ZhuLong 仓根只读）与**会话链**（range-chain-v1——
  步=`gt_ref` 指向 session-GT 条目，verify_cmd 锚=链在案全过的夹具账本，cwd=仓根）。
- **链级两档判分（写死不漂）**：gt_eval.py `CHAIN_TIERS = {full: 1.0, partial: 0.5,
  zero: 0.0}`——整链全对=1.0/部分对（≥1 环非全环）=0.5/零=0；断环位置不加分不扣分。
  chain_recall=Σ链分/链数；同场输出 step_recall（环级平铺）与 flat_recall（全场平铺）
  作对照。测试钉死常量与判分（test_gt_chains.py）。
- 消费面：`gt_verify.py` 收链校验（环序/环号/守卫/锚跑/会话链 gt_ref 落册）；
  `gt_eval.py --chain <json> [--write-chain <tsv>]` 出链式召回（三既有战对照=
  baselines/gt-chain-baseline-v1.tsv + 注记）。

## 三、source-gt 战场口径（zl-*）

- 行字段：id/battlefield/polarity(pos|neg)/status(open|fixed-anchor|decoy)/class/cwe/
  severity/title/location/finding/verify_cmd/provenance/entered_at（完整性由测试钉）。
- **open**=当前 HEAD 仍开放的真发现（4+2 面）；**fixed-anchor**=已修复伤疤的回归锚
  （锚消失=修复回退=评测 FAIL，与召回回退同律）；**neg**=FP 诱饵负对（加固面锚定在位，
  报告它=误报——FP 量测的负对面）。
- verify_cmd：以锚根为 cwd 的只读复合命令（grep/test 段式；黑名单词面硬拒=校验器守卫）。
  锚根缺省=`snapshots/zl-repo`（离线 CI）；`--live` =ZhuLong 靶场仓根（只读实跑；
  入库时 15/15 行 live 全过——伤疤锚定真仓，非仅快照）。
- 靶场仓只读律：本舰对 ai-assisted-security-verification-platform 零写入（伤疤=在册记录：
  usage-guide-zhulong.md §9 + walk-zhulong-live.md §3 + BO9 回执）。

## 四、快照纪律

snapshots/zl-repo/ 下文件=锚承载摘录（非可构建源码）：首行 `GT-ANCHOR-SNAPSHOT` +
来源路径注释 + 命中锚的原文行段。再生成方式：按战场 JSON 的 location/锚串从靶场仓
（只读）重摘。快照漂移≠靶场漂移——以 `gt_verify --live` 为准（本机实跑在 baselines 注记）。

## 五、capability_gate 消费契约

1. 读 `gt-index.tsv`（TSV；# 注释行跳过；**11 列**见文件头注释——chains/steps=链式
   步骤组字段，非链行为 0；链行 chains/steps 与战场 JSON 逐数对账由 gt_verify 钉）；
2. source-gt 战场：逐 JSON 行消费（字段见 §三）；变更影响面=open 行数 ±、
   fixed-anchor 锚 rc、neg 诱饵命中数（FP 计数）；
3. 会话评测：`python3 evals/gt/gt_eval.py --session <dir> --label <名> --write <tsv>`
   （复用 tests/eval_range_recall 单源 scorer；keying 随其常量）；
4. 门禁建议：召回≥基线−容差 且 FP≤基线+容差 且 fixed-anchor 全过 且链环锚全过
   （棘轮律：回退=拒合并）；基线数值以 baselines/ 追加行为准（不覆写历史）；
   链式面基线=gt-chain-baseline-v1.tsv（两档判分写死，漂移=尺子坏）。
