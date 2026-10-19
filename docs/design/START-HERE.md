# START HERE · 会话启动锚(任何新会话/上下文压缩后,先读本档,按读序走)

## 一句话现状(2026-10-20)
v4 总案待用户过审;P0 施工 T1-T4 已落(读面/登录/Vite 壳),T5+ 冻结待 v4 过审解冻。

## 读序(权威优先级)
1. 本档 → 2. docs/design/2026-10-20-product-master-design-v4.md(现行总案) → 3. docs/research/2026-10-20-personal-full-read.md(ARTEX/CSAI 四相全深档案) → 4. docs/design/2026-10-20-system-mechanism-ledger.md(28 机制对照) → 5. docs/superpowers/plans/p0-execution-ledger.md(施工态+裁决) → 6. docs/design/2026-10-20-build-master-plan.md 落舱记(历史)
旧档(full-history-synthesis/v3 总案)已被超越,仅考古。

## 用户裁决全集(不可违背)
1. 产品=「和 ARTEX/CSAI 一样的产品」完整渗透平台;「AI 自动挖洞,误报漏报都好,可控制」
2. 对话即指挥(opencode 式);AI 原生交互原则: AI 能推断的不让用户填,AI 只问真缺的
3. 两级播报(指挥级人话+点开原文);危险请示=中间档;单一常驻对话
4. 技术栈四节裁决: Vite+React SPA/FastAPI 读面/SQLite 只读索引/流量 P0 钩子→P1 Go 边车;引擎 Python 保留,引擎零改
5. 「不要被现有实现限制,不合理就换,但能力一件不丢」;全功能对照纪律(禁静默消失)
6. 授权哲学: 授权确认+预算两问+范围红线;拒「授权前置不反问」;不采 C2/WebShell
7. 「不能乱来,实事求是」: 没读过就说没读过;禁止清单面冒充深读
8. 词汇律: 用户词表(harness/AI 调度/首仗),答人话;禁超 ARTEX/CSAI 空话(除非逐点有据)

## 工艺铁律
- 测试: PYTHONPATH=cli python3 -m unittest…,管道出口码不可信,显式收 rc;前端 vitest;E2E Playwright channel=chrome
- 提交: pathspec-only;文档编辑用 edit 工具带断言(python replace 静默失败教训×1)
- 验收: 独立复跑才算过(npx 假验收教训×1);68 律三验
- 每次落地→落舱记→push

## 下一步
v4 过审 → 解冻 T5+(指挥台五件/会话签/灰卡) → P0' 新吸收件入 P1。

