# 预筛规则（阶段0/1 预筛分流权威，v0.11.0 A10 重写）

> 依据：docs/research/45-derivation-chain.md + 48-v04-pure-llm-final.md + 77-final-design-adjudication.md（浅扫三档已废除、5% 抽样已废除——用户核心约束绝对不抽样）。
> 现行执行载体：contracts/derive_checkpoints.py（机械闭合，跨平台 python3）。

## 总则

1. **预筛只分流不排除**：预筛把文件分流为「机械排除（命中排除规则，not_applicable）」与「深扫（未命中，逐文件真实分析）」两类；**没有浅扫中间态**（v0.4 已废除——文件结论只有机械排除或真实分析两条路）。
2. **排除需规则 + 证据**：标 not_applicable 必须写明命中的规则名与证据（prefilter_no_exec: 前缀 + 类型判定 + 0 命中 grep 输出引用）。
3. **禁止抽样复核**：绝对不抽样（用户核心约束）；排除证据来自全量 grep/扫描输出，不是抽样。

## 排除规则（全部满足才可 not_applicable）

| 规则名 | 条件（全部满足才可标 not_applicable） | 必录证据 |
|---|---|---|
| 无执行面文件 | 文件不含任何可执行代码（纯文档/图片/数据文件），且不在任何入口清单、不被任何代码引用 | file 类型判定 + 无入口特征 grep 结果 + 无引用证据 |
| 无危险 API | 文件不含任何 sink 双轨索引的 grep 模式，且不含入口特征 | 逐类 sink grep 0 命中证据 + 入口特征 0 命中证据 |
| 生成/构建产物 | 明确为生成物（如 dist/、min.js.map），且源码侧存在对应源文件（源文件另行入清单） | 生成物判定 + 对应源文件路径引用 |
| 二进制文件 | binary_flag=binary 或 type ∈ {image,binary,archive} 且无 sink 命中 | binary 探测结果 + 0 命中证据 |

## 机械闭合命令（v0.11.0：derive_checkpoints.py 承担，跨平台）

文件终态检查点（direction=terminal）按以下优先级**机械**落终态（python3 derive_checkpoints.py --session {session_dir}）：

1. binary_flag=binary 或 type ∈ {image,binary,archive} 且无 sink 命中 → not_applicable，reason 前缀 prefilter_no_exec:；
2. type 为 doc（纯文本/文档）且无 sink 命中且无入口特征 → not_applicable，reason 前缀 prefilter_no_exec:；
3. 其余文件（含所有有 sink 命中的文件、type 为 source/other 的文件）→ deep_scan（LLM 真实分析，结论落终态）。

只有第 3 类需要 LLM。第 1/2 类由脚本机械闭合——文件终态的大头从机制上消灭「文件分析未完成」类缺口。

## 排除记录格式

每个预筛排除的文件，在 check_point_ledger.tsv 的终态写 not_applicable，reason 含：

```text
prefilter_no_exec:{规则名}:{类型判定}:{0 命中证据引用}
```
