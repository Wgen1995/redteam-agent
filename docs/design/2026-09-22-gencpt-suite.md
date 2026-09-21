# 探隐 GenCPT — 容器与 K8s 渗透测试技能套件（最新源码定稿）

> **这份是什么**：GenCPT（Gen=生成式 AI + CPT=Container Penetration Test）的专项设计页——容器/K8s 场景的全流程渗透技能套件全景，探隐生态的容器引擎/知识源候选。
> **怎么读**：先 §1 定位与 §2 五层架构，再 §3 九阶段流程逐段下钻；§9 与探隐 v2 的同构对照、§10 实测核验（README 陈旧口径纠偏）、§11 你自己的 v2 计划评审差距。
> **以谁为准**：以 docs/design/imported/gencpt/GenCPT-main/ 源码考古为准（事实带文件:行号证据），规模计数全部实测核验。

## 1 项目定位

GenCPT 是一套基于 LLM 语义驱动的容器与 Kubernetes 渗透测试技能套件：通过 SSH 远程对 K8s/Docker/containerd 环境执行 **合规检测 → 攻击验证 → 链式攻击 → POC 生成 → 报告交付** 全流程渗透测试，支持攻击模式库自我进化。

| 项 | 值 |
|---|---|
| 运行形态 | 纯 Markdown SKILL 体系（零 Python 判定脚本），寄宿于 opencode CLI / Claude Code 等 AI 编码代理 |
| 组成 | 1 个 Pipeline 入口 SKILL + 15 个 Phase 子技能 + 6 个共享规范 + 知识库 |
| 执行单元 | 每 Phase 以 Task(general) 独立子代理执行（独立上下文窗口），SSH 命令经 ssh-manager MCP 唯一出口 |
| 产物 | Markdown 报告（合规/攻击/全景三份）+ JSON 知识图谱 |
| 规模实测 | 163 文件（134 md）/ 49 攻击模式 / 226 合规规则 / 188 假设条目 / 15+5 机制 |

## 2 架构全景

### 2.1 五层架构

```text
+--------------------------------------------------------------+
| ① 接入层  opencode CLI（用户入口）+ ssh-manager MCP            |
|           -> SSH 远程服务器 -> 目标环境 K8s/Docker/containerd  |
|              （所有远程命令唯一出口）                          |
+--------------------------------------------------------------+
| ② 编排层  Pipeline 入口 SKILL：参数收集·环境验证·初始化        |
|           suite_version·熔断计数器·环境指纹                    |
|           progress.json 状态机：pending->in_progress->complete |
|           （batch 级断点续传，中断后从最后 WU 恢复）           |
+--------------------------------------------------------------+
| ③ 执行层  9 个 Phase 检测流程（P1a...P9，见 §3）              |
|           每 Phase 独立子代理·独立上下文                       |
+--------------------------------------------------------------+
| ④ 知识库层 knowledge_graph/（Phase 间数据传递唯一媒介）        |
|           attack-patterns/ 49 模式·compliance-rules/ 226 条   |
|           hypothesis-libraries/ 188 条·_learned/ 自进化区      |
+--------------------------------------------------------------+
| ⑤ 规范层  6 个共享规范（输出标准/证据标准/审批分级/...）       |
+--------------------------------------------------------------+
  贯穿链路 A（基础设施）：ssh-manager MCP -> SSH -> 目标环境
  贯穿链路 B（检测原理）：合规 fail -> 三库联动映射攻击前置
                          -> L0 探测 + L1 验证前置 -> L2 差分攻击证明
```

### 2.2 LLM 调用闭环

每 Phase = 独立子代理（Task general）+ 独立上下文窗口；命令经 ssh-manager MCP（ssh_execute/ssh_execute_background）下发，输出回读语义判定；Phase 间零耦合——只通过知识图谱 JSON 节点/边传递数据，后续 Phase 按节点 ID 反查不重跑收集。

## 3 执行流程：9 阶段（11 段位）

```text
P1a 环境侦察 -> P1b 源码扫描(可选) -> P2 合规检测(226条) -> P3 交叉关联
   -> P4a 模式匹配 -> P4b LLM推理补盲 -> P5 链构建 -> P6 链验证
   -> P7 POC生成 -> P8 报告交付(8a/8b/8c) -> P9 模式进化
```

| Phase | 职责 | 关键机制 |
|---|---|---|
| P1a | 环境建模：指纹（OS/arch/kernel/runtime + env_hash）、集群结构分批收集 | 不审漏洞不跑攻击；env_hash=sha256(k8s+docker+node+pod+sa_count) |
| P1b | 源码层配置风险（Dockerfile/K8s manifest/Helm/CI-CD/.env） | 默认不启用，需 source-path；补运行时侦察盲区 |
| P2 | CIS 全量逐条：K8s 134（4 WU）+ Docker 64（2 WU）+ Containerd 28（1 WU） | 每条 LLM 读 SSH 原始输出语义判定；分批 WU+三重校验 |
| P3 | 三库联动：Phase 2 fail × 侦察交叉比对，产 ATK-CAND | 静态库优先、LLM 动态推理补盲（只标 [?]） |
| P4a | 条件触发表把 [?] 变 [x]：按需加载命中模式 SKILL | 不读全部 49 个；platforms 过滤；L0/L1 探测前置->L2 攻击验证+差分证明 |
| P4b | 漏报最后防线：未匹配/证据不全/盲区候选 | CoT+ReAct 循环（<=10 轮）从零动态推理新路径 |
| P5 | 组合多步链 CHAIN-xxx + 可达性评估 | 如 socket-escape->secret-exfil->lateral-move |
| P6 | 逐链逐步骤终判：前置验证->审批门控攻击->差分证明 | 5 项门槛综合判 C1/C2/C3；被阻断读模式"绕过策略" |
| P7 | confirmed/condition_met 链生成可执行 POC | C3/不可利用/被阻断一律不产；POC 是证据不是武器；每步标注 [L0]/[L1]/[L2] |
| P8 | 8a 平台合规报告+阈值矩阵；8b 每链详情+修复建议；8c 全景 10 章 | 盲区提示 Top3+覆盖矩阵+QA 三层校验+置信度评分+更新情节记忆 |
| P9 | insights 经 4 门槛+用户审批晋升永久模式写入 _learned/ | 纯 Markdown 读写，不执行 SSH；4 级自净+三库一致性检查 |

## 4 15 项设计机制

| # | 机制 | 一句话 |
|---|---|---|
| ① | 攻击者视角 L0-L3 分层 | root 仅做 L0 宿主机只读侦察，攻击验证必须 L1/L2 容器内视角复现，L3 破坏性只理论推导——解决"root 跑攻击证明不了逃逸"的 BAS 通病 |
| ② | 可信度 C1/C2/C3 分级 | 以证据充分度定级：C1 实证复现（5 门槛+L2 差分）/C2 条件实证/C3 风险线索，另有不可利用与已阻断两态 |
| ③ | 三库联动 | 合规 fail 自动反查 CHK-CAND -> 关联 ATK-HYP -> 静态不命中走 LLM 动态推理，把"配置不合规"升级为"满足攻击前置条件" |
| ④ | 模式自我进化 | 4b insights -> 4 门槛 -> 用户审批 -> _learned/ -> 更新三库索引+一致性检查 |
| ⑤ | 全景覆盖报告 | 7 攻击面覆盖矩阵+盲区提示 Top3+不可利用项必入矩阵，从"看运气"变"可度量" |
| ⑥ | 反幻觉 6 条硬约束 + 三层 QA | 不凭记忆出命令/不伪造 SSH 输出（禁"等/大致/约"）/无证据不写确认态/占位符必替换/超审批即停/baseline 永不替代当前 |
| ⑦ | 方法 C 混合渐进 | 原生命令优先 -> 专用工具按需上传+SHA256 校验 -> 失败回退原生命令 -> 会话结束自动清理 |
| ⑧ | 知识图谱解耦 | Phase 间不直接传数据，只经图谱 JSON 节点/边；Secret 节点绝不存内容 |
| ⑨ | 断点续传 | progress.json 状态机每 WU 落盘，崩溃从 results.jsonl 已写行续传 |
| ⑩ | 五态标记闭环 | [x]/[?]/[-]/[!]/[ ] 交付前 [ ] 必消灭；[x][?] 必有编号、[-] 必有证伪依据 |
| ⑪ | 条件触发表按需加载 | 4a 只读命中模式，省 15-20k token |
| ⑫ | 分批 WU + 三重校验 | 每批完成立即校验规则数/判定/依据，不等全部完成才发现错 |
| ⑬ | SSH 限速+重试 | 最大并行 3、批次间隔 2s、单次超时 30s；读重试 3 次、写不重试标 [!] |
| ⑭ | baseline 版本兼容 | 版本一致逐条 diff、不一致降级趋势对比；baseline 永不替代当前结果 |
| ⑮ | 环境指纹+跨会话 | env_hash 记录环境特征，作工具选择依据与 P9 进化过滤条件 |

docs 补充 5 项实现级机制：平台分片并发写保护 / LOOP_POLICY / 强制交互确认 / 套件根 Glob / pipeline_blocked。

## 5 知识图谱（Phase 间唯一数据媒介）

- **节点**：OUTPUT_STANDARD.md 实际定义 8 类节点文件（hosts/pods/containers/services/SA/secrets/findings + source_findings；README 全景图称 7 类——口径差已标注）
- **边 5 类**：infra（宿主->容器包含）/compliance（资产->规则）/cross_ref（跨库关联）/attack（链式攻击）/source（源码->运行时映射）
- **情节记忆**：session_history + recommendations，跨会话累积
- **流转**：10 步 Phase 间图谱流转（每 Phase 产什么节点/边、下游怎么反查）
- **红线**：Secret 节点绝不存内容

## 6 知识资产盘点（实测）

| 资产 | 规模 | 组织 |
|---|---|---|
| 攻击模式库 | **49 个**（AS-1~AS-7 七攻击面） | 49/49 均为 8 段式结构+MITRE 映射；destructive=true 仅 5 个（全名单见下表） |
| 合规规则库 | **226 条**精确核验（K8s 134 / Docker 64 / Containerd 28；41 分组=29+7+5，逐组吻合） | 规则 8 字段 schema |
| 假设库 | **188 条**（CHK-CAND 136 + ATK-HYP 49 + XREF 3） | README 旧口径 35/25 已标不符 |
| 自进化区 | _learned/（P9 晋升产物） | 与三库索引联动 |

模式 SKILL.md 内部结构（抽读 5 个全文样本：socket-escape/k8s-sa-exploit/fork-bomb/cloud-metadata/webhook-backdoor）：frontmatter（platforms/scope/destructive/MITRE）+ 8 段式正文（前置条件/检测/验证/攻击步骤/差分证明/绕过策略/修复建议/参考）。

**49 模式全名单（AS-1~AS-7）**：

| 攻击面 | 模式 |
|---|---|
| AS-1 逃逸（12） | docker.sock 逃逸 · cgroup 逃逸 · procfs 逃逸 · runc 逃逸 · hostPath 挂载 · capability 提权 · containerd-shim 逃逸 · 特权容器逃逸 · hostPID/hostIPC 逃逸 · hostNetwork 滥用 · shareProcessNamespace 滥用 · sysctl 滥用 |
| AS-2 认证授权（14） | K8s SA 滥用 · RBAC 提权 · 匿名访问 · Docker API 认证绕过 · K8s exec 滥用 · containerd ctr 滥用 · Ephemeral Container 注入 · Kubelet API 滥用 · etcd 未授权访问 · etcd 证书窃取 · CSR API 滥用 · 节点身份提权 · TokenRequest API 滥用 · Aggregated APIServer 滥用 |
| AS-3 网络（7） | 横向移动 · 云元数据泄露 · DNS 外发 · NTFS ALPN 协议攻击 · Node Proxy/Port-Forward 滥用 · NetworkPolicy 绕过 · kubectl port-forward 滥用 |
| AS-4 数据泄露（6） | Secret 外发 · 环境变量凭据泄露 · 镜像层敏感信息 · 云提供商凭证窃取 · ConfigMap 数据泄露 · etcd 数据泄露 |
| AS-5 拒绝服务（2） | 资源滥用 · fork 炸弹 |
| AS-6 供应链（2） | 镜像标签篡改 · 仓库投毒 |
| AS-7 持久化（6） | Webhook 后门 · CronJob 持久化 · Docker Volume 持久化 · MutatingWebhook 持久化 · DaemonSet 持久化 · Deployment 镜像覆盖 |

**条件触发表（信号 → 模式，Phase 4a 先读合规+侦察结果再选模式；铁律：不准凭记忆出攻击命令，必须 Read 对应 SKILL.md）代表性映射**：

| 触发信号 | 来源 | 读取模式 |
|---|---|---|
| K8s-7.1.1 privileged=true | 合规 G_7 | socket-escape / capability-privesc / hostpath-mount |
| docker.sock 挂载 | 侦察 | socket-escape |
| /proc/1/cgroup 可见 | 侦察 | cgroup-escape |
| /proc mounted rw | 侦察 | procfs-escape |
| runc 版本 <1.0-rc91 | 合规 | runc-escape |
| containerd-shim socket 可访问 | 侦察 | containerd-shim-escape |
| K8s SA token 可读取 | 侦察 | k8s-sa-exploit |
| K8s RBAC 过宽 / pods/exec 权限 | 合规 G_8/侦察 | k8s-rbac-abuse / k8s-exec-abuse |
| 容器网络无 NetworkPolicy | 合规 G_6 | lateral-move |
| 云元数据可访问 / DNS 可解析外部 | 侦察 | cloud-metadata / dns-exfil |
| Secret 明文环境变量 / 环境变量含凭证 | 侦察/合规 | secret-exfil / env-credential-leak |
| 镜像历史含 Secret / tag 非固定 | 侦察/合规 | image-layer-secret / image-tag-mutation |
| 特权容器+无 pid 限制 | 合规 G_7 | fork-bomb |

## 7 安全机制

- **5 级审批门控**：攻击验证逐级审批（读/探测/L1 验证/L2 差分/破坏性禁止）
- **熔断计数器**：超限即停
- **SSH 限速**：并行 3 / 间隔 2s / 超时 30s；rate limited 自动降级串行
- **反幻觉 6 条硬约束**（见机制⑥）+ QA 三层校验（结构->语义->覆盖）
- **POC 纪律**：只有 C1/C2 链产 POC；POC 是证据不是武器；每步标执行层级

## 8 模式自进化（P9）

晋升流水线：Phase 4b insights.md -> **4 项晋升门槛**评估 -> 用户审批 -> 写入 _learned/ -> 更新三库索引+一致性检查。自净 4 级：hit>=5 升 high / 连续 15 次未命中问用户归档 / 证伪剔除 / 格式重建。

## 9 与探隐 v2 的同构对照

| GenCPT 机制 | 探隐 v2 对应 | 关系 |
|---|---|---|
| 知识图谱解耦（Phase 间唯一媒介） | 13 表 TSV 账本+10 边图谱 | 同构思想，载体不同（JSON vs TSV） |
| 五态标记闭环 [x][?][-][!][ ] | matrix 五态+终态门禁空格消灭 | 几乎逐字同构 |
| 可信度 C1/C2/C3+不可利用+已阻断 | 两维评级 confidence 四态×impact | GenCPT 单维，v2 更细 |
| 断点续传 progress.json | 受管重启+resume_kit | 同构 |
| 模式自进化 4 门槛+用户审批 | 知识飞轮 staging 审批入库 | 同构（v2 多反向验证脱敏） |
| 零 Python 判定脚本 | v1 纯 SKILL 立场；v2 已修订为薄 CLI | **分叉点**：GenCPT 保持零代码，探隐 v2 走确定性 CLI 执法 |
| env_hash 环境指纹 | P0 落账 SKILL 版本+tools.lock 哈希 | 同构（指纹换锚点） |

**接入路径**（v2 批次 3+ 引擎批之后）：容器场景的候选引擎/知识源——49 攻击模式的 8 段式+MITRE 结构可平移为 knowledge/ 先例语料（staging 审批入库），226 合规规则可作 vuln_class 词表扩展源；图谱 schema 对接统一提交 schema（facts/findings/edges 三桶）。

## 10 实测核验与陈旧口径（README 纠偏）

| README 说法 | 实测 | 判定 |
|---|---|---|
| 假设库 35 CHK-CAND / 25 ATK-HYP | 136 / 49 | 陈旧口径 |
| 29 个攻击模式 | 49 | 陈旧 |
| 总文件数 106 | 163 | 陈旧 |
| 7 类图谱节点 | OUTPUT_STANDARD 定义 8 类（含 source_findings） | 口径差，已标注 |
| 60 卡片 | 与实际结构不对应 | 陈旧 |

另 6 条 uncertain 已存档（k8s-sa-exploit 的 T1525 MITRE 映射可疑 / /tmp 工具目录命名不一致 / attack-surface-model.md 停在 25 模式旧口径等）。

## 11 你的 V2 计划评审差距（2026-08-01，外部文档）

评审对象是 GenCPT V2 重写计划（10 份设计/计划文档），结论：整体写作质量高（实现契约到函数体级、三向 Finding 绑定、每任务 5 步 TDD），但存在 **4 处实质写漏 + 3 处边界项**：

1. 【最重要】Wave 2/3/4 的"安装+回滚 smoke"没有落实为任务（仅 Wave 1 完整实现；rollback-manifest 全库仅命中 wave1）——照计划执行则 alpha2/beta1/beta2 的可交付声明无实现证据
2. 威胁模型/安全边界文档缺失（设计规格 §4.4 要求，五波无对应任务）
3. Session 归档/retention 只有命令名没有语义
4. （第 4 项及 3 处边界项详见 docs/design/imported/gencpt/2026-08-01-gencpt-v2-plan-review-gaps.md 原文）

> 差距稿全文已保真收录：docs/design/imported/gencpt/2026-08-01-gencpt-v2-plan-review-gaps.md——若启动 GenCPT V2 重写，先补这四处再动工。
