# v0.8 借脑三件套 + judge 窄调用 · Implementation Plan（2026-10-11 批准「都开」）

> Spec 依据： docs/research/artex-deep-dive/0-index.md §v0.8 批次映射（五路实读背书）+ docs/design/tanyin-target-form.md §1 引擎面。
> 纪律： TDD 红绿、Python 3.9 纯 stdlib、py_compile、每件独立测试文件。实现期不 commit（由主会话统一集成后提交）。

## Task A · llmpool 故障转移（cli/ledger/llmpool.py + tests/test_v08a_llmpool.py）
参数表（4 路实读取自 ARTEX，含两处我们声明的改进）：
- 错误分类： 400/ctx取消 不转移；401/402/403/404 硬熔断（1 次即熔）；408/429/网络(URLError/timeout) 软计数；5xx 软计数。
- 软计数连续 3 次熔断；冷却阶梯 1min/5min/30min（连续熔断次数选档）。
- **改进①**: 429 短冷却档（1min 固定）/5xx 长冷却档——分道。
- **改进②**: 冷却加 ±20% 抖动（随机种子注入可测）。
- Registry 进程级 + 状态落盘（ledger 旁 llmpool_state.json，重启恢复未过期窗口）。
- 接口： pick(models:list[dict]) -> 健康链序第一个; report(model, err_or_status); snapshot() -> 三态(healthy/cooling/tripped)+剩余秒。
- 判定纯函数化（时间注入），全部离线可测；不接真 API。
- 事件入账： 每次 trip/recover 写一条 timeline 事件（kind=llm_failover，走既有 timeline append API）。

## Task B · 链式 todolist 稳定器（write_cmds.py 扩展 + tests/test_v08b_chain.py）
- intents.tsv 加 prereq 列（默认空=intent 无前置）。
- 命令： chain-create（同链步骤按序写 prereq 链）; chain-advance（校验前置步骤终态后才放行下一步）; chain-ls（列链与各步状态）。
- 链上步骤继承不蒸发律： prereq 未终态的 intent 不得进入 frontier（查询侧过滤+写入侧 Reject 双保险）。
- 与 EDGE_KINDS 共存： 链步骤间补 spawns/derived_from 边（复用既有写边 API）。
- 测试： 无前置放行/有前置且未终态 Reject/前置终态放行/重启后链状态可恢复（读 TSV 即态）。

## Task C · trace 检索（cli/ledger/trace_search.py + tests/test_v08c_trace.py）
- 只读： search(pattern, scope=runner_logs|timeline|both, battle=None, last=None) -> 命中行及上下文各 2 行。
- 数据源： battles runner 日志目录 + timeline.tsv；不写任何文件。
- 测试： fixture 日志+timeline，断言命中/上下文/last 截断/scope 过滤；恶意 pattern（超长/全匹配）性能与安全（禁正则炸弹：仅 literal substring，不做 regex）。

## Task D · judge 窄调用客户端（cli/ledger/judge_client.py + tests/test_v08d_judge.py）
- stdlib urllib 直连 openai 兼容端点（模型/URL/key 从 env 读，缺省 None→"not-configured"）；temperature=0, max_tokens 512。
- 输出契约严格解析（借 3 路配方）： 仅接受单 JSON 对象、键白名单、重复键/多余字段/截断/散文一律 → verdict=None + reason；fail-closed 任何异常不外抛猜测。
- 独立接口 ask(prompt) -> (verdict_dict|None, reason)；不做工具、不做多轮。
- 测试： 本地 http.server stub 模拟三种响应（合法/畸形/超时）断言三态；真实 API 永不在测试里调用。

## 集成（主会话执行，不在子任务内）
全量回归 → 逐任务 commit → HANDOFF v0.8 段 → 蓝图双胎 v0.8 行 → push。
