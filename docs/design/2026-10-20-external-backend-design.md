# 功能24 外部执行后端·设计定稿(harness即后端)· 2026-10-20

> 输入: 裁决书§11(已裁: 阶段2任务包→后端会话→记录行归一)+Multica全量清点§7.2/§8(dsh一等后端协议全形+七条冲击)。67律: 每条决定对照竞品。

## 干什么(人话)
把外部 AI 后端(dsh/claude/codex/opencode…)当**编外士兵的肌肉**: 我们的军官派活定规矩,外部 harness 出力执行,成果一律回我们的账本、过我们的质量门。两个方向: ①我们用别人当后端(肌肉扩容,白盒兵种/重型任务) ②别人用我们当后端(profile 分发,生态位)。

## 里面怎么转(六件)
1. **协议=版本化 JSONL stdio v1**(Multica/dsh 已商品化的形状,不发明新协议): 帧 ready/session/text/thinking/tool_call/tool_result/usage/result/error,task_id 关联。MCP stdio=阶段3扩展位,不现在做。
2. **Backend 统一接口,字段按 Multica 26 后端 checklist 全集**(它缺一块就是我们的对标缺口): resume(期望/被拒/通知三语义)/supplement(中途改目标——渗透刚需)/tool_activity+interrupt(工具级看门狗,长扫描必备)/terminal_observed(防「完成」被误判挂起)/usage 四 token 维+成本 ticks。
3. **会话映射**: 意图卡→任务包(goal+scope+预算+红线序列化)→后端会话→流式回传(seq 截断三态)→**记录行归一: 外部肌肉产的事实/发现走我们全部质量门(哨兵前置→验证官复放→GT 棘轮),零豁免**——这是与 Multica 的根本差异(它无质量门层)。
4. **权限分级=差异化卖点**: Multica 全线 bypassPermissions;我们范围锁+审批+guard 门链对外部后端同样生效——「受控渗透」恰恰是它没有的。
5. **能力协商**: capability 常量缺省=安全失败,新字段不认识=降级不崩(抄 Multica 模式,灰度安全)。
6. **profile 载体**: graphled 分发 profile+检测+自愈(未装=runtime 降级+两条修复路径+自动装守门,Multica 模式)。

## 你看到什么
设置页「外部后端」面: 每个后端(名字/状态/装没装 profile/最近用量/花多少钱);任务页里外部执行的活标「外包」来源;产出照常进漏洞榜(经质量门)。

## 失败怎么办
后端崩→会话 resume 三语义(期望续/被拒/通知);租约超时→沿用战士既有回收律;结果不可归一→记原始流+人工通道,不硬编。

## 对比(67律)
Multica=26后端+协议成熟(最强,全抄协议形) 但 全线bypass+零质量门+零渗透纪律;ARTEX 无此后端层;CSAI 有 MCP 联邦(协议位=我们的阶段3)。**我们独有**: 外部产出过质量门+权限分级+账本归一防篡改。

## 建序
F24a(本舰): Backend 抽象+adapters 三件(dsh/claude/codex)+任务包序列化+流式归一入账(走既有 add-fact/add-finding 通道)+usage 入 budget——≈1500行 TDD。
F24b(后): profile 分发自愈+MCP client+daemon 化(多机)。
