# 方向修正案 1 号（2026-10-15 · 六专家独立评审合流）

## 一、总判决
**产品方向（AI 自动化渗透）维持——六位独立专家零否决。** 全部刀口落在执行层： 优先级（E2）、刻度（E4）、地基（E1/E5）、设计完备度（E6）、批次纪律（E3）。修正后的路线如下，**还债排序新律： 由「哪颗先炸」驱动，不由「本批顺手」驱动**（E5 病根诊断）。

## 二、修正后路线（v1.0b 多战士开战前的三张门票）
### 票① · v0.9d 收口批（E3,已定范围）
侧栏骨架+12 级灰阶（按冻结设计）/死链收口+NAV 测改每链可达/人话禁词替词表进测试/最新发现按 finding-stream-priority 规格/status.js 切外链（server 静态句柄 S 舰在加）/语言律加触发器「共享代码复制≥3 份」。

### 票② · v0.9.6 执法面升权批（E2,不批则自主化=给被俘战士扩权）
- S1 信任根摘出: 战士 env 剥离（TANYIN_JUDGE_*/APPROVAL_KEY 不可达）+approvals/approvers 战士只读+审批 HMAC 通道启用（现成件差一步）
- S2 egress 实挂: request-ticket 机械记账+docker exec 走 guard（覆盖率 0%→机械强制）
- S3 时戳防时间旅行: 执法钟改链上锚（账本 seq 单调）,自报 --timestamp 降级为参考值
- S4 replay 授权窗+危险方法分类+次数帽+scope 单源（吃掉第二套实现）
- S5 promote 信任源门: 持钥签名+EV 链复核（**知识库接检索前的前置硬门**）
- S6 车道A 内容消毒规约进 v1.0a 设计稿

### 票③ · v0.9.7 循环地基批（E1+E5）
- O(1) 追加写（open("a")+尾行 prev_hash,读侧半行容错已有）+flock 超时+SSE 偏移游标+分段归档——实测 18µs/行线性劣化必须先治
- 读侧撕裂封口: epoch 戳（30 行,拖了两个评审周期）
- **枚举单源化**: GATE_ORDER/cmd_status seq 统一（P6.0 活bug根治）/命令面四处手抄→registry 单源派生/selfcheck 表派生/「禁双份枚举」从注释变机器
- 接线四件: llmpool pick→ask→report 成环+池单写者化/judge_client 生产接线/wall_clock 心跳源/intent owner+lease+机械 dedup 键
- **sqlite3 投影层决策（呈用户）**: stdlib 里就有 sqlite3——推荐分层: TSV=真相层（审计直读卖点不动）,sqlite3=投影索引层（治撕裂+查询+O(1)），Go 边车三触发器维持（E5 判定今天全不可点火,随车道A 遥测再评）
- 异常分流: 代码 bug 与门禁失败在账本可区分（rc 语义）
- SYSTEM-MAP ≤200 行入口档+Ruling 索引（人/AI 双用 onboarding）

## 三、v1.0 双车道重设计（E6 六裁决吸收）
单图两域+第 11 边型 anchor（provenance 必填）,不开第二图仓;解析产物必入 13 表;车道A 金样律+失败律+六灰区预裁决+YAML 取舍呈批;账位=endpoint→assets/sink→facts(engine-static)/深挖卡→intents(engine-hyp 勘误);矩阵只加证据位;激励五修正（**排序权给规划者,终止/剪枝权不给;engine deferred=0 进 P4 门**）;codex 六层三成可抄落 T2/T3;实验设计吃下 E4 全部（GT-free 考场+三 sha256+战层配对置换 N≥4+post_auth 主指标+GT-T2 与 GenSift INV 孪生共建+死区 14 题零战成本归因先行）。

## 四、v1.0b 常驻循环（E1 对账 b26）
规划者=唯一写者,战士产 submissions（契约既有答案）;派发 intent 级+战士长寿命带账恢复（b26 失分机制=会话重置上下文碎片化）;计划书必含「与 b26 判决对账」节。

## 五、待用户裁决三件
1. 本修正案整体（批/改）
2. sqlite3 投影层（推荐分层方案如上）
3. ZhuLong 导入闸放行（对仓一行,您自己的仓）
