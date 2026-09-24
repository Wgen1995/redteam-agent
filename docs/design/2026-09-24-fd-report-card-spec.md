# 漏洞报告卡片规格（FD 卡片 v1 定稿——批次 4/6 实现依据）

> 原则：一张卡片=一个漏洞的完整自证。所有内容不空说：每句话都有账本数据举证；所有证据都在渗透识别当刻落盘，不是写报告时现找现编。

## 一、卡片九段（每段的数据源=已落盘事实）

1. 位置：URL/端点/参数/文件路径/功能入口——取自 assets/edges（图谱坐标），格式=资产ID + 表面 + 精确位置
2. 涉及资产与接口：该 finding 关联的资产子图（资产+边+接口签名）——read-ledger 投影，非手写
3. 漏洞描述：一句话类型+一句话影响——类型必须命中矩阵词表（否则不算 finding，进 facts）
4. 等级：tech 严重度（CVSS 向量可复算）× biz 影响（资产价值）双轴——分值公式与调度同源（G-24 基线表），不是拍脑袋
5. 漏洞原理/原因：为什么存在（代码层/配置层/逻辑层归因）——引用 evidence 链：哪条请求的哪个差异暴露了它
6. POC/EXP（Burp 直贴）：
   - raw_request 按抓包原样（header 顺序不重排、不补不改；body 原文）——Burp Repeater 粘贴即发
   - raw_response 原样（含状态行/headers/body）
   - 变体参数（时间盲注的 delay、OOB 的回连域名）单列"判读说明"，不改原始证据
   - 格式契约：EV 卡片 POC 四要素（raw_request/raw_response/时间/环境）为唯一来源；报告渲染=原文转抄，禁止编辑
7. 危害：此环境下的实际影响（拿到什么权限/读到什么数据/影响到哪个业务）——引用 response 中实际回显的数据（脱敏 token 化后的原文），不写"可能造成重大损失"式空话
8. 修复建议：按类型给可执行建议（临时缓解+根治两层）——挂 K1 方法论基准条目；每条建议标注对应的 POC 请求（修复后哪条请求应失效）
9. 复现与验证状态：独立重放门三态（verified/env-diff/unverified）+ 最近一次重放时间——未过重放门的 finding 标记披露，不得宣称 verified

## 二、"不是现找现编"的机检保证（时间链自证）

- 落盘时序断言：evidence.captured_at < finding.added_at < report.issued_at——哈希链+timeline 可证"先有证据后有结论"
- add-finding 的 POC 四要素来自当次渗透的 add-evidence 原文（引用而非复制编辑）；渲染层只转抄，改一字即与 E-index 双指纹不符=validate FAIL
- 独立重放门（批次 4 T5/T6）用 raw_request 原文直发复现——报告里的 POC 是被机器复现过的，不是人写出来的
- 反编造哨兵：redact-scan+取票链保证 evidence 里的凭据引用是 vault token；response 中的真实数据经 tokenize 后原文保留

## 三、落点
- 批次 4：T5 重放驱动（raw_request 直发）+ T9 vuln-agent 归一化（外部发现强制 POC 四要素）直接消费本规格
- 批次 6：报告流水线渲染卡片（P5 签发门 lint：九段齐/时间链断言/Burp 可贴格式校验）
- 探知项 G-25：Burp 粘贴格式边界（HTTP/2 二进制帧、TLS 指定、Host 头与 Connection 归属）——批次 6 渲染器定
