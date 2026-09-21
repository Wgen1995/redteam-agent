# GenCPT 检测原理与运作机制详解（外行友好版）

> 这份文档是写给"完全不懂容器安全、也不懂大模型"的人看的。你看完一遍，就能明白 GenCPT 这个工具是怎么把一台运行着 Kubernetes（或 Docker、containerd）的服务器"测出风险来的"。
>
> 写作原则：**先讲清概念，再讲怎么做**。每个专业术语第一次出现时都会用括号解释一遍；每条命令都会说清楚"它做什么、为什么这么做、产物是什么"。所有举例都来自 GenCPT 的真实实现文件（`/root/gencpt/`），不是编的。
>
> 维护人：wanghuigen
> 最近更新：2026-07-04

---

## 目录

1. [一、项目定位——它到底是个什么东西](#一项目定位它到底是个什么东西)
2. [二、基础概念（先看这一节，后面才看得懂）](#二基础概念先看这一节后面才看得懂)
3. [三、架构全景图——9 个 Phase 怎么串起来](#三架构全景图9-个-phase-怎么串起来)
4. [四、执行流程——每个 Phase 具体怎么干](#四执行流程每个-phase-具体怎么干)
5. [五、关键机制详解——九个核心机制](#五关键机制详解九个核心机制)
6. [六、反幻觉核心机制——为什么大模型会编造漏洞](#六反幻觉核心机制为什么大模型会编造漏洞)
7. [七、设计哲学——为什么这么设计](#七设计哲学为什么这么设计)
8. [八、与其它工具对比](#八与其它工具对比)
9. [九、Q&A 常见疑问 + 术语表](#九qa-常见疑问--术语表)

---

## 一、项目定位——它到底是个什么东西

### 1.1 什么是"容器渗透测试"

先讲最基础的概念。当下大多数互联网应用都不是直接跑在一台物理服务器上，而是被装进一个个"容器"（container，可以理解成一个轻量级的隔离盒子，里面跑着应用程序）里运行。管理这些容器的系统叫 **Kubernetes**（常缩写为 K8s，谷歌开源的容器编排平台），另外还有 **Docker**（最早的容器引擎，也是最广为人知的容器运行时）和 **containerd**（Docker 的下一代替代品，更轻量）。

把应用装进容器，隔离了进程、网络、文件系统——本来是为了"安全"。但容器本身不是铁桶，它和宿主机（host，跑着容器的那台物理机或虚拟机）之间有大量接口（docker.sock 套接字、/proc 文件系统、capability 权限位……）。一旦配置有疏漏，容器里的攻击者就能"逃"出去拿到宿主机权限，这就叫**容器逃逸**（container escape）——容器安全里最可怕的事故。

**容器渗透测试**（container penetration test）就是模拟攻击者，对一套运行中的 K8s/Docker/containerd 环境发起授权攻击，把配置漏洞、逃逸路径、提权手法、横向移动（lateral movement，从一个容器跳到另一个容器或宿主机）的可能路径一条条找出来，证明"这环境真要被人打了会出什么事"。

### 1.2 传统渗透工具有什么问题

市面上已有不少容器安全工具，分两大类：

- **合规扫描器**（compliance scanner）：比如 kube-bench、docker-bench-security。它们的工作方式是照着 **CIS Benchmark**（一种业界公认的安全配置基线，后面会详讲）对照检查几百条规则，"文件权限 600 没有？没有就 fail"。这种工具只能告诉你"哪条配置不符合基线"，但**证明不了这条违规到底能不能被利用**——比如"特权容器（privileged=true）"在 CIS 里是 fail，但攻击者要真利用它逃逸，还得看宿主机有没有 docker.sock、有没有 AppArmor 拦着、有没有 capability 限制……扫描器答不出来。
- **BAS 工具**（Breach and Attack Simulation，入侵与攻击模拟）：比如 Atomic Red Team、kube-attack。它们直接在目标环境里跑预写的攻击脚本——"拿到 root 就 nsenter 进宿主机、就 docker run 挂宿主机根盘"。问题是：**脚本拿到 root 成功了，只代表宿主机有 root 能干啥，不代表容器内的攻击者也能干这事**。容器渗透的核心是"容器内的低权限视角能干啥"，但 BAS 往往直接拿宿主机 root 跑，得出的结论是宿主机能被干爆——这种结论甲方听了也只能摇头，因为甲方早就知道宿主机 root 啥都能干。

总结一句：**合规扫描器证明了"配置不合规"，BAS 证明了"宿主机 root 能干啥"，但两者都证明不了"容器内攻击者能不能真的逃出来"**。

### 1.3 大模型（LLM）能做什么

**LLM**（Large Language Model，大语言模型）就是能读懂人类语言和命令的 AI。它的优势是能读懂配置文件的**语义**——它看 `privileged: true` 不只是看到一个布尔值，而是能理解"这个容器拥有宿主机几乎全部权限"，进而能串联"特权 + docker.sock 挂载 + 无 AppArmor"这种多因素组合，判断"这套组合下来攻击者能从容器内 docker run 逃逸到宿主机读 /etc/shadow"。

但 LLM 也有致命弱点：它会**幻觉**（hallucination）——也就是一本正经地编造不存在的东西。比如它可能"觉得"某台机器上 docker.sock 是可写的，硬说"攻击者能逃逸"，但实跑 SSH 命令一看根本不可写。如果没有约束，LLM 会产出一堆假攻击报告，甲方一复核全垮。

### 1.4 GenCPT 解决什么问题

**GenCPT** = **Gen**（生成式 AI）+ **CPT**（Container Penetration Test，容器渗透测试）。它是一款用 **LLM 语义驱动**的容器渗透测试工具（在 opencode 里叫 SKILL 套件，SKILL 就是"技能"，是一段给 AI 看的指令文本）。它的代码和文档全部位于 `/root/gencpt/`。

它的核心思路是：**用 LLM 的语义理解能力去补 BAS/扫描器的盲区——既证明配置不合规（合规扫描器能做的），又证明攻击者从容器内真能逃出来（BAS 干不好的）；同时用一整套纪律约束去压住 LLM 的幻觉**。

具体做法是把一次渗透测试拆成 **9 个 Phase**（Phase，也就是 9 步流水线），每一步都通过 SSH 远程执行真实命令产出可查证的证据，每个攻击候选都必须经过"5 级审批门控 + 差分证明 + 5 项验收门槛"才能最终判定 C1（实证复现）。

**它不是什么**：

- 不是 kube-bench 那种纯脚本扫描器（虽然有 226 条 CIS 合规规则，但每条规则的判定由 LLM 读 SSH 原始输出后做语义判断，不是字符串匹配）。
- 不是 BAS 那种拿到 root 就跑预写脚本（攻击的每一步都从容器内用 `kubectl exec` 模拟容器内攻击者视角，root 仅用于 L0 宿主机侦察）。
- **零 Python 脚本做分析判定**——脚本只用来做杂活（`jq` 查 JSON、`wc -l` 统计行数、`mkdir` 建目录），漏洞判定 100% 由 LLM 语义产出。

**它解决的 5 个核心问题**：

1. **root 跑攻击证明不了逃逸** → 用"执行上下文分层 L0-L3"，root 只做 L0 宿主机侦察，攻击用 L1/L2 容器内视角复现（行业首创，详见 §5.1）。
2. **传统高/中/低危分级没信息量** → 用"可信度 C1/C2/C3"分级，由证据决定而非位置决定，甲方知道哪些立刻能打（§5.2）。
3. **合规扫描只发现配置不合规，证明不了能利用** → 用"三库联动"，从合规 fail 自动触发攻击假设映射，再到攻击验证层层证明（§5.3）。
4. **LLM 幻觉满天飞** → 用"反幻觉 6 条硬约束 + 三层 QA 校验 + 安全熔断 + 差分证明强制"四重压住（§5.6 / §6）。
5. **攻击模式库跟不上攻防态势** → 用"模式自我进化"，Phase 9 把 LLM 推理发现经 4 门槛 + 用户审批晋升为永久模式（§5.4）。

### 1.5 运行环境

GenCPT 在 **opencode CLI**（一个 AI 编程助手命令行工具）或兼容的 AI 助手（Claude Code、Cursor）里运行。它靠这些工具提供的 SSH 能力远程对目标服务器下命令——具体来说是通过一个叫 **ssh-manager MCP**（MCP，Model Context Protocol，是给 AI 提供外部工具的协议；ssh-manager 是其中一个插件，封装了 `ssh_execute`、`ssh_execute_sudo`、`ssh_upload` 等工具）的工具集。

GenCPT 自身不是程序，是**一堆 Markdown 文件**——一个 Pipeline 入口 SKILL.md（`/root/gencpt/SKILL.md`）+ 15 个子技能 SKILL.md（在 `/root/gencpt/skills/` 下）+ 知识库（攻击模式、合规规则、假设库）+ 共享规范。LLM 读了这些 Markdown 指令，照着执行。

---

## 二、基础概念（先看这一节，后面才看得懂）

后面讲每个 Phase 时，会反复用到一批术语。这一节先把它们讲清楚，后面就不卡壳了。

### 2.1 容器逃逸——攻击者最想干的事

**容器逃逸**（container escape）是指攻击者从容器内部突破隔离，拿到宿主机权限的过程。可以想象成：容器是一间玻璃房，攻击者被关在里面只能动自己房间的家具；逃逸就是想方设法砸穿玻璃、控制整个大楼。

逃逸的常见手法（GenCPT 攻击模式库 `/root/gencpt/attack-patterns/escape/` 覆盖 12 种）：

- **docker.sock 挂载逃逸**：容器里挂了宿主机的 `/var/run/docker.sock`（Docker 守护进程的 socket 文件），攻击者在容器内调 docker API → `docker run -v /:/host alpine` → 在新容器里挂宿主机根盘 → 读 `/etc/shadow` 改 `/etc/crontab`。对应模式 `escape/socket-escape`。
- **特权容器逃逸**：`securityContext.privileged: true` 的容器拥有几乎所有宿主机能力（capability），可直接 `nsenter` 进入宿主机命名空间、`mount /dev/sda1` 挂宿主机根盘。对应模式 `escape/privileged-container-escape`。
- **capability 提权**：容器被给了 `CAP_SYS_ADMIN`、`CAP_SYS_PTRACE` 等危险 capability，能做 mknod、ptrace 等敏感操作。对应模式 `escape/capability-privesc`。
- **cgroup 逃逸**：通过 `/sys/fs/cgroup` 可写做 release_agent 触发宿主机命令。对应 `escape/cgroup-escape`。
- **procfs 逃逸**：`/proc` 被 rw 挂载，可读宿主机进程信息。对应 `escape/procfs-escape`。
- **runc 逃逸**：runc 版本 <1.0-rc91 有已知 CVE，可逃逸。对应 `escape/runc-escape`。
- **hostPath 挂载**：Pod 的 volume 挂了 `/etc`、`/` 等宿主机敏感路径。对应 `escape/hostpath-mount`。

为什么可怕？因为一旦逃逸成功，攻击者就拿到的不是"一个容器"的控制权，而是**整台宿主机**的控制权——而这台宿主机上还跑着其他租户的几十上百个容器，全部沦陷。

### 2.2 合规检测——CIS Benchmark 是什么，为什么 226 条

**合规**（compliance）就是"配置符合业界安全基线"。容器安全圈公认的基线叫 **CIS Benchmark**（CIS = Center for Internet Security，互联网安全中心，一个非营利组织），它把"什么样的容器配置算安全"写成一条条可检查的规则。

GenCPT 的合规规则库在 `/root/gencpt/compliance-rules/`，覆盖三大平台共 **226 条**规则：

| 平台 | 规则数 | 分组数 | Benchmark 版本 |
|------|--------|--------|---------------|
| Kubernetes | 134 | 29 | CIS Kubernetes Benchmark v1.8.0 |
| Docker | 64 | 7 | CIS Docker Benchmark v1.6.0 |
| Containerd | 28 | 5 | CIS Containerd Benchmark |
| **合计** | **226** | **41** | — |

每条规则包含：编号、描述、检查命令（标注 L0/L1 执行层级）、期望值、判定标准（pass/fail/warn/na）、修复建议、CIS 映射、攻击面关联。比如 `/root/gencpt/compliance-rules/kubernetes/G_7_1_pod_security.md` 里的 K8s-5.2.1 规则就是检查"是否启用了 privileged"，期望值是"不应有 privileged=true 的 Pod"。

为什么这么细分？因为容器栈涉及 API Server、etcd、Kubelet、Pod、RBAC、网络策略等十余个组件，每个组件都有自己的安全配置点，226 条规则就是把这些"应该检查的配置项"穷尽列出来。漏掉一条就可能漏一个攻击面。

### 2.3 攻击模式——什么是攻击模式，8 段格式

**攻击模式**（attack pattern）就是"一种已知攻击手法的模板"。GenCPT 的攻击模式库在 `/root/gencpt/attack-patterns/`，共 **49 个模式 / 7 大攻击面**：

| 攻击面 | 模式数 | 代表模式 |
|--------|--------|---------|
| AS-1 逃逸 | 12 | socket-escape、capability-privesc、hostpath-mount、privileged-container-escape… |
| AS-2 认证授权 | 14 | k8s-sa-exploit、k8s-rbac-abuse、k8s-anonymous-access、docker-api-auth… |
| AS-3 网络 | 7 | lateral-move、cloud-metadata、dns-exfil、ntfs-alpn、networkpolicy-bypass… |
| AS-4 数据泄露 | 6 | secret-exfil、env-credential-leak、image-layer-secret、configmap-data-exposure… |
| AS-5 拒绝服务 | 2 | resource-abuse、fork-bomb |
| AS-6 供应链 | 2 | image-tag-mutation、registry-poison |
| AS-7 持久化 | 6 | webhook-backdoor、cronjob-persist、daemonset-persist、deployment-image-override… |

每种攻击模式用一个 SKILL.md 文件描述，采用 **8 段格式**（每段都是必填的）：

1. **前置条件**（如"docker.sock 在容器内可见且可写"）
2. **探测命令**（如 `ls -l /var/run/docker.sock`，标注 L0/L1）
3. **攻击验证**（如 `docker run -v /:/host alpine ls /host/etc/shadow`，标注 L2）
4. **差分证明**（攻击前后状态对比）
5. **绕过策略**（如"AppArmor 阻断时怎么办"）
6. **证伪条件**（如"socket 不可写则证明不可逃逸"）
7. **审批级别**（这个模式验证需要 L3/L4 哪级审批）
8. **MITRE ATT&CK 映射**（业界攻击技术编号，详见 https://attack.mitre.org/）

这 49 个模式外加条件触发读取表，存放在 `/root/gencpt/attack-patterns/_index.md`。Phase 4a 启动时先读 `_index.md` 的条件触发表，根据合规 fail 和侦察发现按"触发信号 → 需读模式"映射**按需加载**对应的模式文件（不一次性读全部 49 个，省 token）。

### 2.4 假设库和三库联动——从发现问题到证明问题

光有合规规则和攻击模式还不够，要把二者"咬合"起来——一条合规 fail 规则到底对应哪条攻击前置条件？这就靠**假设库**（hypothesis library）。GenCPT 有三个假设库，存放在 `/root/gencpt/hypothesis-libraries/`：

| 库 | 卡片数 | 内容 | 触发方式 |
|----|--------|------|---------|
| **CHK-CAND**（合规假设库） | 35 张 | G1-G7 每组合规违规 × 攻击假设的映射卡片 | Phase 3 拿合规 fail 反查 |
| **ATK-HYP**（攻击假设库） | 25 张 | 注入/逃逸/访问控制/信息泄露/数据/供应链/持久化 7 类攻击假设 | Phase 3 拿 sink_type+entry+authz 触发 |
| **XREF**（交叉查询） | 3 条 | 叠加/组链/盲区查询模板 | 静态库全不命中时走 XREF-001 LLM 动态推理 |

**三库联动**（three-library linkage）就是：合规 fail 规则 → 反查 CHK-CAND 卡片 → 关联到 ATK-HYP 攻击假设 → 若静态库全不命中 → 走 XREF-001 让 LLM 动态语义推理补充映射。通过这个机制，"配置不合规（合规扫描器能做的）"自动升级为"这条违规满足这个攻击的前置条件（合规扫描器做不到）"——也就是从**发现问题**到**证明问题**。

### 2.5 执行上下文分层 L0-L3——行业首创

这是 GenCPT 最关键的设计，也是它区别于所有 BAS 工具的根本。所有 SSH 远程执行的命令，必须标注执行层级（在 `/root/gencpt/skills/shared/SSH_COMMANDS.md` 里强制规定）：

| 层级 | 名称 | 执行方式 | 用途 |
|------|------|---------|------|
| **L0** | 宿主机观察 | `ssh_execute` 在宿主机直接执行（可用 sudo） | 侦察环境、收集配置、做差分对比的基线/后快照 |
| **L1** | 容器内观察 | `ssh_execute` + `kubectl exec <pod> -- <cmd>` | 验证容器内攻击者视角能看到什么（容器内进程权限） |
| **L2** | 容器内攻击验证 | `ssh_execute` + `kubectl exec <pod> -- <attack_cmd>` + 差分框架 | 在容器内执行攻击命令，前后对比证明 |
| **L3** | 条件验证 | 不执行破坏性命令，理论推导 | DoS、删根目录等不可安全复现的操作，标 ⚠️ |

**为什么必须这么分？** 因为容器渗透的核心命题是"**容器内的攻击者能不能逃出来**"。如果直接拿宿主机 root 跑攻击脚本（BAS 的典型做法），即使成功也只能证明"宿主机 root 神通广大"——但这没价值，甲方早就知道宿主机 root 啥都能干。真正的攻击者通常一开始只有容器内的低权限（比如一个被攻破的 Web 应用的容器），必须从容器内视角出发才能证明逃逸真的成立。

所以 GenCPT 强制：**root 仅用于 L0 宿主机侦察，攻击验证必须用 L1/L2 容器内视角复现**。如 `/root/gencpt/skills/attack-pattern/SKILL.md` 步骤 2.2 写明："L0/L1 命令：直接 ssh_execute；L2 命令：必须先获得 approval，然后 ssh_execute；L3 步骤：标注 ⚠️，只做条件组合分析，不实际执行破坏性操作"。

### 2.6 可信度 C1/C2/C3——替代高危中危低危

传统漏洞分级是"高危/中危/低危"，按漏洞类型决定——SQL 注入一律算高危、XSS 一律算低危。但容器渗透里同一个"特权容器"配置，看实际环境差异巨大：环境 A 有 AppArmor 拦着就不算高危，环境 B 没任何防护能直接逃逸就是高危。所以 GenCPT 改用按**证据充分度**分级：

| 等级 | 名称 | 条件 | 报告标注 |
|------|------|------|---------|
| **C1** | 实证复现 | 5 项门槛全满足 + L2 差分证明充分 | ✅✅ confirmed |
| **C2** | 条件实证 | 前置条件满足 + 理论链路完整，但被阻断或不可安全复现 | ✅ condition_met |
| **C3** | 风险线索 | 配置有隐患 + 前置条件不完全满足 | ⚠️ high_risk_clue |
| 不可利用 | ➖ | 前置条件不满足（证伪） | ➖ disproved |
| 已阻断 | 🛑 | 被安全机制阻断 | 🛑 blocked |

**5 项确认门槛**（C1 必须全满足）：①前置条件可复现 ②可执行 ③可区分（差分可观测） ④影响可观测 ⑤可恢复（有清理命令）。

**关键规则**：可信度由**证据**决定，不由**执行位置**决定。比如一个 C1 漏洞必须真的在 L2 跑通了攻击、攻击前后有可观测差异、有清理步骤——不是"我觉得这个逃逸能成立"。这给了甲方真正可决策的分级：C1 一发现立刻修，C2 排期修，C3 记风险。

### 2.7 五态标记闭环——质量门禁

所有发现项必须用**五态标记**（five-state mark）之一标注，不允许留空 `[ ]`（未检查必须消灭）：

| 标记 | 含义 | 合规语义 | 攻击语义 |
|------|------|---------|---------|
| `[x]` | 已确认 | fail（违规确认） | confirmed（攻击成功） |
| `[?]` | 疑似 | 可疑发现，需 Phase 4b 深审 | 可疑面，需深审 |
| `[-]` | 不适用 | na / pass（通过） | disproved（已证伪） |
| `[!]` | 环境干扰 | 命令执行失败 | 被安全机制阻断 |
| `[ ]` | 未检查 | 过程态，必须消灭 | 过程态，必须消灭 |

这个机制的意义是：**最终交付前所有 `[ ]` 必须转换为其他四态**，且每个 `[x]/[?]` 必须有 ATK-CAND 编号、每个 `[-]` 必须写证伪依据、每个 `[!]` 必须写阻断机制。这样甲方不会困惑"这条到底查了没查"，QA 也能用脚本扫残留 `[ ]` 强制报告拒收。

### 2.8 知识图谱——检测过程的"记忆库"

检测过程产生大量结构化数据（找到了哪些主机/Pod/容器/SA、哪些合规 fail、哪些攻击候选、它们之间什么关系）。这些数据以 JSON 文件形式存成一份**知识图谱**（knowledge graph），存放在 session 目录的 `knowledge_graph/` 下：

**7 类节点**（`knowledge_graph/nodes/`）：
- `hosts.json` — 主机节点（hostname、os、kernel、runtime）
- `pods.json` — Pod 节点（name、namespace、security_context、SA）
- `containers.json` — 容器节点（image、Privileged、CapAdd、Binds 等）
- `services.json` — Service 节点
- `service_accounts.json` — ServiceAccount 节点（automount_token、secrets）
- `secrets.json` — Secret 节点（**仅名称+类型，绝不存储 Secret 内容**——这是硬约束）
- `findings.json` — 发现节点（合规 fail 等）

**5 类边**（`knowledge_graph/edges/`）：
- `infra.json` — 基础设施关系（runs_on / uses_sa / mounts / exposes / host_path_mount / container_in）
- `compliance.json` — 合规边（host → finding）
- `cross_ref.json` — 交叉关联边（finding → 攻击假设）
- `attack.json` — 攻击边（含 verification_level 和 context）
- `attack_chain.json` — 攻击链边

后续每个 Phase 不用重新跑 SSH 收集数据，而是按节点 ID 反查知识图谱。这样既省 SSH 调用，又保证前后 Phase 看到的是同一份数据。

### 2.9 反幻觉 6 条硬约束——给大模型定的"纪律"

前面说过 LLM 会幻觉。GenCPT 每个 Phase 的 SKILL.md 里都强制写入 6 条反幻觉规则（详见 `skills/shared/SSH_COMMANDS.md`、`skills/k8s-compliance/SKILL.md` 等所有 Phase 的"反幻觉机制"章节）：

1. **不准凭记忆出攻击命令**——必须 Read 攻击模式 SKILL.md 后才执行探测
2. **不准伪造 SSH 输出**——每条判定必须附原始命令输出，省略词零容忍（禁用"等/.../大概/约"）
3. **无证据不写确认态**——`[x]` 必须有差分证明，`[?]` 需标待验证原因
4. **占位符必须替换**——报告模板 `{{}}` 必须替换为实际数据
5. **超出审批立即停**——L5 操作不生成执行命令，超时降级为理论验证
6. **baseline 永不替代当前测试**——baseline 报告仅用于 diff 对比，当前结果始终权威

这 6 条是底线纪律，违反任一条对应 WU 的 `status` 置为 `failed`，由 supervisory-agent 决定重试或降级。

### 2.10 5 级审批门控 + 安全熔断——攻击行为的安全网

容器渗透里有些操作是有破坏性的（比如 fork bomb 会真把宿主机搞挂、escape 验证可能产生残留容器）。所以 GenCPT 设了 **5 级审批门控**（在 `skills/chain-verify/SKILL.md` 定义）：

| 级别 | 操作类型 | auto 模式 | manual 模式 | 超时处理 |
|------|---------|----------|------------|---------|
| L1 | 只读检测（ls/cat/find/kubectl get） | 自动通过 | 自动通过 | 无 |
| L2 | 非破坏性攻击验证（curl/nc/kubectl auth can-i） | 自动通过 | 标准 approval | 5 分钟降级理论 |
| L3 | 破坏性攻击验证（docker run 临时容器） | 自动通过 | 快速 approval | 5 分钟降级理论 |
| L4 | 逃逸验证（nsenter/chroot/cgroup） | 自动通过 | question 确认 | 5 分钟降级理论 |
| L5 | 不可安全复现（DoS/删根目录） | question 确认 | question 确认 | 10 分钟降级理论 |

**安全熔断机制**（兜底防护）：auto 模式下若 10 分钟内 ≥5 次 L3/L4 被自动通过，触发熔断——下一个 L4 强制要求 manual approval。这是为了防 LLM 幻觉导致连续自动审批高破坏性命令。熔断事件记入 `evidence/qa/circuit_breaker_event.md`，含时间戳、触发时计数、操作列表。

### 2.11 SKILL.md——给 AI 看的"操作说明书"

GenCPT 的核心载体不是程序代码，是一堆 Markdown 文件——每个文件叫 **SKILL.md**，里面是一段指令文本，告诉 LLM"这个阶段做什么、按什么顺序做、产物写成什么格式"。LLM 读了这段指令，照着执行。

GenCPT 共有：
- 1 个 **Pipeline 入口 SKILL**（`/root/gencpt/SKILL.md`）——负责参数收集、环境验证、初始化、按顺序调度各 Phase
- 15 个 **Phase 子技能 SKILL**（`/root/gencpt/skills/{phase}/SKILL.md`）——每个对应一个具体检测阶段
- 5 个 **共享规范**（`/root/gencpt/skills/shared/`）——SSH_COMMANDS / SEVERITY_RATING / VULNERABILITY_GROUPING / QA_OVERRIDE_TRACKING / OUTPUT_STANDARD，被各个 Phase 反复引用

---

## 三、架构全景图——9 个 Phase 怎么串起来

### 3.1 整体流水线

把 9 个 Phase 按执行顺序画出来，就是这样一条流水线（→ 表示先后执行）：

```
Phase 1a  环境侦察           （必跑）SSH 收集集群结构/Pod/SA/Secret，建知识图谱 7 节点
   ↓
Phase 1b  源码扫描           （可选）扫描 Dockerfile/K8s manifest/CI-CD 配置（≤8000 tokens）
   ↓
Phase 2   合规检测           （必跑）K8s 134 + Docker 64 + Containerd 28 = 226 条 CIS 规则分批跑
   ↓
Phase 3   交叉关联           （必跑）三库联动把合规 fail 映射到攻击假设，+ LLM 动态推理
   ↓
Phase 4a  模式匹配           （必跑）按条件触发表按需加载攻击模式，L0/L1/L2 分层验证
   ↓
Phase 4b  LLM 推理补盲       （必跑）对模式库未覆盖的盲区候选 LLM 推理，产 insights
   ↓
Phase 5   链构建             （必跑）把多个 ATK-CAND 串成 CHAIN-xxx 多步利用链
   ↓
Phase 6   链验证             ★（必跑）5 级审批门控 + 差分证明，判定 C1/C2/C3
   ↓
Phase 7   POC 生成          （必跑）对 confirmed/condition_met 链生成可执行 POC 脚本
   ↓
Phase 8   报告交付           ★（必跑）合规+攻击+全景 10 章 + QA 三层校验
   ↓
Phase 9   模式进化           （可选 --evolve）4 项门槛 + 用户审批 + 自净
```

注：Phase 1a/1b 是侦察阶段，Phase 2 拆成 2a/2b/2c（对应 K8s/Docker/Containerd 三个平台可并行），Phase 4 拆成 4a/4b（模式匹配 ↔ LLM 推理），Phase 8 拆成 8a/8b/8c（合规报告 / 攻击报告 / 全景报告），所以技术上有 13 个调度单元。文档里为方便理解仍说"9 个 Phase"。

带 ★ 的两个 Phase 最关键：Phase 6 是"最终判定关卡"（决定一条链到底是 C1 还是 C2 还是 C3），Phase 8c 是"最终交付关卡"（汇总所有结果 + 三层 QA 校验）。

### 3.2 5 层架构

GenCPT 整体分 5 层（详见 `/root/gencpt/README.md` 的系统全景图）：

1. **接入层**：opencode CLI + ssh-manager MCP → SSH 远程目标环境
2. **编排层**：Pipeline 入口 SKILL.md 收集参数、初始化、按 progress.json 断点续传
3. **执行层**：15 个 Phase 子技能按序执行，Phase 间通过知识图谱传数据
4. **知识库层**：攻击模式库（49 模式）+ 合规规则库（226 条）+ 假设库（185 张卡片）
5. **规范层**：5 个共享规范（OUTPUT_STANDARD / SEVERITY_RATING / VULNERABILITY_GROUPING / SSH_COMMANDS / QA_OVERRIDE_TRACKING）

### 3.3 产物存哪里

检测的所有产物都存在一个 session 目录里（session 就是"一次渗透测试会话"）。路径形如 `/tmp/gencpt-{session_id}/`，目录结构（见 `/root/gencpt/SKILL.md` 第 152 行）：

```
/tmp/gencpt-{session_id}/
├── session_config.json          # 这次的参数 + env_fingerprint + suite_version
├── progress.json                # 每个 Phase/WU 的完成状态（断点续传）
├── audit_log.json               # 每条审计记录
├── evidence/
│   ├── recon/                   # Phase 1a 侦察原始数据（raw/、summaries/）
│   ├── compliance/              # Phase 2 合规结果
│   │   ├── k8s/raw/
│   │   ├── docker/raw/
│   │   └── containerd/raw/
│   ├── cross-ref/               # Phase 3 交叉关联分析
│   ├── attack/                  # Phase 4a/4b 攻击验证证据
│   ├── chains/                  # Phase 5/6 链验证记录
│   ├── poc/poc_scripts/         # Phase 7 可执行 POC
│   ├── evolve/                  # Phase 9 进化报告
│   └── qa/                      # QA 校验记录
├── reports/
│   ├── compliance/              # 合规报告
│   ├── attack/                  # 攻击报告
│   ├── summary/                 # 全景综合报告
│   └── panorama/                # 攻击面覆盖矩阵
├── knowledge_graph/
│   ├── nodes/                   # 7 类节点 JSON
│   └── edges/                   # 5 类边 JSON
└── tmp/
```

### 3.4 每个 Phase 触发时的调用闭环

每当执行一个 Phase 时，LLM 会经历：

1. **读取共享规范**：按需加载 `skills/shared/` 里的相关规则
2. **读取知识库**：按需加载对应规则文件（如 Phase 4a 读 `attack-patterns/_index.md` + 命中模式）
3. **启动子代理执行**：通过 Task(general) 调起一个隔离的子代理（独立上下文窗口，互不干扰）
4. **子代理用 ssh-manager MCP 跑命令**：把 SSH 原始输出立即写盘到 `evidence/.../raw/`，不累积在上下文
5. **LLM 语义判定 + 写知识图谱**：判定结果写成 JSON 节点/边存到 `knowledge_graph/`
6. **更新 progress.json**：标记该 WU 为 complete

这个"每 Phase 产证据、写图谱、后续 Phase 查图谱"的闭环，保证了整个过程可追溯、可复现。

---

## 四、执行流程——每个 Phase 具体怎么干

这一节逐个讲 9 个 Phase。每个 Phase 先说"它干什么、检测什么"，再说"具体怎么做"（保留实际命令并讲清原因），最后用 GenCPT 实际实现的代码和示例数据说明。

---

### Phase 1a — 环境侦察（recon）

#### 这个阶段在干什么

Phase 1a **不审漏洞，也不跑攻击**，它只做一件事：给整个目标环境"建模"——有哪些主机、跑了哪些 Pod、用了哪些 ServiceAccount、挂了哪些 Secret、安全上下文（securityContext）长什么样。想象你要审一栋大楼的安全，得先拿到大楼图纸——有几层、每个房间在哪、哪些门能从外面进。Phase 1a 就是画这张图纸。

产物是知识图谱的 7 类节点 + infra 关系边，是后续所有 Phase 的数据基础。所有 Phase 2 合规检测、Phase 4a 攻击验证都从这图谱里查节点。

#### 怎么做（4 步骤，命令均来自 `/root/gencpt/skills/recon/SKILL.md`）

**步骤 ① 环境指纹识别**：分批执行 SSH 命令（每批 5-7 条，间隔 2 秒）。

```bash
[L0] uname -m                        # 架构
[L0] cat /etc/os-release              # 发行版
[L0] uname -r                         # 内核版本
[L0] hostname                          # 主机名
# scope 含 k8s 时：
[L0] kubectl version -o yaml           # K8s 版本
[L0] kubectl cluster-info              # 集群端点
# scope 含 docker 时：
[L0] docker version
[L0] docker info
# scope 含 containerd 时：
[L0] crictl --version
[L0] containerd --version
[L0] runc --version
```

为什么每条命令前面都标 `[L0]`？因为这是宿主机观察层操作——直接在 SSH 远程服务器上跑，可用 sudo。后续 L1/L2 操作就是进入容器内的，权限模型完全不同。

每条命令的输出**立即写盘**到 `evidence/recon/raw/`（不在上下文累积），文件按 SSH_COMMANDS.md §7.1 标注五元组（命令、来源、输出、时间戳、备注）。这就是反幻觉第 2 条——不准伪造 SSH 输出，必原始记录。

最后生成 `env_fingerprint`，包括 OS / arch / kernel / runtime 版本，写入 `session_config.json`，并算 `env_hash = sha256(k8s_version + docker_version + node_count + pod_count + sa_count)`——这个 hash 后面 Phase 9 模式进化时用作"跨环境命中"判断依据。

**步骤 ② 集群结构收集**：按 scope 分批拉取集群结构信息。

K8s 的批次（注意大集群 300+ Pod 时按 namespace 分批，每批 100 Pod）：

```bash
# 批次 1：节点和服务
[L0] kubectl get nodes -o wide
[L0] kubectl get services --all-namespaces -o wide

# 批次 2：Pod（大集群按 namespace 拉单 namespace）
[L0] kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'
[L0] kubectl get pods -n <ns> -o json

# 批次 3：RBAC 和准入控制
[L0] kubectl get serviceaccounts --all-namespaces
[L0] kubectl get secrets --all-namespaces          # 仅名称+类型，绝不存内容
[L0] kubectl get networkpolicies --all-namespaces
[L0] kubectl get roles,clusterroles --all-namespaces
[L0] kubectl get validatingwebhookconfigurations

# 批次 4：Pod 安全标准
[L0] kubectl get namespaces --labels pod-security.kubernetes.io/enforce

# Worker 节点 SSH 可达性验证（从 master ssh 到 worker）
[L0] ssh <worker_ip> echo OK
```

为什么要按 namespace 分批？因为大集群全量拉 Pod 可能拉出几千条 JSON，单次全量输出会触发"会话压缩"（LLM 上下文窗口溢出后系统自动压缩历史消息，但压缩会丢数据）。所以每个 namespace 一个 WU（Work Unit，工作单元），WU 完成立即落盘，再放下一个。

Worker 节点 SSH 可达性验证是 Phase 1a 独有的——从 master 节点 `ssh <worker_ip> echo OK` 看能不能跳过去。可达的写入 `session_config.json.env_fingerprint.worker_nodes`，不可达的标 `ssh_unreachable`。后面 Phase 2 的节点级规则就要靠这个清单到 worker 上跑本地文件检查。

**步骤 ③ 安全上下文提取**：从 raw 输出里提取安全相关字段写入知识图谱节点。

举例（`/root/gencpt/skills/recon/SKILL.md` 第 200 行样本）：

```json
{
  "id": "pod-kube-system-apiserver-79f6c5d6c4-abc12",
  "node_type": "pod",
  "data": {
    "namespace": "kube-system",
    "name": "kube-apiserver-79f6c5d6c4-abc12",
    "security_context": {
      "privileged": "[-] false",
      "runAsUser": "[x] 1001",
      "hostNetwork": "[x] true",
      "hostPID": "[-] false",
      "seccompProfile": "[?] 未设置"
    },
    "ip": "10.244.0.3"
  },
  "session_id": "sess-20260619-001"
}
```

每个安全上下文字段五态标记必填——`[-] false` 表示"已确认不开启这个危险标志"（合规语义上是 pass，攻击语义上是已确认非逃逸路径）；`[x] true` 表示"已确认开启这个危险标志"（如 `hostNetwork=true`，需要后续 Phase 4a 深审）；`[?] 未设置` 表示字段未设值（按默认行为可疑）。Phase 1a 完成时所有 `[ ]` 必须消灭。

同时提取基础设施关系边（`infra.json`）：`runs_on`（Pod→Host）、`uses_sa`（Pod→SA）、`mounts`（Pod→Secret）、`exposes`（Service→Pod）、`host_path_mount`（Pod 挂宿主机路径）、`container_in`（Container→Pod）。

**步骤 ④ 数据写入与指纹生成**：写入 7 类节点 JSON、infra 关系边、`recon_summary.md`、`_index.md`。提升 `progress.json` 中 recon Phase 状态为 complete。

#### 限速与重试规则

| 参数 | 值 |
|------|-----|
| 最大并行 SSH 命令 | 3（同一服务器） |
| 批次间隔 | 2 秒 |
| 单次 SSH 超时 | 30 秒 |
| 读命令重试 | 3 次 / 间隔 2 秒 / 失败标 `[!]` |
| 探测命令重试 | 2 次 / 间隔 3 秒 |
| 攻击验证 | 1 次 / 间隔 5 秒 / 失败降级为 C3 |
| 返回 rate limited | 自动降级串行、间隔升至 5 秒 |

这些规则在 `/root/gencpt/skills/recon/SKILL.md` 第 362-387 行定。为什么这么严格？因为容器渗透的目标是生产环境，HTTP 请求过多会让 kube-apiserver 或 docker daemon 过载，影响业务。GenCPT 默认走"最小权限最小影响"原则。

#### 本 Phase 反幻觉约束

- **不准凭记忆出检测结果**——所有数据必 ssh_execute 真实执行产生
- **不准存储 Secret 内容**——`secrets.json` 仅记名称+类型
- **不准在上下文中累积原始输出**——立即写盘
- **不省略五态标记**——每字段必标注之一

---

### Phase 1b — 源码扫描（recon-source，可选）

#### 这个阶段在干什么

Phase 1a 是看运行中的集群，Phase 1b 是看**源代码层**的配置——Dockerfile（写"怎么构建容器镜像"的脚本文件）、K8s manifest（声明 Pod/Deployment/Service 的 YAML 文件）、Helm Chart（K8s 的包管理器模板）、CI/CD 配置。这些文件里常常藏着"运行起来之后看不到但源码里能发现的"风险，比如 Dockerfile 里写死一个 token 当环境变量、K8s manifest 用了 `privileged: true`、CI 把镜像仓库的密钥打进去了。

**启用条件**：用户启动时传了 `source-path` 参数指定源码目录，默认不启用。

#### 怎么做

LLM 用 `Glob` 按扩展名搜索源码目录（`Dockerfile*`、`*.yaml`、`*.yml`、`Chart.yaml`、`*.json`、`.gitlab-ci.yml`、`.github/workflows/*.yml`），把命中文件**控制总 token ≤ 8000**——比 Phase 1a 严格得多，因为源码扫描是补充性质，不希望喧宾夺主。

每个命中文件 Read 后提取安全相关字段：
- Dockerfile：`USER`（运行用户，若是 root 算风险）、`RUN apt-get install` 装了什么、`COPY . .` 是否拷贝整个目录（可能含 .git/密钥）、`ENV` 是否硬编码凭据
- K8s manifest：`securityContext.privileged`、`hostNetwork`、`hostPID`、`hostPath` 挂载、`serviceAccountName`、`imagePullPolicy`
- CI/CD：secrets 怎么管理、是否把密钥 echo 出来、是否 `docker login` 用明文凭据

提取的字段五态标记，写入 `evidence/recon/source_findings.md`，并更新知识图谱的相关节点（如把 Dockerfile 里手贱的 root 标到 `containers.json` 的 `security_context.runAsRoot=[x]`）。

---

### Phase 2 — 合规检测（k8s-compliance / docker-compliance / containerd-compliance）

#### 这个阶段在干什么

照着 CIS Benchmark 全量规则做合规检测。Phase 2 拆成 3 个子技能可并行：2a 跑 K8s 134 条、2b 跑 Docker 64 条、2c 跑 Containerd 28 条。每条规则由 LLM 读 SSH 原始输出后做语义判定（不是字符串匹配），fail 项必须附原始输出 + LLM 判定理由。

#### 三大设计机制（GenCPT Phase 2 区别于 kube-bench）

1. **JSON Lines 追加模式**：每条规则检测完立即一条 JSON 写到 `results.jsonl`（每行一条），不累积满批再写——这避免崩溃丢数据。
2. **分批 WU + 三重校验**：226 条规则分批跑，每批 WU 完成后立即做第一重校验（规则数/每条判定/fail 依据），不等全部跑完才发现错。
3. **平台分片写入**：K8s 写 `findings_k8s.json`、Docker 写 `findings_docker.json`、Containerd 写 `findings_containerd.json`，互不干扰，Phase 2 全部完成后再由 Pipeline 入口串行汇总。

#### K8s 合规的 WU 分批（详细见 `/root/gencpt/skills/k8s-compliance/SKILL.md` 第 232 行）

134 条规则分 4 个 WU：

| WU | 子分组 | 规则数 | 内容 | 检测层级 |
|----|--------|--------|------|---------|
| WU-2a-01 | G_1 全组 | 41 | API Server 文件权限/认证/DoS/泄露/审计/TLS | 全 L0（宿主检查 kube-apiserver 启动参数+配置文件） |
| WU-2a-02 | G_2-G_4 | 29 | Etcd + CM + Scheduler + Kubelet 认证 | 全 L0 |
| WU-2a-03 | G_5-G_6 | 26 | Kubelet 运行时/Streaming/TLS + Network Policies | L0 + 部分 L1 |
| WU-2a-04 | G_7-G_8 | 38 | Pod 安全 + RBAC + Secret 管理 | L0 + L1（kubectl exec 检查容器内 securityContext 实际生效值） |

**多节点检测策略**：K8s 规则分两类——
- **集群级**（G_1/G_2/G_3/G_6/G_8）：只 master 节点检查即可
- **节点级**（G_4/G_5/G_7）：每个节点跑本地文件检查。master 用 `ssh_execute(server, "...")`，可达 worker 用 `ssh_execute(server, "ssh <worker_ip> ...")` 跳转，不可达 worker 标 `[-] 不适用（SSH 不可达）`

#### 单条规则检测流程（4 步）

以 K8s-1.1.1（API Server pod specification 文件权限）为例：

**1. 读规则文件**：从 `compliance-rules/kubernetes/G_1_1_api_server_files.md` 读出规则定义——期望权限 600、检查命令 `stat -c '%a' /etc/kubernetes/manifests/kube-apiserver.yaml`、判定为 L0 层级。

**2. 执行检测命令**：

```bash
[L0] ssh_execute(server, "stat -c '%a' /etc/kubernetes/manifests/kube-apiserver.yaml")
# 输出：644
# 退出码：0
```

**3. 五态判定**（LLM 读输出做语义判定）：644 比 600 宽松（多了 group-read 和 other-read 权限位），不符合期望 → 标 `[x]`（fail）。必须附 SSH 原始输出 + 判定理由。

**4. 写盘**：

每条规则检测完立即写 `results.jsonl`（每行一条 JSON，反幻觉机制防崩溃丢数据）：

```bash
echo '{"rule_id":"K8s-1.1.1","verdict":"pass","evidence":"stat -c %a ...","host":"prod-k8s-01","ts":"2026-06-20T10:15:30Z"}' >> evidence/compliance/k8s/results.jsonl
```

WU 完成时把 jsonl 转成 JSON 数组：

```bash
jq -s '.' evidence/compliance/k8s/results.jsonl > evidence/compliance/k8s/results.json
```

同时写 `knowledge_graph/nodes/findings_k8s.json` 和 `compliance_k8s.json`（平台分片，不与其他平台混写）：

```json
[
  {
    "id": "finding-k8s-1-1-1",
    "node_type": "finding",
    "data": {
      "rule_id": "K8s-1.1.1",
      "platform": "k8s",
      "status": "fail",
      "severity": "high",
      "title": "API Server pod specification 文件权限过于宽松",
      "judgment": "文件权限 644 宽松于期望值 600",
      "host": "prod-k8s-01"
    }
  }
]
```

#### 三重校验

每批 WU 完成立即做第一重（规则数对得上？每条有判定？fail 有依据？），Phase 2 全部完成做第二重（134 条总数对得上？每条 fail 在 compliance.json 都能找到 finding 节点？五态无 `[ ]` 残留？），报告生成前做第三重（无占位符、无 `[ ]`）。

#### 合规确认门槛（3 项）

每条 fail 规则要算"真 fail"必须证明：
1. **可检测**：SSH 执行检测命令返回了实际违规证据
2. **可归属**：违规可明确归属到具体 Pod/容器/节点/命名空间
3. **影响可说明**：能说明违规的具体安全影响（映射到攻击假设族）

这是从"配置不符合基线"到"配置不符合基线且实际有安全影响"的升级判定。

#### 本 Phase 反幻觉约束

- **fail 必须附原始输出**：缺 SSH 输出 → 该规则改 `[?]` 移交 Phase 4b 深审，不许硬标 fail
- **na 必须说明原因**：如"非静态 Pod 部署模式，文件不存在"
- **warn 必须说明偏离**：如"权限 640，期望 600，偏离：group 位有读权限"
- **baseline 永不替代当前**：passed baseline 不影响本次判定，每条必重新执行检测

---

### Phase 3 — 交叉关联（cross-ref）

#### 这个阶段在干什么

Phase 2 找的是单条合规 fail。Phase 3 把这些单点和 Phase 1a 的侦察信息**交叉比对**，通过三库联动发现"哪些 fail 满足了哪些攻击的前置条件"，并对静态库没覆盖的映射让 LLM 动态推理补盲。产物是 ATK-CAND（攻击候选）列表，喂给 Phase 4a 做精确验证。

#### 怎么做（4 步骤，详见 `/root/gencpt/skills/cross-ref/SKILL.md` 第 56 行）

**步骤 ① 读取输入**：合规 results.json + findings.json + compliance.json + 三个假设库 + recon_summary，**按需读取不一次性加载**。

**步骤 ② 执行 3 条核心 XREF 查询**：

**XREF-001：合规违规 → 攻击假设前置条件映射**
- 遍历所有 fail/warn 规则
- 对每条 fail 在 `compliance-hypotheses.md` 匹配违规族（如 G_7 特权容器族）
- 命中的 CHK-CAND 卡片关联到 `attack-hypotheses.md` 的 ATK-HYP
- 对每个 ATK-HYP 标记五态：`[x]` 前置可能满足、`[?]` 部分满足、`[-]` 证伪、`[!]` 环境干扰
- **LLM 动态补充推理**（≤3000 tokens）：静态库全不命中时，LLM 语义模糊匹配 fail 规则和攻击模式前置条件，标 `[?] LLM推理关联`、source=`llm_reasoning`

输出示例：

```
K8s-5.2.1(fail) → CHK-CAND-002 → escape/socket-escape (ATK-HYP-001)
  标记: [x] 前置条件可能满足
  ATK-CAND-001: 特权容器+docker.sock逃逸
```

**XREF-002：叠加放大**：同一目标 ≥3 种违规叠加 → 风险放大。如某 Pod 同时 privileged=true + 无 resource limit + hostNetwork=true → 同时是逃逸候选 + DoS 候选 + 网络横向候选。

**XREF-003：盲区候选**：合规通过但侦察发现可疑（如 Pod 没明显违规但 reconnaissance_summary 里有 `[?]`） → 标候选送 Phase 4b LLM 推理。

**步骤 ③ 风险叠加分析**：把多组违规组合成的高风险面标记进入 Phase 4a 优先级排序。

**步骤 ④ 写盘**：ATK-CAND 节点（含 source=pattern_library / llm_reasoning / cross_ref 等来源标识）+ cross_ref edges + `prerequisite_signals.md`（前置条件信号比对表，给 Phase 4a 用）。

#### 静态库优先 + LLM 动态补充

为什么既要有静态库又要 LLM 推理？因为静态库是人工策展的高置信度已知映射（稳定），但覆盖跟不上攻防态势演化（滞后）；LLM 动态推理能补盲但置信度低（容易幻觉）。所以策略是：**静态命中直接标 `[x]` 前置可能满足（高置信度）；LLM 推理只标 `[?] LLM推理关联`（低置信度），必须经 Phase 4a 验证才能升级 `[x]`**。

---

### Phase 4a — 模式匹配攻击验证（attack-pattern）★核心

#### 这个阶段在干什么

Phase 3 产出的 ATK-CAND 还只是"前置条件可能满足"的怀疑。Phase 4a 拿攻击模式库（49 个模式）做精确验证——按条件触发表按需加载命中的模式 SKILL.md，按 L0/L1/L2 分层实际执行探测和攻击，把 `[?]` 怀疑变成 `[x]` 实证（C1/C2/C3）+ 差分证明。

#### 怎么做（4 步，详见 `/root/gencpt/skills/attack-pattern/SKILL.md`）

**步骤 ① 扫描触发条件**：

1. 读 Phase 2 的 fail/warn 规则 + Phase 1a 的 `[x]`/`[?]` 标记 + Phase 3 的 prerequisite_signals.md
2. 读 `/root/gencpt/attack-patterns/_index.md`，对照条件触发读取表（25+ 条触发信号→模式映射）
3. 按 `env_fingerprint` 平台信息过滤模式文件（目标纯 Docker 时不加载 k8s-sa-exploit 等 k8s 专属模式）
4. 生成待验证模式列表，按严重等级排序
5. **LLM 语义补充扫描**（≤500 tokens）：基于语义判断 fail/warn 中是否有静态触发表未覆盖、但相关的模式，特别关注 `_learned/` 目录下的新模式（静态表可能未及时收录）。命中的标 `[?] 疑似相关`，source=`llm_supplementary_scan`。这一步只筛不生成命令——必须 Read 完整 8 段 SKILL.md 后才能执行探测（反幻觉第 1 条）

**关键规则**："不准凭记忆出攻击命令！必须 Read 对应的模式 SKILL.md。每个模式的探测命令、攻击验证步骤、差分证明方法只存在于模式文件中，禁止从上下文记忆中提取。" 这是 Phase 4a 反幻觉最重要的约束。

**步骤 ② 逐个模式验证**：

对每个待验证模式，按以下流程：

**2.1 读取模式文件**：如 `attack-patterns/escape/socket-escape/SKILL.md` ——抽出前置条件、探测命令（标 L0/L1）、攻击验证步骤（标 L2）、差分证明方法、证伪条件。

**2.2 执行探测命令**（按执行上下文层级）：

以 socket-escape 模式为例，假设侦察到 `pod/backend-api-xyz` 有 `docker.sock` 挂载：

```bash
# L0 探测：宿主机观察 docker.sock 是否存在
[L0] ssh_execute(server, "ls -l /var/run/docker.sock")
# 输出：srw-rw---- 1 root docker 0 Jun 19 08:42 /var/run/docker.sock

# L1 探测：容器内观察 docker.sock 可见且可写
[L1] ssh_execute(server, "kubectl exec -n production backend-api-xyz -- ls -l /var/run/docker.sock")
# 输出：srw-rw---- 1 root docker 0 Jun 19 08:42 /var/run/docker.sock
# 攻击者视角（容器内进程权限）可看到 → 前置条件满足
```

注意 L0 和 L1 都执行——L0 确认宿主层有这个 socket；L1 确认容器内攻击者能看到这个 socket。两者都满足才证明"前置条件满足"。

**2.3 判断前置条件**：

```
前置条件检查（L0+L1）
    ├─ 不满足 → [-] 证伪（进入全景报告覆盖矩阵"不可利用"行）+ 写证伪依据
    ├─ 部分满足 → [?] C3 风险线索 + 标记未满足的前置条件
    └─ 满足 → 继续攻击验证
```

**2.4 执行攻击验证（L2）**：

前置条件满足时执行模式文件的攻击验证步骤。**必须按审批门控**——L2 非破坏性 auto 模式自动通过，L4 逃逸验证 manual 模式需 question 确认。

差分证明流程（攻击前后状态对比）：

```bash
# 攻击前快照（L0）
[L0] ssh_execute(server, "docker ps")
# 输出：（无异常容器）

# 攻击执行（L2 - 容器内攻击者视角）
[L2] ssh_execute(server, "kubectl exec -n production backend-api-xyz -- \
    docker run -v /:/host alpine ls /host/etc/shadow")
# 输出：root:x:0:0:root:/root:/bin/bash

# 攻击后对比（L0）
[L0] ssh_execute(server, "docker ps")
# 输出：新增一个 alpine 容器

# 差分结论：✅ 攻击成功
# 可观测差异 1：宿主机 docker ps 多出一个 alpine 容器
# 可观测差异 2：容器内可读取宿主机 /etc/shadow

# 清理（必须可恢复，C1 5项门槛之一）
[L0] ssh_execute(server, "docker rm -f <container_id>")
```

差分证明要求至少 2 个可观测差异，每个差异必须有 SSH 输出证据，必须有清理命令（C1 5 项门槛的"可恢复"项要求）。

**2.5 生成 ATK-CAND**：

```json
{
  "id": "ATK-CAND-001",
  "source": "pattern_library",
  "pattern_ref": "escape/socket-escape",
  "target": "pod/backend-api-xyz",
  "severity": "Critical",
  "verification_level": "L2",
  "context": "container",
  "confidence": "C1",
  "prerequisites_met": ["docker.sock_visible", "docker.sock_writable"],
  "prerequisites_unmet": [],
  "evidence_files": [
    "evidence/attack/raw/pre_ATK-CAND-001_20260619T084200.md",
    "evidence/attack/raw/post_ATK-CAND-001_20260619T084200.md"
  ],
  "five_state": "[x]",
  "trigger_rules": ["K8s-5.2.1", "K8s-5.2.3"],
  "hypothesis_refs": ["CHK-CAND-002", "ATK-HYP-001"]
}
```

`verification_level` 字段说明：L0 仅宿主机观察/ L1 容器内观察/ L2 容器内攻击验证差分充分/ L3 条件验证理论推导。

**步骤 ③ 处理未匹配信号**：有 fail 或侦察发现匹配不上任何现有模式 → 写 `unmatched_signals.md`，标 `[?]`，明确"无法匹配现有模式，需 LLM 推理"，移交 Phase 4b。

**步骤 ④ 五态闭环**：所有触发信号转换为 `[x]`/`[?]`/`[-]`/`[!]` 之一，`[x]`/`[?]` 必有 ATK-CAND 编号，`[-]` 必有证伪依据，`[!]` 必有阻断机制描述。ATK-CAND 编号从 Phase 3 最大编号 +1 起连续。

#### 差分证明 L0 观测强制要求（按攻击类型分级）

这是 GenCPT 行业首创的精细设计（详见 `/root/gencpt/README.md` 第 289 行）：

| 攻击类型 | 差分证明要求 | 不满足时 |
|---------|------------|---------|
| AS-1 逃逸 | 必须 `[L0]基线 + [L2]执行 + [L0]观测` 三段式 | C1 降级 C2 |
| AS-5 DoS | 必须 `[L0]资源监控基线 + [L2]执行 + [L0]对比` | C1 降级 C2 |
| AS-7 持久化 | 必须 `[L0]宿主机文件检查` | C1 降级 C2 |
| AS-3 网络 / AS-4 数据 | `[L1]基线 + [L2]执行 + [L1]观测` | 不强制 L0 |

为什么 AS-1 逃逸必须 L0 观测？因为逃逸的"危害可观测"是"宿主机出现了不该有的进程/文件/连接"，光看容器内观察不到这个证据。L0 观测就是用宿主机视角拍快照前后对比。

#### 本 Phase 反幻觉约束

- 不准凭记忆出攻击命令
- 不准伪造 SSH 输出
- 无证据不写确认态（差分不充分不得标 C1）
- 超出审批立即停（L4/L5 拒绝就降级）
- 不混合审计和攻击视角（L0 仅侦察，L1/L2 通过 kubectl exec 模拟容器内视角）

---

### Phase 4b — LLM 推理补盲（attack-reasoning）

#### 这个阶段在干什么

Phase 4a 用"已知模式库"做验证。但模式库只有 49 个模式，不可能覆盖世界上所有攻击手法——总有些 flaw 组合在库外。Phase 4b 处理这些盲区候选：让 LLM 用 **CoT + ReAct 循环**（最多 10 轮）从零开始动态推理，自主探索有没有漏洞。这是漏报的最后防线。

- **CoT**（Chain of Thought，思维链）：让 LLM 一步一步推理，而不是直接下结论
- **ReAct**（Reasoning + Acting）：每步推理后执行一个动作（ssh_execute / kubectl exec / Read 文件），根据观察结果再推理下一步

#### 输入候选来源

1. Phase 4a 未匹配的候选
2. `[?]` 状态的候选
3. 证据不完整的候选
4. Phase 3 的盲区候选（XREF-003）
5. Phase 1a 侦察里 `[?]` 标记的发现

#### 怎么做

对每个盲区候选，LLM 执行 ReAct 循环：

```
Round 1:
  Thought: K8s-5.2.1 fail 说 privileged=true，但侦察显示该 Pod 无 AppArmor，
           需验证是否真能 nsenter 进入宿主机 PID 命名空间
  Action: [L1] kubectl exec -n prod backend-api -- cat /proc/1/status | grep CapEff
  Observation: CapEff: 0000003fffffffff （所有 capability 位全开）
  
Round 2:
  Thought: CapEff 全开表示容器有 CAP_SYS_ADMIN，且无 AppArmor 阻断（Phase 1a 已确认），
           尝试 nsenter 进入宿主机 PID 命名空间
  Action: [L2] kubectl exec -n prod backend-api -- nsenter -t 1 -m -u -i -n -p -- ls /etc/shadow
  Observation: （需 manual approval）批准后输出 root:x:0:0:root:/root:/bin/bash ...

Round 3:
  Thought: nsenter 成功读取宿主机 /etc/shadow，逃逸成立。需要做差分证明并写 ATK-CAND
  Action: 写 ATK-CAND-XXX + 差分证明到 chain-verify
  Observation: 完成
```

每轮必须执行 ssh_execute 或 Read 加载真实数据（反幻觉规则：禁凭记忆推理，必附完整 ReAct 链，Thought/Action/Observation 不许省略）。

#### 产出 insights

Phase 4b 把 LLM 推理发现写成 `evidence/insights.md`，每个 INSIGHT 包含完整 ReAct 链。这些 insights 是 Phase 9 模式进化的原料——若发现了一条模式库没有的新攻击路径，Phase 9 评估是否晋升为永久模式。

**重要**：insights 不直接晋升模式（必须经 Phase 9 的 4 项门槛 + 用户审批）；Phase 4b 只产候选不决定晋升。

---

### Phase 5 — 链构建（chain-builder）

#### 这个阶段在干什么

两件事：

1. **链构建**：把多个已确认的 ATK-CAND 组合成一条多步利用链（CHAIN-xxx），深度 ≤5。比如"步骤 1 用 socket-escape 逃逸到宿主机 → 步骤 2 用宿主机 docker 控制权读 etcd 数据 → 步骤 3 用 etcd 里的 SA Token 横向移动到 kube-system 命名空间"。
2. **评估每条链的可达性和总影响**：理论链路是否成立？组合影响是否大于单点？

#### 怎么做

**步骤 ①** 提取 `confirmed` 项作为链起点，`condition_met` 项作为链材料。

**步骤 ②** 图谱查找可达路径：通过知识图谱的 cross_ref 边、infra 边、attack 边反查——某 ATK-CAND 的 target 节点（如 `pod-backend-api`）有没有到其他节点的边？SA Token 是否在逃逸后可被读？etcd 是否可达？把它们一个接一个串起来。

**步骤 ③** 评估链式影响：每个单点影响 + 组合放大效应。如 socket-escape 单点是"读宿主机文件"，加上 secret-exfil 就是"读 kube-system 命名空间所有 Secret"，加上 lateral-move 就是"横向到全集群"——总影响远大于单点之和。

**步骤 ④** 分配 CHAIN 编号 + 写 `chain_builder.md`。每条链描述包括：步骤列表、每步引用的 ATK-CAND、可达性判定（confirmed_full / confirmed_partial / theoretical）、总影响推论、阻断点描述（若链某步被安全机制阻断则后续步骤依赖不上的说明）。

#### 限制

- 深度 ≤5（防无限扩展）
- 单链 ATK-CAND ≤20
- 推导深度超 5 必报"深度截断"声明

---

### Phase 6 — 链验证（chain-verify）★最终判定关卡

#### 这个阶段在干什么

Phase 5 构建了 CHAIN-xxx 链。Phase 6 对每条链做最终判定：5 级审批门控逐项执行、收集差分证明、综合所有步骤的验证结果、判定最终可信度 C1/C2/C3。这是渗透测试的最终判定关卡——所有"差分证明不充分就标 C1"的偷懒在这里被拦截。

#### 怎么做（4 步骤，详见 `/root/gencpt/skills/chain-verify/SKILL.md`）

**步骤 ① 逐链验证**：

对每条链的每个步骤执行：

**阶段 A 前置条件验证**：
- 检查环境固有条件（合规违规 + 基础设施边）——读 findings.json 和 cross_ref.json 确认
- 检查前一步攻击后果是否满足本步前置条件——读前一步差分证明。如果前一步未验证或降级，本步前置条件可能不满足

**阶段 B 攻击验证（按审批门控）**：根据攻击模式 SKILL.md 的 `max_verification_level` 和 `destructive` 决定验证层级。如 `max_verification_level = L2 且 destructive = false` → 执行 L2 攻击验证；`max = L2 且 destructive = true` → 标 L3 条件验证不实跑；涉及宿主机逃逸 → L4 需 manual 确认；DoS 类 → L5 理论推导标 ⚠️。

**阶段 C 差分证明收集**：每步执行前快照 → 执行攻击 → 执行后对比，差分判断（攻击前后有明确可观测差异 → ✅ 充分 / 无明确差异 → ⚠️ 不充分 / 无法执行 → ❌ 无差分理论验证）。

每步必标 `[L0]`/`[L1]`/`[L2]` 执行上下文。差分证明格式：

```markdown
### CHAIN-001 步骤 2 差分证明

**攻击前快照**：
- [L0] `docker ps` 输出：无异常容器
- [L1] `cat /proc/1/cgroup` 输出：在容器内

**攻击执行**：
- [L2] `kubectl exec -n production backend-api -- docker run -v /:/host alpine ls /host/etc/shadow`

**攻击后对比**：
- [L0] `docker ps` 输出：出现新 alpine 容器
- [L2] 攻击命令输出：可读取宿主机 /etc/shadow

**差分结论**：✅ 攻击成功，可从容器内通过 docker.sock 读取宿主机文件
```

**步骤 ② 收集差分证明**：见上。

**步骤 ③ 审批门控 5 级**：每个需审批的步骤，按 session_config.json 的 approval 模式执行：
- L1 始终自动通过
- L2 manual 模式 question 确认 / auto 模式自动
- L3 manual 快速 / auto 自动
- L4 manual question / auto 自动
- L5 必 question（理论验证）
- 超时：L2/L3/L4 5 分钟超时降级理论 ⚠️；L5 10 分钟超时降级 ⚠️

**安全熔断检查**：执行 L3/L4 前先检查 `session_config.json.auto_high_risk_exec_count`——10 分钟内 ≥5 次自动通过则下一个 L4 强制 manual。

**步骤 ④ 被阻断链检查 + 差分证明验证**：

对被阻断的步骤：
- 识别阻断机制（AppArmor / Seccomp / NetworkPolicy / SELinux）
- 读该 ATK-CAND 模式 SKILL.md 的"绕过策略"章节
- 评估：✅ 有可行绕过 → 继续链标注绕过方式；⚠️ 理论可能但未证实 → 标 condition_met；❌ 无已知绕过 → 该链该步骤 blocked

**最终链可信度判定**：

C1 实证复现需 5 项全满足：
1. 前置条件可复现（每步前置都有实际观测数据满足）
2. 可执行（每步攻击命令在目标环境执行且未报错）
3. 可区分（差分证明充分，攻击前后有 ≥2 项可观测差异）
4. 影响可观测（攻击成功副作用可被观测）
5. 可恢复（攻击后有清理命令恢复原状态）

C2 条件实证：前置满足 + 理论链路完整但被阻断或不可安全复现。

C3 风险线索：配置有隐患但前置不完全满足。

输出 `chain_verification.md` 含每条链的验证概要 + 步骤验证 + 审批记录 + 差分证明 + 最终可信度判定：

```markdown
## CHAIN-001: socket-escape → secret-exfil → lateral-move

### 步骤验证

#### 步骤 1: ATK-CAND-001 (socket-escape)
- 前置条件: ✅ 全部满足
- 攻击验证: ✅ L2 通过
- 差分证明: ✅ 充分
- 可信度: C1

#### 步骤 2: ATK-CAND-005 (secret-exfil)
- 前置条件: ✅ 全部满足（依赖步骤1逃逸后果）
- 攻击验证: ✅ L2 通过
- 差分证明: ✅ 充分
- 可信度: C1

#### 步骤 3: ATK-CAND-007 (lateral-move)
- 前置条件: ⚠️ 部分满足（SA Token权限范围未实测）
- 攻击验证: ⚠️ L3 条件验证
- 差分证明: ⚠️ 不充分
- 可信度: C2

### 链可信度判定: C2 条件实证 ✅
原因: 步骤1-2为C1实证复现，步骤3依赖步骤2窃取的SA Token
进行横向移动，理论推导充分但差分证明不足。
```

#### 本 Phase 反幻觉约束

- 不准凭记忆出验证结果——每条命令必从模式或假设库查出处
- 不准伪造 SSH 输出
- 无证据不写确认态（差分不充分不得 C1）
- 超出审批立即停
- 省略词零容忍
- 占位符必替换

---

### Phase 7 — POC 生成（poc-generator）

#### 这个阶段在干什么

对 Phase 6 判定为 confirmed (C1) / condition_met (C2) 的链生成**可执行的 POC 脚本**。POC（Proof of Concept，概念验证）就是"能证明这条攻击路径确实可复现的可执行脚本"。

**重要**：POC 是渗透测试证据，不是攻击武器。Phase 7 严格只对 C1/C2 终态产 POC，C3/不可利用/被阻断一律不产。每个 POC 标注 `L0/L1/L2/L3` 执行层级 + `C1/C2/C3` 可信度，让甲方知道这个 POC 在什么视角能跑、什么可信度。

#### POC 形态

- Web 入口产 HTTP 请求包（这里容器渗透其实少见，GenCPT 主要产 bash 脚本）
- 命令行入口产可执行的 bash / PowerShell 脚本（写入 `evidence/poc/poc_scripts/POC-{NNN}-{slug}.sh`）
- 每个脚本含：
  - 攻击前快照收集命令（标 `[L0]`）
  - 攻击执行命令（标 `[L1]`/`[L2]`）
  - 攻击后对比命令（标 `[L0]`/`[L1]`）
  - 清理命令（必含）
- 占位符替代真实凭证（反幻觉 #4 适配）：真 host → `{{target_host}}`、真 token → `{{test_token}}`、真 IP → `{{target_ip}}`

#### 输入

- chain_verification.md（Phase 6 判定的 confirmed/condition_met 链）
- attack.json（Phase 4a 的 ATK-CAND 详情）
- attack-patterns/ 下的具体模式 SKILL.md（拿探测命令和攻击验证步骤）

#### 输出

- `evidence/poc/poc_scripts/POC-{NNN}-{slug}.sh` — 可执行脚本
- `evidence/poc/summaries/POC-{NNN}-{slug}.md` — 人读说明 + 复现步骤
- `knowledge_graph/edges/poc.json` — POC 引用边

POC 脚本示例（特权容器 + docker.sock 逃逸场景）：

```bash
#!/bin/bash
# POC-001: docker.sock socket-escape
# Required verification level: L2
# Required confidence: C1
# Prerequisites: privileged=true OR docker.sock mounted writable

set -e
TARGET_HOST="{{target_host}}"
TARGET_NS="{{target_namespace}}"
TARGET_POD="{{target_pod}}"

echo "[Step 1] Attack pre-snapshot (L0)"
ssh $TARGET_HOST "docker ps -q" > /tmp/poc-001-pre-dockerps.txt

echo "[Step 2] Execute attack (L2 - container perspective)"
ssh $TARGET_HOST "kubectl exec -n $TARGET_NS $TARGET_POD -- \
    docker run -v /:/host alpine ls /host/etc/shadow" > /tmp/poc-001-attack-output.txt

echo "[Step 3] Attack post-snapshot (L0)"
ssh $TARGET_HOST "docker ps -q" > /tmp/poc-001-post-dockerps.txt

echo "[Step 4] Diff comparison"
diff /tmp/poc-001-pre-dockerps.txt /tmp/poc-001-post-dockerps.txt

echo "[Cleanup] Remove temporary containers"
ssh $TARGET_HOST "docker rm -f \$(docker ps -aq --filter ancestor=alpine)"
```

#### 本 Phase 反幻觉约束

- 只对 C1/C2 终态产 POC，C3/不可利用/被阻断不产
- 占位符必替代真实凭证
- payload 必沿 evidence_chain 验证可达
- 非命令行攻击不强套 HTTP 包

---

### Phase 8 — 报告交付（report-compliance / report-attack / report-summary）★最终交付

#### 这个阶段在干什么

把所有产物汇总成**完整交付物**：合规报告 + 攻击报告 + 全景综合报告 10 章 + QA 三层校验 + 覆盖矩阵报告。Phase 8 拆 3 个子技能：

- **Phase 8a 合规报告**（report-compliance）：按平台分组合规报告 + 阈值矩阵 + 违规详情
- **Phase 8b 攻击报告**（report-attack）：每条 CHAIN 一份详细报告 + 局部 POC 引用 + 修复建议
- **Phase 8c 全景报告**（report-summary）：汇总所有结果 + QA 三层校验

#### 全景报告 10 章（详见 `/root/gencpt/skills/report-summary/SKILL.md`）

| 章 | 内容 |
|----|------|
| 1 | 执行详情（启动时间/模式/环境/Phase 统计） |
| 2 | 环境覆盖全景（侦察/源码/合规覆盖率） |
| **2.5** | **⚠️ 最大检测盲区提示**（Top 3 高优先级盲区） |
| 3 | 合规分组热力图 |
| 4 | 攻击面覆盖矩阵（7 攻击面 × 模式/LLM/总覆盖） |
| 5 | 已知模式库覆盖全景 |
| 6 | LLM 推理覆盖全景 |
| 7 | 攻击验证结果分布（C1/C2/C3/不可利用/已阻断） |
| 8 | 漏洞来源标识（📚 已知模式库 / 🧠 LLM 推理 / 🔄 学习模式） |
| 9 | 未覆盖事项及原因（高/中/低优先级 + 盲区提示） |
| 10 | 产品安全质量评估（综合评分 + Top 5 风险） |

**重要**：即使审计成功找出多条 C1 攻击链，报告里也要老实写出"哪些没查到"——这就是反幻觉的精神：**不许"未发现即安全"**。

#### QA 三层校验

| 层级 | 校验内容 | 可否 Override |
|------|---------|--------------|
| **第一层** 结构校验 | MUST 输出文件存在、知识图谱边节点对应、ATK-CAND 编号连续、五态无 `[ ]` 残留 | 否 |
| **第二层** 语义校验 | 5 条合规 + 3 条 ATK-CAND + 2 条 `[-]` 抽检，ssh_execute 重新验证 | 是（记录原因） |
| **第三层** 覆盖校验 | 7 攻击面 × 模式覆盖矩阵无空白，226 条合规规则覆盖矩阵无空白 | 否 |

#### 攻击面覆盖矩阵

行=7 攻击面，列=模式库覆盖 / LLM 推理覆盖 / 总覆盖。**不可利用项（已证伪）也必须出现在覆盖矩阵中**，标注"已检查不可利用 + 证伪依据"。

这个矩阵回答甲方最关心的"你到底有没有全覆盖"——传统工具没法答这题，GenCPT 用覆盖矩阵明确告诉甲方：7 个攻击面里 AS-5 DoS 这次只覆盖了 1 个模式，AS-2 认证授权这次有 14 个模式全跑过。

---

### Phase 9 — 模式进化（evolve）★进化闭环

#### 这个阶段在干什么

把 Phase 4b 产出的 `insights.md`（LLM 推理发现）经 **4 项晋升门槛评估 + 用户审批**，批准的写入 `attack-patterns/{攻击面}/{pattern-name}/_learned/SKILL.md`（永久模式目录，8 段格式与永久模式同标准）。同时运行 **4 级自净机制** + baseline 跨会话累积。

换句话说：每次渗透测试如果发现了"模式库没有的新攻击路径"，就评估要不要把它加进模式库，让下次测试能自动识别这种路径。这样工具会越用越强。

**触发方式**：Pipeline 末尾用 `--evolve` 参数触发，或独立运行 `/gencpt-evolve --session-dir /path`。Phase 9 不执行任何 SSH 命令，纯 Markdown 读写 + LLM 语义分析。

#### 4 项晋升门槛

详见 `/root/gencpt/skills/evolve/SKILL.md` 第 42 行。一个 LLM 推理发现要晋升为攻击模式，4 项**必须全部满足**：

| # | 门槛 | 判定依据 |
|---|------|---------|
| ① | 差分证明充分 | L2 差分前后证据完整，至少 2 个可观测差异 + 每个差异有 SSH 输出文件路径 |
| ② | 探测可复现 | 在 ≥2 个不同 host_fingerprint 环境可达同样安全结论（探测命令不依赖临时状态） |
| ③ | 无法匹配现有模式 | 与全部 49 个现有模式 + 25 张 ATK-HYP 假设卡片的前置条件和攻击路径都不一致（是变体则不算新） |
| ④ | 跨会话命中 ≥2 次 | session_history.md 中相同或高度相似 ATK-CAND 出现 ≥2 次 |

4/4 全过 → 用户审批（添加为新模式 / 拒绝 / 暂存观察）。用户拒绝：insights.md 标"已拒绝：{原因}"，不创建模式。用户批准：执行模式创建。

#### 模式创建流程

1. 读 `references/promotion-template.md` 拿 8 段结构模板
2. 生成新模式 SKILL.md，frontmatter 含：`source: learned`、`confidence: medium`、`hit_count: 1`、`last_hit: 本次会话时间`、`stale: false`、`platforms: [{适用平台}]`、`attack_surface`、`severity`、`trigger_rules`、`hypothesis_refs`、`required_tools`
3. 写入 `attack-patterns/{攻击面}/{pattern-name}/_learned/SKILL.md`（`_learned/` 标识为自动进化产生）
4. 更新 `_index.md` 加新条目 + 条件触发表加新触发条目
5. 更新 `hypothesis-libraries/attack-hypotheses.md` 加新 ATK-HYP 假设卡片
6. 更新 `_learned_index.md`
7. 执行**三库一致性检查**：_index.md 条目 ↔ 实际文件 ↔ 假设卡片，编号连续，frontmatter 完整

#### 4 级自净

对 `source=learned` 的模式根据命中次数自动调整：

| 触发 | 动作 |
|------|------|
| hit_count ≥5 且跨 ≥2 环境 | confidence 升 high |
| 连续 5 次会话未命中 | confidence 降 medium（若当前 high） |
| 连续 10 次会话未命中 | 标 `stale=true`（不归档保留库中） |
| 连续 15 次会话未命中 | question 工具问用户是否归档到 `attack-patterns/_archived/` |

`manual/curated` 来源模式不执行降级或归档（永远 confidence=high），只更新 hit_count 和 last_hit。

#### 进化报告 7 章

`evidence/evolve/evolve_report.md` 必含：晋升列表/降级列表/升级列表/归档列表/变体匹配列表/暂存观察列表/统计。即使本次无候选晋升，也必输出（记录零晋升原因 + 三库一致性检查结果）。

#### 本 Phase 反幻觉约束

- 不准跳过晋升门槛（4 项必逐项检查并记录）
- 不准自动晋升（必经 question 工具用户审批）
- 不准跳过用户审批归档
- 不准降级 manual/curated 模式
- 不准伪造差分证明
- 不准跳过三库一致性检查

---

## 五、关键机制详解——九个核心机制

### 5.1 攻击者视角 L0-L3（行业首创）

前面 §2.5 已讲过基础。这里补完整的设计动机和反幻觉意义：

**设计动机**：BAS 工具普遍"拿到 root 就跑预写脚本"——成功的攻击只证明"宿主机 root 神通广大"，但容器渗透的真实命题是"容器内非特权攻击者能干啥"。比如一个被攻破的 Web 应用容器里的攻击者，权限等于容器内进程权限（可能只 1000:1000），他能不能逃出来？必须从容器内视角验证才有意义。

**GenCPT 的做法**：

- L0 只读侦察（ssh_execute 直接在宿主机跑）：拍快照、查配置、做差分对比。可用 sudo。
- L1 容器内观察（`kubectl exec <pod> -- <cmd>`）：模拟被攻破容器的攻击者视角能"看到"什么。容器内进程权限。
- L2 容器内攻击验证（`kubectl exec <pod> -- <attack>`）：实际执行攻击命令。需差分框架 + 审批。
- L3 条件验证（不执行破坏性命令）：标 ⚠️ 理论推导。DoS / 删根目录等不可安全复现。

**root 仅做 L0**——这是反幻觉的关键约束（在 `/root/gencpt/skills/attack-pattern/SKILL.md` 步骤 2.2 明文写"不混合审计和攻击视角——L0 仅用于侦察和条件核实，L1/L2 通过 kubectl exec 模拟容器内攻击者视角"）。

**AS-1 逃逸差分证明必须 L0 观测**：因为逃逸危害表征是"宿主机出现异常进程/文件/连接"，必须用 L0 视角才能观测到。L1/L2 视角在容器内看不到这些证据。所以 AS-1 逃逸的差分证明三段式：`[L0]基线 + [L2]执行 + [L0]观测`，不满足就 C1 降 C2。

### 5.2 可信度 C1/C2/C3

前面 §2.6 已讲。这里补差分证明 L0 强制要求和 5 项门槛的细节。

**5 项确认门槛**（C1 必须全满足）：

| # | 门槛 | 证据来源 |
|---|------|---------|
| ① | 前置条件可复现 | 链中每步前置条件都有实际观测数据证明满足 |
| ② | 可执行 | 链中每步攻击命令都能在目标环境执行且未报错 |
| ③ | 可区分 | 攻击效果可与正常行为区分（差分证明充分，≥2 项可观测差异） |
| ④ | 影响可观测 | 攻击成功副作用可被观测 |
| ⑤ | 可恢复 | 攻击后可恢复到原始状态（有清理命令） |

为什么"可恢复"是 C1 门槛之一？因为 L2 攻击会在目标环境留遗物（如多出一个 alpine 容器、宿主机多几个进程）。如果不清理就标 C1，甲方会问"那我现在环境是不是已经被改了"——破坏性操作必须可恢复才算可复现的合格证据。

**C1 → C2 降级触发**：差分证明 L0 三段式不满足、5 项有 1 项不满足、被安全机制阻断（附阻断机制名称）、不可安全复现（标 ⚠️）。

### 5.3 三库联动

前面 §2.4 和 §Phase 3 已讲。核心：

- **CHK-CAND（35 张合规假设卡）**：G1-G7 每组合规违规 × 攻击假设映射
- **ATK-HYP（25 张攻击假设卡）**：注入/逃逸/访问控制/信息泄露/数据/供应链/持久化
- **XREF（3 条交叉查询模板）**：叠加/组链/盲区

**静态库优先 + LLM 动态补充**：静态命中直接 `[x]`，LLM 推理只 `[?] llm_reasoning`（须经 Phase 4a 验证才能升级）。这是平衡"覆盖滞后"（静态库头痛）和"幻觉风险"（LLM 头痛）的设计——优先信任稳定的高置信度静态库，但用 LLM 推理补盲。

### 5.4 模式进化（行业首个活系统）

前面 Phase 9 已讲。核心 4 项晋升门槛 + 4 级自净 + 三库一致性检查。

为什么这是"行业首个活系统"？因为传统攻击模式库都是人工策展的静态库——要更新得有人手工加新模式、手工删失活模式，慢还容易忘。GenCPT 的进化机制是**自动评估候选 + 用户审批门控 + 自动自净**——LLM 推理发现的新路径自动评估 4 项门槛，满足就提交用户审批；老模式 15 次会话未命中自动问归档。模式库因此跟随攻防态势演化。

### 5.5 全景覆盖报告

前面 §Phase 8 已讲。核心是**攻击面覆盖矩阵**——行=7 攻击面，列=模式库覆盖 / LLM 推理覆盖 / 总覆盖，**不可利用项也要出现在覆盖矩阵中**（标证伪依据）。

这个矩阵回答甲方"你到底有没有全覆盖"——传统工具答不出这题，GenCPT 明确告诉甲方：本次 AS-5 DoS 只跑了 1 个模式（resource-abuse），fork-bomb 因 L5 不可安全复现只做了理论验证。

**盲区提示 Top 3**（强制出现在全景报告 2.5 章）：即使审计成功也要老实写出"哪些没查到"——这是反幻觉的精神"未发现即安全"被禁。

### 5.6 反幻觉 6 条 + 三层 QA

前面 §2.9 和 §Phase 8 三层 QA 已讲。核心 6 条硬约束：

1. 不准凭记忆出攻击命令
2. 不准伪造 SSH 输出
3. 无证据不写确认态
4. 占位符必替换
5. 超出审批立即停
6. baseline 永不替代当前

**三层 QA 校验**：结构层（_必有 / 编号连续 / 五态无残留）→ 语义层（ssh_execute 重新验证 10 条抽样）→ 覆盖层（226 条规则 + 7 攻击面 100% 覆盖）。第三层不可 Override——失败即拒收报告。

### 5.7 方法 C 混合渐进（企业落地障碍为零）

GenCPT 在 SSH 命令使用上走"方法 C 混合渐进"策略（详见 `/root/gencpt/skills/shared/SSH_COMMANDS.md` §6.4 Fallback）：

- **原生命令优先**：优先用目标环境已有的工具（kubectl / docker / crictl / ctr），不用第三方工具
- **专用工具按需上传**：若需要某特殊工具（如 trivy 扫镜像），通过 ssh_upload 上传到 `/tmp/gencpt-tools/`，**SHA256 校验**后执行
- **失败自动回退**：上传失败或工具不可用 → Fallback 到用原生命令替代（如 trivy 不可用，改用 `docker history` + `docker inspect`）
- **会话结束自动清理**：会话结束自动删 `/tmp/gencpt-tools/` 内容
- **最小权限最小影响**：所有上传工具以非特权用户跑，所有命令走 SSH 限速

为什么？因为企业落地最大障碍是"你得在我们的生产环境装一堆第三方工具，安全部门不批"。方法 C 让 GenCPT 默认只用原生命令，企业落地障碍为零。

### 5.8 并发写入保护

Phase 2 的 K8s/Docker/Containerd 三个合规可并行跑。但它们都要写 `knowledge_graph/nodes/findings.json` 和 `compliance.json`——并发直接写同一个文件会冲突。

GenCPT 解决方案：**平台分片写入**（K8s 写 `findings_k8s.json`、Docker 写 `findings_docker.json`、Containerd 写 `findings_containerd.json`，各自落盘互不干扰），Phase 2 全部完成后再由 Pipeline 入口用 `jq -s 'add'` 串行汇总为统一的 `findings.json` 和 `compliance.json`。

这种"各自落盘 + 串行汇总"模式（见 `/root/gencpt/skills/k8s-compliance/SKILL.md` 第 174 行 + `/root/gencpt/skills/cross-ref/SKILL.md` 第 33 行的补救脚本）既能并行提速，又避免并发写入冲突。如果 Phase 3 启动时发现仅有分片无汇总，会自动跑补救命令汇总，缺分片则跳过（不报错）。

### 5.9 断点续传（batch 级 progress.json + JSON Lines）

容器渗透大集群可能跑几小时，中间可能因会话压缩、子代理崩溃、Token 耗尽而中断。重跑从头就浪费大量算力。

GenCPT 的断点续传机制（详见 `/root/gencpt/SKILL.md` 第 292 行）：

1. **batch 级粒度**：`progress.json` 记录每个 Phase 下每个 WU 的状态（pending / in_progress / complete / failed）
2. **JSON Lines 续传**：每条规则/每个攻击检测完即写一行到 `results.jsonl`，崩溃后用 `wc -l results.jsonl` 确定已完成行数，跳过对应规则继续
3. **崩溃的 WU 重跑**：WU 崩溃/中断时 status 保持 in_progress，下次从最后写盘的 jsonl 行续传，不重做已检测的规则
4. **已 complete 的 WU 永不重跑**（反幻觉规则：不许循环重跑已完成的工作）
5. **每 WU 完成立即写盘 progress.json**——不等整个 Phase 完成才写，防 Phase 中断丢全部进度
6. **会话压缩后先读 progress.json 恢复**——LLM 重启后从第一个非 complete 的 WU 继续

这种"分批 WU + 每批立即写盘 + JSON Lines 续传"三层机制，保证中断可恢复、不重跑、不丢数据。

### 5.10 五态标记闭环 + 条件触发表按需加载

这两个机制前面 §2.7 和 §Phase 4a 已讲。补总览：

**五态标记闭环**：所有发现项必标 `[x]/[?]/[-]/[!]/[ ]`，最终交付前 `[ ]` 必消灭。**这是质量门禁**——QA 第一层校验扫残留 `[ ]`，有则报告拒收。意义是让甲方不会困惑"这条到底查了没查"。

**条件触发表按需加载**：`attack-patterns/_index.md` 的 25+ 条触发信号→模式映射表，Phase 4a 启动时只读命中的模式 SKILL.md，不读全部 49 个模式——避免 15-20k token 浪费在不相关模式上。配合 `platforms` 字段按 scope 过滤平台（纯 Docker 时不加载 k8s 专属模式）。

### 5.11 baseline 版本兼容 + 环境指纹跨会话

**baseline 版本兼容**（不止 diff 报告）：`suite_version` 字段记录套件版本。Phase 8c 报告生成时检查 baseline 与当前 suite_version 是否一致：
- 版本一致：正常 diff 对比（逐条规则 pass/fail 状态变化）
- 版本不一致：降级为**趋势对比**（不逐条对齐，只看总体合规率变化趋势），并明确标注"baseline 永不替代当前测试"——baseline 只用作 diff，当前结果始终权威

**环境指纹 + 跨会话**：`env_hash = sha256(k8s_version + docker_version + node_count + pod_count + sa_count)` 记录每次会话的环境特征。Phase 9 模式进化的门槛②"探测可复现"就是靠这个 hash 判断"在 ≥2 个不同 host_fingerprint 环境命中"——同样攻击路径在两个不同环境复现，才证明它是真模式而不是单环境偶发。

---

## 六、反幻觉核心机制——为什么大模型会编造漏洞

这是 GenCPT 区别于传统 LLM 单对话渗透测试的核心。理解了这一节，就理解了 GenCPT 为什么要有那么多纪律。

### 6.1 什么是"幻觉"，为什么 LLM 会编造攻击

**幻觉**（hallucination）是指 LLM 一本正经地输出不存在的东西。比如你问它"这台机器 docker.sock 可不可写"，它没真跑 SSH，但会根据 Pod 配置"猜"——"嗯这个 Pod privileged=true，那 docker.sock 肯定可写"。语气很自信，但实际可能 AppArmor 拦着、可能 socket 根本没挂载进来。你不实跑根本看不出是编的。

在容器渗透里幻觉特别危险，因为 LLM 会：

- **编造攻击路径**：硬说"这个容器能 nsenter 进宿主机"，但实际 nsenter 在容器里根本不可用
- **伪造 SSH 输出**：说"`docker ps` 输出多出一个 alpine 容器证明逃逸成功"，但 SSH 命令根本没跑
- **脑补前置条件**：没真查 AppArmor 就说"无安全机制阻断"
- **合理化误报**：看到 `privileged=true` 就说"高危逃逸"，但不追查宿主机有没有 docker.sock、有没有 hostPath 实际能逃

GenCPT 防幻觉的核心思路是**结构性榨出证据**：把 C1 判定变成"举证责任"——LLM 必须提出 5 项门槛证据 + L0 差分观测 + 审批通过，不是"我觉得这条逃逸能成立"。再加上反幻觉 6 条 + 三层 QA + 安全熔断，把幻觉概率压到可控。

### 6.2 6 条约束的违反后果

违反任一条对应 WU 的 `status` 置为 `failed`，由 supervisory-agent 决定重试或降级。具体后果：

| # | 约束 | 违反后果 |
|---|------|---------|
| 1 | 不准凭记忆出攻击命令 | 该 WU 重跑（必 Read 模式/规则文件后才执行） |
| 2 | 不准伪造 SSH 输出 | 该判定撤销，重跑 ssh_execute |
| 3 | 无证据不写确认态 | `[x]` 降级 `[?]` 或 `[!]` |
| 4 | 占位符必替换 | 报告拒收 |
| 5 | 超出审批立即停 | 终止当前 Phase |
| 6 | baseline 永不替代当前 | 该项重审 |

### 6.3 几条最关键的约束

- **#1**：不准凭记忆出攻击命令——必须 Read 模式 SKILL.md 后才执行探测。这是防止 LLM 脑补"我记得 nsenter 这么用"导致命令出错或更糟——正确命令不存在模式库里。
- **#2**：不准伪造 SSH 输出——每条 path/output 必来自实际 ssh_execute 返回。防 LLM 凭印象编证据。
- **#3**：无证据不写确认态——`[x]` 必须有差分证明，`[?]` 需标注待验证原因。防 LLM 草率下结论。
- **#5**：超出审批立即停——L5 操作不生成执行命令、超时降级为理论验证。防 LLM 幻觉级联导致高破坏性命令连续自动审批（配合安全熔断）。
- **#6**：baseline 永不替代当前——上次会话 pass 的规则不影响本次判定，每条必重新执行检测。防 LLM 偷懒"上次 pass 这次也 pass"。

### 6.4 安全熔断——防 LLM 幻觉级联

详见 §2.10 的 5 级审批门控和安全熔断机制。这里补充解释为什么需要熔断：

LLM 的一个典型幻觉模式是"自我合理化级联"——当一个 L3/L4 操作被自动通过时，LLM 可能觉得"既然这个能跑那相似的也都能跑"，连续触发多个高破坏性命令，把目标环境搞乱。安全熔断兜底防护：10 分钟内 ≥5 次 L3/L4 自动通过 → 强制下一个 L4 manual approval，暂停自动审批让用户人工介入判断。熔断事件入 `evidence/qa/circuit_breaker_event.md`。

熔断机制不改变审批级别定义，只在异常频率时插入一个暂停点。正常频率的 L3/L4 操作不受影响。

### 6.5 三层 QA 校验——最终交付的关键门禁

详见 §Phase 8 已讲。补完整逻辑：

1. **第一层结构校验**（不可 Override）：MUST 输出文件存在 + 知识图谱边节点对应 + ATK-CAND 编号连续 + 五态无 `[ ]` 残留。失败即报告拒收。意义是防 LLM 偷懒——必须的文件没写、ATK-CAND 编号跳号、`[ ]` 留着不管，都是结构问题。
2. **第二层语义校验**（可 Override 但需记录原因）：抽 5 条合规 + 3 条 ATK-CAND + 2 条 `[-]` 重新跑 ssh_execute 验证。意义是抽样复查 LLM 判定是否真的基于 SSH 输出——可能 LLM 早期判定对了但环境变了，重新跑一遍验证当前状态。
3. **第三层覆盖校验**（不可 Override）：7 攻击面矩阵无空白 + 226 条合规规则全有判定。**这是强制全覆盖的最后一道防线**——即使某规则在你环境是 `na`，也必须显式标 na 加原因，不许"没查就算了"。

第三层校验失败即拒收报告——这一条保证了 GenCPT 不会"漏报某一类规则"，间接保证了每隔攻击面都被覆盖。

---

## 七、设计哲学——为什么这么设计

### 7.1 为什么用纯 Markdown SKILL 不用代码

GenCPT 全套件 106 个文件全是 Markdown / JSON / YAML，**零 Python 脚本做分析判定**——脚本只做 `jq` 查 JSON、`wc -l` 统计、`mkdir` 建目录这些杂活，所有判定逻辑由 LLM 语义产出。

为什么这么极端？因为代码化的判定逻辑会"硬化"——一旦写成 Python 函数 `is_privileged_vuln(pod)`，就只能按写死的逻辑判断"privileged=true 是漏洞"。但实际安全判定是动态的——同一个 `privileged=true`，环境 A 有 AppArmor 就不算 C1，环境 B 没防护就是 C1。让 LLM 语义判断能根据上下文动态决定可信度。

代价是 LLM 会幻觉——但 GenCPT 用 6 条反幻觉 + 三层 QA + 安全熔断 + 攻击者视角分层 + 差分证明强制，把幻觉压到可控。这个权衡是划算的——灵活性远超硬编码，幻觉可控。

### 7.2 为什么 Phase 间不直接传数据而用知识图谱

每次判定要用的数据可能源自好几个 Phase 的产出——攻击验证要读 Phase 1a 的侦察数据、Phase 2 的合规结果、Phase 3 的交叉关联。如果 Phase 之间直接传内存对象，上下文窗口会爆。

GenCPT 的设计是：**每个 Phase 把结构化结果写成 JSON 节点/边存到 `knowledge_graph/`，后续 Phase 按节点 ID 反查图谱不重跑数据收集**。这样：
- 每个 Phase 的上下文里只放当前需要的那几条节点，不大不小
- 中断可恢复——图谱文件持久化，重启后从 `progress.json` 找最后未完成 WU 继续读图谱
- 跨 Phase 追溯可查——`ATK-CAND-001` 引用了 Phase 3 的 `cross_ref` 边，边又引用了 Phase 2 的 `finding` 节点，一路反查到原始 SSH 输出

这种"图谱解耦 + 节点 ID 反查"是 Phase 间零耦合的关键，也是大集群不爆上下文的核心机制。

### 7.3 为什么 supervisor 只调度不执行

Pipeline 入口 SKILL.md（`/root/gencpt/SKILL.md`）明文规定：

- "**不执行检测命令**：只收集参数、调度子技能和展示结果，不在远程服务器执行检测命令"
- "**不读取原始检测数据**：原始数据由各 Phase 的子技能 SKILL 负责读取和处理"
- "**不跳过 Phase 间数据传递**：Phase 间数据通过知识图谱文件传递，不可直接在 Phase 间传内存数据"

为什么 supervisor 只调度不执行？因为如果 supervisor 既调度又执行，它的上下文窗口会被一堆 SSH 原始输出填满，会话压缩丢数据，调度就会出错。所以严格分层——supervisor 只管调度和摘要展示，执行交给子代理（每个子代理独立上下文窗口），子代理执行完返回 ≤500 token 的摘要，原始数据立即写盘。

这种"调度者不执行，执行者不调度"原则借鉴自 Ansible/Terraform 这类编排工具的设计哲学，但 GenCPT 更极端——连子代理之间也不直接传数据，全走图谱文件。

### 7.4 为什么不可利用项也要入覆盖矩阵

攻击面覆盖矩阵（全景报告第 4 章）要求：**已证伪的不可利用项也必须出现在覆盖矩阵中**，标注"已检查不可利用 + 证伪依据"。

为什么？因为甲方最怕的不是"发现了多少漏洞"，而是"你到底有没有全覆盖"——传统工具没法答这题，甲方就只能凭感觉信或不信。

GenCPT 用覆盖矩阵明确告诉甲方：
- AS-5 DoS：跑了 2 个模式（resource-abuse 确认不可利用证伪依据"无资源限制但 limit range 已配"；fork-bomb 因 L5 不可安全复现只做理论验证）
- AS-1 逃逸：12 个模式跑了 8 个，4 个因平台不符跳过（如纯 K8s 不跑 runc-escape）

这样甲方看到的不是"我发现了多少漏洞"，而是"我把 7 个攻击面/49 个模式/226 条规则都查完了，查了多少、跳了多少、为什么跳、不可利用的证据是什么"。这是从"看运气"变成"可度量"。

### 7.5 为什么攻击模式能自我进化

传统攻击模式库都是人工策展的静态库——攻击者发明新手法，安全研究员手工加新模式，慢还容易忘。GenCPT 的 Phase 9 把这个过程自动化：

1. Phase 4b 用 CoT+ReAct 推理发现模式库没覆盖的新攻击路径，写 `insights.md`
2. Phase 9 对每个 insight 评估 4 项晋升门槛（差分证明/可复现/无法匹配/跨会话命中）
3. 4/4 全过 → 用户审批（添加/拒绝/暂存）
4. 批准 → 写入 `_learned/` 目录，更新 `_index.md` + 假设库 + `_learned_index.md`
5. 老模式 15 次未命中自动问归档（不静默删）
6. 老模式 5 次命中自动升 high（反映它在实战中确实有用）

这样模式下"自然选择"——有用的升 high、没人命中的归档、新模式自动加入。**模式库跟随攻防态势演化**，越用越强。

为什么不直接自动晋升？因为 LLM 推理发现可能本身就有幻觉——比如一个"新攻击路径"实际只是某现有模式的变体伪装。所以晋升必须经 4 项门槛 + 用户审批双门控，防 LLM 自我合理化导致的模式污染。

### 7.6 为什么 9 个 Phase 不能合成 3 个

3 个 Phase 版本（扫环境→报漏洞→出报告）无法保证"不漏报 + 不误报 + 可复现"：

- **漏报**：没有 Phase 4b LLM 推理补盲，模式库没覆盖的攻击路径必漏
- **误报**：没有 Phase 6 5 级审批 + 差分证明，"前置可能满足"硬标 C1 的偷懒没法拦
- **不可复现**：没有 Phase 4a L0/L1/L2 分层差分证明，同一个 Pod 跑两次结果可能不稳定

9 个 Phase 拆开后，每 Phase 产证据，每 Phase 责任单一。最终交付物里每条 C1 都能反向溯源到 L2 差分证明 + 5 项门槛证据 + ATK-CAND 节点 + 合规 fail 节点 + SSH 原始输出 + 攻击模式 SKILL.md（若 LLM 补盲候选还有 ReAct 推理链），一并留底。

### 7.7 为什么 root 仅做 L0

前面 §5.1 已讲。补一个反例说明问题：

假设一个 BAS 工具在 prod-k8s-01 上拿 root 跑 `nsenter -t 1 -m -- ls /etc/shadow` 成功了。它说"逃逸成功！高危！"。甲方慌了。但仔细复盘——这个 root 是宿主机的 root，他本来就能读 `/etc/shadow`。所谓"逃逸成功"只是证明"宿主机 root 神通广大"，跟容器内攻击者能不能逃出来毫无关系。

GenCPT 的做法：同一个 Pod 用 L2 视角跑——`kubectl exec <pod> -- nsenter -t 1 -m -- ls /etc/shadow`。如果攻击者从容器内真能 nsenter 进宿主机 PID 命名空间，那才证明逃逸成立。如果失败（如 AppArmor 阻断 nsenter），那就标 C2 condition_met 或 ❌ 不可利用——而不是像 BAS 那样骗甲方。

**这就是为什么 root 只做 L0**——root 神通广大不是漏洞，容器内低权限攻击者能突破隔离才是漏洞。

---

## 八、与其它工具对比

### 8.1 GenCPT vs 传统 BAS / 扫描器

| 维度 | kube-bench / docker-bench | BAS（Atomic Red Team 等） | **GenCPT** |
|------|---------------------------|--------------------------|------------|
| 检测对象 | CIS 合规配置 | 攻击行为预写脚本 | 配置 + 攻击路径 |
| 攻击视角 | 无 | 宿主机 root 跑 | 容器内 L1/L2 视角复现 |
| 证明能力 | 证明配置不合规 | 证明宿主机 root 能干啥 | 证明容器内攻击者能逃出来 |
| LLM 语义 | 无 | 无 | 有（理解配置组合语义） |
| 分级 | pass/fail | 成功/失败 | C1/C2/C3 + 不可利用 + 已阻断 |
| Full 模式时长 | 分钟级 | 分钟级 | 30 分钟+ |
| 模式库进化 | 静态 | 静态 | 4 门槛 + 自净自动进化 |
| 攻击链 | 无 | 单点 | 多步攻击链 + 可达性评估 |
| 覆盖矩阵 | 无 | 无 | 7 攻击面 × 模式库/LLM/总覆盖 |
| 盲区提示 | 无 | 无 | Top 3 必显式列 |
| 反幻觉约束 | N/A | N/A | 6 条 + 三层 QA + 安全熔断 |

### 8.2 GenCPT vs SourceCPT

GenCPT 和 SourceCPT 是同一作者、同 CPT 后缀，但前缀和检测对象完全不同：

| 维度 | SourceCPT | GenCPT |
|------|-----------|--------|
| 前缀 | Source（源代码） | Gen（生成式 AI） |
| CPT 解读 | Code Penetration Test 代码渗透 | Container Penetration Test 容器渗透 |
| 检测对象 | 本地源码 | 远程运行时容器环境 |
| 检测方式 | 白盒静态审计（不用执行） | 黑盒运行时检测（必须 SSH 远程执行） |
| 来源数据 | Read 源码文件 | ssh_execute 远程命令输出 |
| Phase 数 | 17 Phase（14 必跑 + 3 可选） | 9 Phase + 1b/2a/2b/2c/4a/4b/8a/8b/8c 拆分 |
| 深度分层 | T0-T3（代码读得多深） | L0-L3（攻击在哪个视角执行） |
| 可信度层级 | C3 风险线索 / C2 条件成立 / C1 已确认 | C3 风险线索 / C2 条件实证 / C1 实证复现 |
| 攻击模式库 | 41 个模式（OWASP 漏洞） | 49 个模式（MITRE ATT&CK 7 攻击面） |
| 合规模块 | 编码合规 7 分组 | CIS Benchmark 226 条 |
| 挑战者对抗 | Phase 6 独立对抗 + 六项验收 | Phase 6 5 级审批 + 5 项门槛 |
| 进化闭环 | Phase 9 4 门槛+自净 | Phase 9 4 门槛+自净（结构相同） |

两者互不依赖——T0-T3 白盒深度 vs L0-L3 黑盒运行时本质不同，但共享很多设计机制：反幻觉约束、Pipeline 编排、三库联动、Phase 间图谱解耦、模式进化闭环、可信度三态、五态标记。SourceCPT 早期开发时借鉴了 GenCPT 的反幻觉 6 条 + Pipeline 编排 + 三库联动等 11 项机制。

---

## 九、Q&A 常见疑问——常见疑问解答 + 术语表

### Q1：为什么不直接用 kube-bench / trivy / Aqua？

kube-bench 只能证明 CIS 合规 fail，证明不了利用可能性；trivy 主要扫镜像 CVE，扫不了运行时配置；Aqua 是商业 CSPM 工具但攻击验证能力弱。GenCPT 同时做合规 + 攻击链验证 + LLM 推理补盲 + 模式进化，把"配置不合规"自动升级为"配置不合规且攻击者真能逃出来"。

### Q2：9 个 Phase 不会太慢吗？

有 3 种 mode：
- **fast**（10 分钟）：跳 Phase 3-7，只跑 Phase 1a→2→8a→8c（合规基线报告）
- **full**（30 分钟+）：全 9 Phase 完整渗透测试
- **custom**：用户指定检测项

不同满足不同场景——快速摸底用 fast，授权完整测试用 full。

### Q3：跑一次要多少 token（AI 处理量单位）？

fast 模式约 1-2 亿 token；full 模式小型集群（3 节点 50 Pod）约 3-5 亿；大集群（30 节点 500+ Pod）按 namespace 分批可能 8-15 亿。智能派发按 scope 过滤平台 + WU 分批并发 + 按需加载模式（不一次性读 49 个模式）+ jq 过滤后读（不读整个 JSON 文件）控上下文爆炸。

### Q4：全 LLM 语义判定会不会漏报？

Phase 4b LLM 推理补盲是漏报最后防线——对 4a 模式库未覆盖的盲区候选 CoT+ReAct 推理补，新候选标 `source=llm_reasoning`、`five_state=[?]`，Phase 6 验证从严（必须 5 项门槛全过）。但 LLM 推理本身有限度——10 轮 ReAct 跑不完标 partial_insufficient 退出留人工。

### Q5：它和 SourceCPT 什么关系？

同一作者、同 CPT 后缀、不同前缀——GenCPT 是容器渗透（黑盒运行时），SourceCPT 是源码审计（白盒静态）。互不依赖但有共同设计机制。详见 §8.2。

### Q6：大集群（30 节点 500+ Pod）跑得动吗？

跑得动但不快。通过三层机制：
- **写入层**：findings 按平台分片 + results.jsonl 立即追加不积批 + audit_log 按 Phase 分文件
- **读取层**：jq 过滤后读（禁 Read 整个 JSON）+ jq 输出 ≤1000 行截断 + 按需加载模式 SKILL.md
- **执行层**：每批 100 Pod + 最大 3 并行 SSH + 批次间隔 2 秒 + 断点续传

慢但完整——慢一些不怕，怕的是漏报和丢数据。

### Q7：子代理会不会偷懒只写统计不写实际节点？

不会。每个 Phase 的 MUST 输出文件都有非空硬门：`hosts.json`/`pods.json`/`containers.json`/`service_accounts.json` 四个必须存在且数组非空、`pods.json` 每个 Pod 必含 `security_context`、五态无 `[ ]` 残留。子代理只写统计摘要不写节点数组 → 该 Phase 标 `blocked` 不许标 `complete`。

### Q8：不支持真实并发时怎么办？

启动前确认能否创建独立子代理（Task(general)）。不能则写 `pipeline_blocked.md` 说明阻塞环节、已落盘产物、未运行 Phase 和继续条件，终止。**禁顺序模拟冒充完整流水线**——大集群顺序跑会上下文压缩丢数据，必须真实并发或阻塞。

### Q9：启动时我怎么知道有哪些参数可选？

即使用户只输入"用 GenCPT 对服务器 prod-k8s-01 做渗透测试"，LLM 也必须先用 question 工具一次性批量询问全部 5 个参数（mode / scope / approval / source-path / baseline），让用户看到全套配置再开始。禁默念默认值直接跑。这是反幻觉的精神——让用户对本次测试任务有完整全景认知。

### Q10：差分证明和审批门控有什么关系？

差分证明是攻击前快照 + 攻击执行 + 攻击后对比的可观测证据，证明"攻击真的改变了环境"——是 C1 门槛之一。审批门控是授权层面——证明这次操作得到了适当授权（L1 自动 / L2 标准 / L3 快速 / L4 手动 / L5 理论）。

两者关系：差分证明的结果会被审批门控记录下来——若差分证明充分但走的是 L5 理论验证，最终只能 C2 condition_met，不能 C1。差分证明和审批门控共同决定可信度。

### Q11：模式进化会不会污染模式库？

不会。4 项晋升门槛卡得很死：
1. 差分证明充分——必须有 2 个可观测差异 + SSH 输出证据
2. 探测可复现——必须在 ≥2 个不同 host_fingerprint 环境命中
3. 无法匹配现有模式——必须与 49 个现有模式 + 25 张假设卡片的前置和路径都不一致
4. 跨会话命中 ≥2 次——session_history.md 中相同或高度相似 ATK-CAND ≥2 次

4/4 全过 → 用户审批（添加/拒绝/暂存）。LLM 自我合理化的"新发现"基本过不了——因为它往往是某现有模式的变体（门槛③拦），或者只在单环境偶发（门槛②拦），或者本次会话首次发现（门槛④拦）。

### Q12：发现一条 C1 攻击链后能在生产环境直接复现吗？

不能直接复现。C1 的"可恢复"门槛要求"有清理命令恢复原状态"——POC 脚本必含 cleanup 步骤执行后清理临时容器、临时文件。但即使有 cleanup，生产环境也不建议直接跑 POC——建议在测试环境或灰度 Pod 上复现。

GenCPT 的设计是"证明可能性"而非"实际攻击"——C1 漏洞证明"这条路径真能逃出来"，甲方据此排期修复，不是说"GenCPT 在生产环境成功打穿了"。

---

## 术语表

| 术语 | 含义 |
|------|------|
| Phase | Pipeline 单步，9 Phase 顺序执行（拆分后 13 个调度单元） |
| SKILL.md | 单 Phase 或 Pipeline 入口的指令文本 |
| WU | Work Unit（工作单元），单子代理任务，处理一组规则/一个模式/一条链 |
| session_dir | `/tmp/gencpt-{session_id}/`，全 Phase 产物落盘根 |
| env_fingerprint | session_config.json 里的环境指纹（OS/arch/kernel/runtime） |
| env_hash | sha256(k8s+docker+node+pod+sa_count)，模式进化跨环境判断依据 |
| knowledge_graph | 7 类节点 + 5 类边的 JSON 知识图谱 |
| ATK-CAND | 攻击候选，Phase 3/4a/4b 产出 |
| CHAIN | 攻击链，Phase 5 构建多步利用链 |
| C1 | 实证复现，5 项门槛 + L2 差分充分 |
| C2 | 条件实证，前置满足但被阻断或不可安全复现 |
| C3 | 风险线索，配置有隐患但前置不完全满足 |
| 不可利用 | ➖ disproved，前置条件不满足（证伪） |
| 已阻断 | 🛑 blocked，被安全机制阻断 |
| L0 | 宿主机观察执行层级（可用 sudo） |
| L1 | 容器内观察执行层级（kubectl exec） |
| L2 | 容器内攻击验证执行层级（kubectl exec + 差分框架 + 审批） |
| L3 | 条件验证执行层级（不执行破坏性，理论推导 ⚠️） |
| 5 级审批门控 | L1 自动 / L2 标准 / L3 快速 / L4 手动 / L5 理论 |
| 安全熔断 | 10 分钟内 ≥5 次 L3/L4 自动通过 → 强制 manual |
| 5 项确认门槛 | 前置可复现 / 可执行 / 可区分 / 影响可观测 / 可恢复 |
| 差分证明 | 攻击前快照 + 攻击执行 + 攻击后对比，≥2 个可观测差异 |
| 五态标记 | `[x]` 已确认 / `[?]` 疑似 / `[-]` 不适用 / `[!]` 环境干扰 / `[ ]` 未检查 |
| AS-1~AS-7 | 7 大攻击面：逃逸/认证授权/网络/数据泄露/DoS/供应链/持久化 |
| CIS Benchmark | 互联网安全中心的容器安全配置基线 |
| CHK-CAND | 合规假设库（35 张卡片） |
| ATK-HYP | 攻击假设库（25 张卡片） |
| XREF | 交叉查询模板（3 条：叠加/组链/盲区） |
| 三库联动 | CHK-CAND → ATK-HYP → XREF，从发现问题到证明问题 |
| CoT | Chain of Thought 思维链，逐步推理 |
| ReAct | Reasoning + Acting，每步推理后执行动作 |
| insights | Phase 4b LLM 推理产的候选新模式 |
| _learned/ | Phase 9 晋升的永久模式目录 |
| baseline | 上次测试报告，仅用于 diff 对比，永不替代当前 |
| QA 三层校验 | 结构层 / 语义层 / 覆盖层，第三层不可 Override |
| 覆盖矩阵 | 7 攻击面 × 模式/LLM/总覆盖，不可利用项必入矩阵 |
| attack-patterns | 攻击模式库，49 模式 / 7 攻击面 / 8 段格式 |
| compliance-rules | CIS 合规规则库，3 平台 226 条 |
| hypothesis-libraries | 假设库，3 库联动共 185 张卡片 |
| 方法 C 混合渐进 | 原生命令优先 + 专用工具按需上传 SHA256 校验 + 失败自动回退 + 自动清理 |
| MCP | Model Context Protocol，给 AI 提供外部工具的协议 |
| ssh-manager MCP | SSH 远程工具的 MCP 插件 |
| JSON Lines | 每行一条 JSON 的追加写入模式，断点续传防丢数据 |
| 平台分片 | K8s/Docker/Containerd 写各自分片文件，Phase 2 完成后串行汇总 |
| 条件触发表 | _index.md 里 25+ 条触发信号→模式映射，Phase 4a 按需加载模式 |
| suite_version | 套件版本，baseline 版本兼容性检查依据 |
| Task(general) | opencode 的子代理调用方式，每个子代理独立上下文窗口 |
| supervisory-agent | 调度者角色，只调度不执行，不读原始检测数据 |
| opencode | AI 编程助手命令行工具，GenCPT 的运行宿主 |

---

## 完整链路——一个 C1 实证的完整数据流

最后用一个完整的端到端示例串起整个流程（虚构示例，引用的是 GenCPT 各 Phase 的真实实现）：

```
Phase 1a ──→ SSH 侦察 prod-k8s-01（3 节点 / 47 Pod / 9 SA / 12 Secret）
             知识图谱：7 类节点 + infra 关系边
             recon_summary 关键发现：
               pod/backend-api-xyz: security_context.privileged=[x] true
               pod/backend-api-xyz: mounts /var/run/docker.sock=[x]
               AppArmor=[-] docker-default（已启用）
             env_fingerprint 指纹写入 session_config.json

Phase 1b ──→ （未启用，无产出）

Phase 2a ──→ K8s 合规 134 条规则 4 个 WU 并发跑完
             K8s-5.2.1（不应 privileged=true）→ fail [x]
               证据：stat -c %a /etc/kubernetes/manifests/kube-apiserver.yaml → 644
             K8s-5.2.3（不应挂载 docker.sock）→ fail [x]
               证据：kubectl get pod -o yaml backend-api-xyz → mounts /var/run/docker.sock
             写 findings_k8s.json + compliance_k8s.json 分片

Phase 3  ──→ 三库联动：
             K8s-5.2.1(fail) → CHK-CAND-002 → escape/socket-escape (ATK-HYP-001)
               标记: [x] 前置条件可能满足
               ATK-CAND-001: 特权容器+docker.sock逃逸
             LLM 动态推理未补充新映射（静态库命中充分）

Phase 4a ──→ 按 _index.md 触发表加载 socket-escape 模式 SKILL.md
             2.2 探测：
               [L0] ls -l /var/run/docker.sock → srw-rw---- 1 root docker 0 ...
               [L1] kubectl exec backend-api-xyz -- ls -l /var/run/docker.sock
                 → srw-rw---- 1 root docker 0 ...
               前置条件 ✅ 全部满足
             2.4 攻击验证（L2，auto 模式自动通过）：
               [L0] docker ps -q → （无）
               [L2] kubectl exec backend-api-xyz -- \
                   docker run -v /:/host alpine ls /host/etc/shadow
                 → root:x:0:0:root:/root:/bin/bash
               [L0] docker ps -q → （多一个 alpine 容器）
               [L0] docker rm -f <alpine_id> → 清理完成
             2.5 生成 ATK-CAND-001:
               verification_level: L2, context: container, confidence: C1
               差分证明2项可观测差异 + SSH输出文件路径

Phase 4b ──→ Phase 4a 已匹配全部候选，无新增 insights

Phase 5  ──→ 提取 C1 ATK-CAND-001 作为链起点
             图谱查可达路径：backend-api-xyz → uses_sa → sa-backend-api
             假设逃逸后能拿宿主机 docker 控制权 → 能访问 etcd
             构造 CHAIN-001（深度 2）：
               step 1: socket-escape (ATK-CAND-001) → 宿主机访问权
               step 2: etcd-unauth-access (假设) → 读全集群 Secret
             评估：confirmed_partial（step1已验证，step2依赖step1理论）

Phase 6  ──→ 逐链验证：
             step 1 (socket-escape)：
               前置 ✅ / L2 攻击 ✅ / 差分 ✅ 充分 / C1
             step 2 (etcd-unauth-access)：
               前置 ⚠️ 部分满足（etcd 网络未实测）
               L3 条件验证 (假设 etcd 2379 可达)
               差分 ⚠️ 不充分 → C2
             审批：step1 L2 auto 通过 / step2 L3 自动通过
             最终链可信度判定：C2 条件实证 ✅
               原因：step1 C1 实证，step2 依赖 step1 后果理论推导
                     但差分证明不足
             检查安全熔断：本次 L3 自动通过 < 5，不触发

Phase 7  ──→ 对 CHAIN-001 生成 POC 脚本（C2 condition_met 可产 POC）
             evidence/poc/poc_scripts/POC-001-socket-escape.sh
             含 [L0]/[L2]/[L0] 三段式 + cleanup 步骤
             占位符 {{target_host}} / {{target_namespace}} / {{target_pod}}

Phase 8a ──→ 合规报告：226 条规则判定 + 阈值矩阵 + 违规详情
Phase 8b ──→ 攻击报告 CHAIN-001：socket-escape → etcd-read
Phase 8c ──→ 全景报告 10 章 + QA 三层校验 + 攻击面覆盖矩阵
             2.5 章 ⚠️ 最大检测盲区 Top 3：
               1. Phase 1b 源码扫描未执行 — 未传 source-path
               2. fork-bomb 因 L5 不可安全复现只做理论验证
               3. AS-3 网络 lateral-move 在不可达 worker 节点未验证

Phase 9  ──→ （未启用 --evolve，跳过）
```

最终交付：合规报告 + 攻击报告 + 全景报告 + POC 脚本包 + 知识图谱 + QA 报告，全产在 `/tmp/gencpt-{session_id}/reports/` 和 `/tmp/gencpt-{session_id}/evidence/` 下，session 完整保留供未来复测或验证审查。

---

> 看完 9 大节，即可完整复盘 GenCPT 全套件各维度。仍想细查某 Phase/机制，按文中引文跳转到对应 SKILL.md / shared/ / attack-patterns/ / compliance-rules/ / hypothesis-libraries/ 文件 Read 原文。
>
> ——