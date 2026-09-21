# 探隐 GenCPT — 容器与 K8s 渗透测试技能套件（完整定稿）

> **这份是什么**：GenCPT（Gen=生成式 AI + CPT=Container Penetration Test）的专项设计页——容器/K8s 场景的全流程渗透技能套件全景，探隐生态的容器引擎/知识源候选。以 docs/design/imported/gencpt/GenCPT-main/ 当前源码为准（188 文件实测）。
> **怎么读**：§1 定位 → §2 五层架构 → §3 全部 Phase → §4 机制全表 → §5 知识图谱 → §6 知识资产（49 模式全名单+条件触发表）→ §7 安全 → §8 自进化 → §9 工程质量 → §10 与探隐 v2 对照。

## 1 项目定位

| 项 | 值 |
|---|---|
| 一句话 | 基于 LLM 语义驱动的容器与 Kubernetes 渗透测试技能套件：SSH 远程对 K8s/Docker/containerd 执行「合规检测→攻击验证→链式攻击→POC 生成→报告交付」全流程 |
| 运行形态 | 纯 Markdown SKILL 体系（不是代码程序），寄宿 opencode CLI / Claude Code 等 AI 编码代理；SKILL 全中文指令 |
| 组成 | 1 个 Pipeline 入口 SKILL + **17 个子技能** + 6 个共享规范 + supervisor 代理 + 知识库 |
| 执行单元 | 每 Phase 独立子代理（Task general·独立上下文），SSH 命令经 ssh-manager MCP 唯一出口 |
| 产物 | Markdown 报告三份（合规/攻击/全景）+ JSON 知识图谱 + 可视化（graph-viz） |
| 规模实测 | 188 文件 / 17 子技能 / 9+2 Phase 段位 / 49 攻击模式 / 226 合规规则 / 188 假设条目 |

## 2 五层架构

```text
+--------------------------------------------------------------+
| ① 接入层  opencode CLI（用户入口）+ ssh-manager MCP            |
|           -> SSH 远程服务器 -> K8s/Docker/containerd 目标环境  |
+--------------------------------------------------------------+
| ② 编排层  Pipeline 入口 SKILL：参数收集·环境验证·初始化        |
|           progress.json 状态机（Phase 级状态由入口 LLM 统一    |
|           接管——子代理输出经验证才写 complete）                |
|           audit_log.json 审计·并发调度重试·Todo 强制更新       |
+--------------------------------------------------------------+
| ③ 执行层  全部 Phase：P1a/P1b/P2/P3/P4a/P4b/P5/P6.5/P6/P7/    |
|           P8a/P8b/P8c/P8d/P9（见 §3）                         |
+--------------------------------------------------------------+
| ④ 知识库层 knowledge_graph/（Phase 间唯一数据媒介）            |
|           attack-patterns/ 49 模式·compliance-rules/ 226 条   |
|           hypothesis-libraries/ 188 条·_learned/ 自进化区      |
+--------------------------------------------------------------+
| ⑤ 规范层  6 个共享规范（输出标准/证据标准/审批分级/质量模板…） |
+--------------------------------------------------------------+
  贯穿链路 A（基础设施）：ssh-manager MCP -> SSH -> 目标环境
  贯穿链路 B（检测原理）：合规 fail -> 三库联动映射攻击前置
                          -> L0 探测+L1 验证前置 -> L2 差分攻击证明
```

## 3 执行流程：全部 Phase（13 段位）

| Phase | 职责 | 关键机制 |
|---|---|---|
| P1a | 环境建模：指纹（OS/arch/kernel/runtime + env_hash）、集群结构分批收集 | **9 项采集完整性门控**（kubectl 实数 vs jq 采集数逐项比对，≤2 次补采否则 blocked） |
| P1b | 源码层配置风险（Dockerfile/K8s manifest/Helm/CI-CD/.env） | 默认不启用需 source-path；补运行时盲区 |
| P2 | CIS 全量逐条：K8s 134（4 WU）+ Docker 64（2 WU）+ Containerd 28（1 WU） | 每条 LLM 读 SSH 原始输出语义判定；分批 WU+三重校验 |
| P3 | 三库联动：fail × 侦察交叉比对，产 ATK-CAND | 静态库优先、LLM 动态补盲只标 [?]；改名回写 cross_ref |
| P4a | 条件触发表把 [?] 变 [x]：按需加载命中模式 SKILL | 不读全部 49 个；platforms 过滤；L0/L1 探测前置->L2 攻击+差分证明 |
| P4b | 漏报最后防线：未匹配/证据不全/盲区候选 | CoT+ReAct 循环（<=10 轮）动态推理新路径 |
| P5 | 组合多步链 CHAIN-xxx + 可达性评估 | 如 socket-escape->secret-exfil->lateral-move |
| **P6.5** | **对抗性验证（adversary-verify）**：独立子代理对全部 C1 结论做只读 L0/L1 定向证伪 | overturned 则降级 C1->C2 并回写 attack.json——攻击结论也要被挑战 |
| P6 | 逐链逐步骤终判：前置验证->审批门控攻击->差分证明 | 5 项门槛综合判 C1/C2/C3；被阻断读模式"绕过策略" |
| P7 | confirmed/condition_met 链生成可执行 POC | C3/不可利用/被阻断一律不产；POC 是证据不是武器；每步标 [L0]/[L1]/[L2] |
| P8a/b/c | 平台合规报告+阈值矩阵 / 每链详情+修复建议 / 全景 10 章 | QA 三层校验+**覆盖率硬阈值**（226 规则与 49 模式 100%、证据链 >=90%） |
| **P8d** | **可视化（graph-viz）**：知识图谱渲染（生成脚本+Cytoscape） | 派生边写回 _derived.json，不改原始图谱 |
| P9 | insights 经 4 门槛+用户审批晋升永久模式写入 _learned/ | 纯 Markdown 读写不执行 SSH；4 级自净+三库一致性 |

## 4 设计机制全表（15 项核心 + 工程加固）

**核心 15 项**：

| # | 机制 | 一句话 |
|---|---|---|
| ① | 攻击者视角 L0-L3 分层 | root 仅做 L0 宿主机只读侦察，攻击验证必须 L1/L2 容器内视角复现，L3 破坏性只理论推导 |
| ② | 可信度 C1/C2/C3 分级 | 以证据充分度定级：C1 实证复现（5 门槛+L2 差分）/C2 条件实证/C3 风险线索，另有不可利用与已阻断两态 |
| ③ | 三库联动 | 合规 fail 反查 CHK-CAND -> 关联 ATK-HYP -> 静态不命中走 LLM 动态推理 |
| ④ | 模式自我进化 | 4b insights -> 4 门槛 -> 用户审批 -> _learned/ -> 三库索引+一致性检查 |
| ⑤ | 全景覆盖报告 | 7 攻击面覆盖矩阵+盲区提示 Top3+不可利用项必入矩阵 |
| ⑥ | 反幻觉 6 条硬约束+三层 QA | 不凭记忆出命令/不伪造 SSH 输出（禁"等/大致/约"）/无证据不写确认态/占位符必替换/超审批即停/baseline 永不替代当前 |
| ⑦ | 方法 C 混合渐进 | 原生命令优先 -> 专用工具按需上传+SHA256 校验 -> 失败回退 -> 会话结束自动清理 |
| ⑧ | 知识图谱解耦 | Phase 间只经图谱 JSON 节点/边传递；Secret 节点绝不存内容 |
| ⑨ | 断点续传 | progress.json 状态机每 WU 落盘，崩溃续传；**Phase 级 complete 由入口 LLM 验证后统一写入** |
| ⑩ | 五态标记闭环 | [x]/[?]/[-]/[!]/[ ] 交付前 [ ] 必消灭；[x][?] 必有编号、[-] 必有证伪依据 |
| ⑪ | 条件触发表按需加载 | 4a 只读命中模式，省 15-20k token |
| ⑫ | 分批 WU+三重校验 | 每批完成立即校验规则数/判定/依据 |
| ⑬ | SSH 限速+重试 | 最大并行 3、批次间隔 2s、超时 30s；读重试 3 次、写不重试标 [!] |
| ⑭ | baseline 版本兼容 | 版本一致逐条 diff、不一致降级趋势对比；baseline 永不替代当前结果 |
| ⑮ | 环境指纹+跨会话 | env_hash 作工具选择依据与 P9 进化过滤条件 |

**工程加固（现行源码已内置）**：

- **KG 自洽三修复**：attack-pattern/cross-ref/chain-builder/chain-verify 四个写边 Phase 强制「节点存在性校验+补采」（历史 53 条悬空边已修复）；unverified 边 5 类归因；4b 改名回写 cross_ref
- **attack 边结构化**：attrs{} 嵌套，强制字段 7->17（差分证据/审批记录/层级标注等全落边属性）
- **编排收权**：progress.json 主权归入口 LLM + audit_log.json 全程审计 + 并发调度重试 + Todo 强制更新；子代理 L3/L4 审批改就地 question（不再中断等外部输入）
- **token 预算废除**：原「<=500 tokens/<=30k/<=8000」等 11 文件 20 处硬限额全删，改为「详细数据写盘+路径引用」纪律（上限交给写盘，不交给上下文）
- **可视化派生隔离**：graph-viz 派生边只写 _derived.json，原始图谱零污染

## 5 知识图谱

- **节点**：OUTPUT_STANDARD.md 定义 8 类节点文件（hosts/pods/containers/services/SA/secrets/findings + source_findings）
- **边 5 类**：infra（宿主->容器）/compliance（资产->规则）/cross_ref（跨库）/attack（链式攻击）/source（源码->运行时）；attack 边带 attrs{} 17 强制字段
- **情节记忆**：session_history + recommendations 跨会话累积
- **红线**：Secret 节点绝不存内容；派生数据（可视化）与原始图谱分离

## 6 知识资产（实测核验）

| 资产 | 规模 | 说明 |
|---|---|---|
| 攻击模式库 | 49 个（AS-1~AS-7） | 49/49 均为 8 段式+MITRE 映射；destructive=true 仅 5 个 |
| 合规规则库 | 226 条（K8s 134/Docker 64/Containerd 28；41 分组） | 规则 8 字段 schema |
| 假设库 | 188 条（CHK-CAND 136 + ATK-HYP 49 + XREF 3） | README 旧口径 35/25 已核偏 |
| 跨会话命中记录 | _index.md 尾部 29 条（2 个实跑会话） | 模式库实战使用痕迹 |
| 自进化区 | _learned/ | P9 晋升产物，与三库索引联动 |

**49 模式全名单**：

| 攻击面 | 模式 |
|---|---|
| AS-1 逃逸（12） | docker.sock 逃逸 · cgroup 逃逸 · procfs 逃逸 · runc 逃逸 · hostPath 挂载 · capability 提权 · containerd-shim 逃逸 · 特权容器逃逸 · hostPID/hostIPC 逃逸 · hostNetwork 滥用 · shareProcessNamespace 滥用 · sysctl 滥用 |
| AS-2 认证授权（14） | K8s SA 滥用 · RBAC 提权 · 匿名访问 · Docker API 认证绕过 · K8s exec 滥用 · containerd ctr 滥用 · Ephemeral Container 注入 · Kubelet API 滥用 · etcd 未授权访问 · etcd 证书窃取 · CSR API 滥用 · 节点身份提权 · TokenRequest API 滥用 · Aggregated APIServer 滥用 |
| AS-3 网络（7） | 横向移动 · 云元数据泄露 · DNS 外发 · NTFS ALPN 协议攻击 · Node Proxy/Port-Forward 滥用 · NetworkPolicy 绕过 · kubectl port-forward 滥用 |
| AS-4 数据泄露（6） | Secret 外发 · 环境变量凭据泄露 · 镜像层敏感信息 · 云提供商凭证窃取 · ConfigMap 数据泄露 · etcd 数据泄露 |
| AS-5 拒绝服务（2） | 资源滥用 · fork 炸弹 |
| AS-6 供应链（2） | 镜像标签篡改 · 仓库投毒 |
| AS-7 持久化（6） | Webhook 后门 · CronJob 持久化 · Docker Volume 持久化 · MutatingWebhook 持久化 · DaemonSet 持久化 · Deployment 镜像覆盖 |

**条件触发表（信号->模式；铁律：不准凭记忆出攻击命令，必须 Read 对应 SKILL.md）代表性映射**：

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

5 级审批门控（读/探测/L1 验证/L2 差分/破坏性禁止）· 熔断计数器 · SSH 限速（并行 3/间隔 2s/超时 30s，超载自动降级串行）· 反幻觉 6 条硬约束+QA 三层（结构->语义->覆盖，覆盖率硬阈值）· POC 纪律（仅 C1/C2 链产 POC，POC 是证据不是武器，每步标执行层级）· **对抗性验证（P6.5 对自己的 C1 结论做定向证伪）**。

## 8 模式自进化（P9）

insights -> **4 项晋升门槛** -> 用户审批 -> _learned/ -> 三库索引+一致性检查。自净 4 级：hit>=5 升 high / 连续 15 次未命中问用户归档 / 证伪剔除 / 格式重建。

## 9 工程质量与实测核验

- suite_version 自证：本轮源码自带「修复 39 个问题」的工程修复记录（docs/superpowers/plans/）
- 5 个超长 SKILL 拆出 references/ 子目录（15 个），长文指令模块化
- README 陈旧口径已核偏：假设库 35/25->实测 136/49、29 模式->49、106 文件->188、60 卡片口径失效、图谱 7 类->OUTPUT_STANDARD 实际 8 类
- uncertain 存档：k8s-sa-exploit 的 T1525 MITRE 映射可疑 / 工具目录命名不一致等 6 条

## 10 与探隐 v2 的同构对照

| GenCPT 机制 | 探隐 v2 对应 | 关系 |
|---|---|---|
| 知识图谱解耦（Phase 间唯一媒介） | 13 表 TSV 账本+10 边图谱 | 同构思想，载体不同（JSON vs TSV） |
| 五态标记闭环 [x][?][-][!][ ] | matrix 五态+终态门禁空格消灭 | 几乎逐字同构 |
| 可信度 C1/C2/C3+不可利用+已阻断 | 两维评级 confidence 四态×impact | GenCPT 单维，v2 更细 |
| P6.5 对抗性验证 | P4 独立重放门（fresh 子代理盲重放） | 同构：结论必须被独立挑战 |
| 断点续传+编排收权 | 受管重启+resume_kit+单写者 | 同构 |
| 模式自进化 4 门槛+用户审批 | 知识飞轮 staging 审批入库 | 同构（v2 多反向验证脱敏） |
| attack 边 attrs 17 字段 | 边 provenance+timeline 链式哈希 | 同构方向（v2 更强：哈希链） |
| 零 Python 判定（除可视化脚本） | v1 纯 SKILL；v2 修订为薄 CLI | 分叉点 |

**接入路径**：容器场景候选引擎/知识源——49 攻击模式 8 段式+MITRE 可平移为 knowledge/ 先例语料，226 合规规则可作 vuln_class 词表扩展源，KG schema 对接统一提交 schema。

## 11 你的 V2 计划评审差距（2026-08-01，外部文档）

GenCPT V2 重写计划（10 份文档）评审结论：质量高（契约到函数体级、三向 Finding 绑定、每任务 5 步 TDD），但 **4 实质写漏+3 边界项**：Wave 2/3/4 安装+回滚 smoke 无任务落地、威胁模型文档缺失、Session 归档只有命令名等——全文见 docs/design/imported/gencpt/2026-08-01-gencpt-v2-plan-review-gaps.md。若启动重写先补四处再动工。
