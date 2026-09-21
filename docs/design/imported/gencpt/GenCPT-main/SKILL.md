---
name: gencpt
description: >
  容器与 Kubernetes 渗透测试技能套件（opencode SKILL），不是代码程序。通过 SSH 远程对 K8s/Docker/containerd 环境做合规检测、攻击验证、链式攻击和报告交付。支持攻击模式库自我进化。所有逻辑由 LLM 语义处理，产出物是 Markdown 报告和 JSON 知识图谱。SKILL 全部为中文指令。
  使用场景：对 K8s/Docker/containerd 环境做授权渗透测试。
  不使用场景：未授权攻击、生产破坏性操作、批量扫描非自有目标。
---

# GenCPT — Pipeline 入口 SKILL

## §0 套件根定位（所有子 Phase 启动第一步，强制）

本套件用相对套件根的路径引用共享规范与知识库：
- `skills/shared/`（6 个共享规范：SSH_COMMANDS / SEVERITY_RATING / VULNERABILITY_GROUPING / QA_OVERRIDE_TRACKING / OUTPUT_STANDARD / LOOP_POLICY）
- `attack-patterns/_index.md`
- `compliance-rules/_index.md`
- `hypothesis-libraries/X.md`

这些路径**相对套件根**，**不相对 cwd**。LLM 直接拿 cwd 拼接会被解析到错位。

LLM 在**第一次 Read 任何相对引用前**必**先调 opencode 内置 Glob 工具**定位套件根。Glob 模式按以下顺序尝试，首个命中即用：

```
Glob pattern 1: **/skills/shared/SSH_COMMANDS.md
Glob pattern 2: **/gencpt/SKILL.md
Glob pattern 3: **/GenCPT*/SKILL.md
```

- pattern 1 命中 → 套件根 = 命中路径**向上两级**（如 `.../GenCPT-main/skills/shared/SSH_COMMANDS.md` → 套件根 = `.../GenCPT-main`）
- pattern 2/3 命中 → 套件根 = 命中路径的**父目录**（如 `.../gencpt/SKILL.md` → 套件根 = `.../gencpt`）

不硬编码套件根路径，取 Glob 实际命中结果。**入口 SKILL 找到套件根后，必在后续子代理调度子 Phase 时把套件根绝对路径作为参数传入**（见 §4 调度模板），子 Phase 不再重复 Glob。

所有后续 Read 共享规范/知识库的调用，**把套件根绝对路径前缀拼到原引用前**：
- SKILL 写 `skills/shared/SSH_COMMANDS.md` → Read `<套件根>/skills/shared/SSH_COMMANDS.md`
- SKILL 写 `attack-patterns/_index.md` → Read `<套件根>/attack-patterns/_index.md`

**重要**：Read 工具吃字串不展开 shell 变量，禁用 `$ROOT/...` 形式。必先用 Glob 命中拿到完整绝对路径，再拼前缀。**不许凭记忆猜套件根路径**。

**session-dir 定位**：session-dir 必在**系统临时目录**下创建，**绝对不能**放到套件根内部（否则污染套件源码）：
- Linux/macOS：`/tmp/gencpt-{session_id}/`
- Windows PowerShell：`$env:TEMP\gencpt-{session_id}\`

LLM 必先检测平台（试 `$PSVersionTable` 不报错是 PowerShell，报错是 bash），选对应路径。**禁用相对路径**（会落到 cwd 而不是系统 temp）。

---

本 SKILL 是容器渗透测试套件的**唯一入口**，负责参数收集、环境验证、工作目录初始化、按顺序调度各 Phase 子技能、展示摘要。**不直接执行任何检测逻辑**，而是通过子代理调用依次调用各 Phase 的子技能 SKILL.md。

---

## 参数格式定义

| 名称 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `server` | string | **是** | — | 目标服务器名称（来自 ssh-manager 配置） |
| `mode` | enum | 否 | `full` | `fast` / `full` / `custom`，详见下方 |
| `scope` | enum | 否 | `all` | `k8s` / `docker` / `containerd` / `all`，详见下方 |
| `approval` | enum | 否 | `standard` | `standard` / `express` / `manual`，审批模式 |
| `source-path` | string | 否 | — | 手动指定的攻击模式路径（覆盖默认知识库） |
| `baseline` | string | 否 | — | baseline 报告路径，用于 diff 对比（baseline 永不替代当前测试） |

### mode 参数选项

| 选项 | 说明 |
|------|------|
| `fast` | 跳过 scan 阶段和 custom 只检查指定项，快速出合规基线报告 |
| `full` | 执行全部 Phase（recon → compliance → attack → chain → report），完整渗透测试 |
| `custom` | 由用户指定要执行的检测项列表，只检查指定项 |

### scope 参数选项

| 选项 | 说明 |
|------|------|
| `k8s` | 仅检测 Kubernetes 环境 |
| `docker` | 仅检测 Docker 环境 |
| `containerd` | 仅检测 containerd 环境 |
| `all` | 检测所有可用平台（取并集） |

---

## 第一步：参数收集

**强制交互确认机制**：即使用户只传了 `server`（如"对服务器 prod-k8s-01 做渗透测试"），LLM **不许直接用默认值跑**。必先用 `question` 工具向用户确认全部参数：

### 1.1 必填参数（无默认值，缺则终止）

| 参数 | 必填 | 用户未传时行为 |
|------|------|-------------|
| `server` | **是** | 若缺失 → **立即终止**并报错"必须指定目标服务器" |

### 1.2 默认值参数（必须交互确认）

即使用户只传了 server，以下参数也**必须用当前环境的用户交互工具逐一询问**用户是否接受默认值：

| 参数 | 默认 | 确认说明 |
|------|------|---------|
| `mode` | `full` | "检测模式: full(完整9Phase, 30分钟+) / fast(仅合规, 10分钟) / custom(自定义项)。建议首次用full。接受full还是选其他?" |
| `scope` | `all` | "检测范围: all(K8s+Docker+Containerd) / k8s / docker / containerd。接受all还是指定?" |
| `approval` | `standard` | "审批模式: standard(标准) / express(快速) / manual(手动)。接受standard还是选其他?" |

### 1.3 可选参数（也必须问，让用户知道全景）

| 参数 | 默认 | 确认说明 |
|------|------|---------|
| `source-path` | — | "是否有源码目录供源码扫描(Phase 1b)? 输入路径或跳过" |
| `baseline` | — | "是否有上次测试的baseline目录供diff对比? 输入路径或跳过(首次测试无baseline)" |

### 1.4 交互流程

```
用户输入: "用 GenCPT 对服务器 prod-k8s-01 做完整渗透测试"

LLM 提取 server = prod-k8s-01 (必填, 已有)

LLM 必须用当前环境的用户交互工具一次性批量询问全部 5 个参数:
  Q1: "检测模式? full(完整9Phase, 30分钟+) / fast(仅合规, 10分钟) / custom — 默认 full"
  Q2: "检测范围? all(K8s+Docker+Containerd) / k8s / docker / containerd — 默认 all"
  Q3: "审批模式? standard / express / manual — 默认 standard"
  Q4: "有源码目录供源码扫描(Phase 1b)? 输入路径或跳过"
  Q5: "有上次测试baseline目录供diff对比? 输入路径或跳过(首次测试无)"

用户回答后 → 写 session_config.json → 进入第二步环境验证
```

**禁跳过确认直接跑**：即使用户说"你看着办"，LLM 可以用默认值不阻塞，但仍须在 session_config.json 里记录所有参数的实际值。

**目的**：让用户对本次测试任务有完整全景认知——知道启动了哪些能力、跳过了哪些能力。

---

## 第二步：环境验证

1. 使用 `ssh_execute` 对目标 server 执行 `echo "OK"` 测试 SSH 连通性
2. 收集环境信息：
   - OS 版本：`cat /etc/os-release`
   - 架构：`uname -m`
   - 容器运行时版本：`docker version` / `kubectl version` / `crictl version` / `ctr version`
3. 检查工具可用性：
   - kubectl：`which kubectl`
   - docker：`which docker`
   - crictl：`which crictl`
   - ctr：`which ctr`
4. 记录环境指纹到 `session_config.json`，包含：
   - hostname / os / arch
   - 容器运行时类型及版本
   - 可用工具列表
   - 节点数 / Pod 数（如可获取）

若 SSH 不通，**立即终止**并报告错误。

---

## 第三步：初始化工作目录

在 `/tmp/gencpt-<session_id>/` 下创建完整目录结构：

```
gencpt-<session_id>/
├── session_config.json
├── progress.json
├── audit_log.json
├── evidence/
│   ├── recon/
│   │   ├── raw/
│   │   └── summaries/
│   ├── compliance/
│   │   ├── k8s/
│   │   │   └── raw/
│   │   ├── docker/
│   │   │   └── raw/
│   │   └── containerd/
│   │       └── raw/
│   ├── attack/
│   │   ├── raw/
│   │   └── summaries/
│   ├── chains/
│   │   ├── raw/
│   │   └── summaries/
│   ├── poc/
│   │   ├── poc_scripts/
│   │   └── summaries/
│   ├── evolve/
│   └── qa/
├── reports/
│   ├── compliance/
│   ├── attack/
│   ├── summary/
│   └── panorama/
├── knowledge_graph/
│   ├── nodes/
│   └── edges/
└── tmp/
```

### Write 工具先 Read 协议

部分环境（opencode / Claude Code）的 Write 工具对已存在的文件要求先 Read 后 Write。初始化时用 bash 创建空 stub + 完整目录树：

```bash
# Linux/macOS — 一次性创建所有目录
mkdir -p {session-dir}/{evidence/{recon/{raw,summaries},compliance/{k8s/{raw},docker/{raw},containerd/{raw}},attack/{raw,summaries},chains/{raw,summaries},poc/{poc_scripts,summaries},evolve,qa},reports/{compliance,attack,summary,panorama},knowledge_graph/{nodes,edges},tmp}
# 初始化空 stub 文件
echo '{}' > {session-dir}/session_config.json
echo '{"phases":{}}' > {session-dir}/progress.json
echo '[]' > {session-dir}/audit_log.json

# Windows PowerShell
New-Item -Path {session-dir} -ItemType Directory -Force
Set-Content {session-dir}\session_config.json '{}'
Set-Content {session-dir}\progress.json '{"phases":{}}'
Set-Content {session-dir}\audit_log.json '[]'
```

bash 先建完整目录树 + 空 stub → 后续 Phase 要 Write 字段时先 Read 再 Write 合并。**禁不用 bash 而直接 Write 新文件**（裸 Write 会报错卡住）。

### 目录补全校验（初始化后强制执行）

初始化完成后立即校验关键子目录是否存在，缺失任一 → 重新执行 mkdir：

```bash
for d in evidence/recon/raw evidence/recon/summaries \
         evidence/compliance/k8s/raw evidence/compliance/docker/raw evidence/compliance/containerd/raw \
         evidence/attack/raw evidence/attack/summaries \
         evidence/chains/raw evidence/chains/summaries \
         evidence/poc/poc_scripts evidence/poc/summaries \
         evidence/evolve evidence/qa \
         reports/compliance reports/attack reports/summary reports/panorama \
         knowledge_graph/nodes knowledge_graph/edges tmp; do
  [ -d {session-dir}/$d ] || { echo "MISSING: $d"; mkdir -p {session-dir}/$d; }
done
[ -f {session-dir}/session_config.json ] && [ -f {session-dir}/progress.json ] && [ -f {session-dir}/audit_log.json ] || echo "STUB_MISSING"
```

### session_config.json 结构

```json
{
  "session_id": "<uuid>",
  "target": {
    "server": "<server>",
    "scope": "<scope>",
    "mode": "<mode>",
    "approval": "<approval>"
  },
  "env_fingerprint": {
    "os": "",
    "arch": "",
    "hostname": "",
    "container_runtime": "",
    "runtime_version": "",
    "available_tools": [],
    "node_count": null,
    "pod_count": null
  },
  "source_path": null,
  "baseline": null,
  "suite_version": "V1.1",
  "auto_high_risk_exec_count": 0,
  "created_at": "<ISO8601>"
}
```

### progress.json 结构

```json
{
  "phases": {
    "1a": {
      "status": "pending",
      "batches": {},
      "current_wu": null,
      "last_updated": "<ISO8601>"
    },
    "2a": {
      "status": "pending",
      "batches": {"WU-2a-01": "pending", "WU-2a-02": "pending", "WU-2a-03": "pending", "WU-2a-04": "pending"},
      "current_wu": null,
      "last_updated": "<ISO8601>"
    },
    "2b": {"status": "pending", "batches": {"WU-2b-01": "pending", "WU-2b-02": "pending"}, "current_wu": null},
    "2c": {"status": "pending", "batches": {"WU-2c-01": "pending"}, "current_wu": null},
    "3": {"status": "pending", "batches": {}, "current_wu": null},
    "4a": {"status": "pending", "batches": {}, "current_wu": null},
    "4b": {"status": "pending", "batches": {}, "current_wu": null},
    "5": {"status": "pending", "batches": {}, "current_wu": null},
    "6": {"status": "pending", "batches": {}, "current_wu": null},
    "7": {"status": "pending", "batches": {}, "current_wu": null},
    "8a": {"status": "pending", "batches": {}, "current_wu": null},
    "8b": {"status": "pending", "batches": {}, "current_wu": null},
    "8c": {"status": "pending", "batches": {}, "current_wu": null},
    "9": {"status": "pending", "batches": {}, "current_wu": null}
  },
  "current_phase": null,
  "last_updated": "<ISO8601>"
}
```

### 断点续传规则（batch级粒度）

1. 每个WU完成后由Phase子代理更新progress.json中对应WU状态为complete
2. WU崩溃/中断时，status保持in_progress，下次恢复时重跑该WU（从results.jsonl已有行续传）
3. 已complete的WU永不重跑
4. 每完成一个WU后立即写盘progress.json（不等整个Phase完成）
5. 会话压缩后，LLM必须先Read progress.json恢复进度，从第一个非complete的WU继续

---

## 第四步：按顺序调度各 Phase 子技能

本 SKILL 通过子代理调用依次调用各 Phase 子技能。每个 Phase 作为独立的 general 子代理执行，Phase 间数据通过知识图谱文件（`knowledge_graph/`）传递。

**子代理调用方式**：根据当前运行环境选择可用的调用方式——
- opencode 环境：`Task(general, prompt="...")` 或 `Task(subagent_type="general", prompt="...")`
- Claude Code 环境：`Task(subagent_type="general", prompt="...")`
- LLM 根据当前可用的工具自行选择，不硬编码调用语法

### 调度原则

1. **顺序执行**：按 Phase 1a → 1b → 2 → 3 → 4a → 4b → 5 → 6 → 7 → 8 → 9 顺序调度
2. **断点续传**：每个 Phase 开始前读取 `progress.json`，跳过已完成的 Phase
3. **失败处理**：某 Phase 失败时记录到 progress.json 并询问用户是否继续
4. **数据传递**：Phase 间不直接传数据，通过 `knowledge_graph/` 目录的 JSON 文件传递
5. **mode=fast 时跳过**：跳过 Phase 3-7（交叉关联、攻击验证、链构建、链验证、POC），只执行 Phase 1a → 2 → 8a → 8c
9. **并发能力确认（大集群必须）**：Phase 内部分批时用子代理调用启动并发执行。若当前运行环境**无法创建独立子代理**，LLM **不许顺序模拟冒充完整流水线**——写 `{session-dir}/pipeline_blocked.md` 说明实际阻塞环节、已落盘产物、未运行 Phase 和继续条件，终止。大集群顺序跑会上下文压缩丢数据，必须真实并发或阻塞。
10. **blocked 状态传播**：任一 Phase 标 `blocked`，后续依赖该 Phase 产出的所有 Phase 也标 `blocked`，不许带着缺失依赖继续跑产出垃圾候选。

### 调度流程

每个 Phase 的调用方式：

```
子代理调用示例（根据当前环境选择可用语法）：

Task(general, prompt="            ← opencode 写法
Task(subagent_type="general", prompt="  ← Claude Code 写法

内容：
  你是 GenCPT 的 {Phase名称} 子技能执行者。
  请读取 {套件根绝对路径}/skills/{phase-skill}/SKILL.md 并严格遵循其指令执行。
  
  套件根: {套件根绝对路径}
  所有相对路径（skills/shared/、attack-patterns/、compliance-rules/、hypothesis-libraries/、references/）均相对于此套件根。Read 时必须拼接套件根前缀。
  
  会话参数：
  - session_dir: {session_dir}
  - server: {server}
  - scope: {scope}
  - mode: {mode}
  - approval: {approval}
  
  执行完成后返回 WU 摘要（≤500 tokens）。
")
```

**套件根绝对路径**由 §0 的 Glob 定位获得，入口在调度每个子 Phase 前把 `{套件根绝对路径}` 替换为实际路径（如 `/root/.config/opencode/skills/gencpt` 或 `C:\Users\xxx\.config\opencode\skills\GenCPT-main`）。

### 各 Phase 调度顺序

| 顺序 | Phase | 子技能 SKILL.md | mode=fast 时 |
|------|-------|-----------------|-------------|
| 1 | Phase 1a 环境侦察 | `skills/recon/SKILL.md` | ✅ 执行 |
| 2 | Phase 1b 源码扫描 | `skills/recon-source/SKILL.md` | 仅当 source-path 提供 |
| 3 | Phase 2a K8s 合规 | `skills/k8s-compliance/SKILL.md` | ✅ 执行（scope 含 k8s） |
| 4 | Phase 2b Docker 合规 | `skills/docker-compliance/SKILL.md` | ✅ 执行（scope 含 docker） |
| 5 | Phase 2c Containerd 合规 | `skills/containerd-compliance/SKILL.md` | ✅ 执行（scope 含 containerd） |
| 6 | Phase 3 交叉关联 | `skills/cross-ref/SKILL.md` | ❌ 跳过 |
| 7 | Phase 4a 模式匹配 | `skills/attack-pattern/SKILL.md` | ❌ 跳过 |
| 8 | Phase 4b LLM 推理 | `skills/attack-reasoning/SKILL.md` | ❌ 跳过 |
| 9 | Phase 5 链构建 | `skills/chain-builder/SKILL.md` | ❌ 跳过 |
| 10 | Phase 6 链验证 | `skills/chain-verify/SKILL.md` | ❌ 跳过 |
| 11 | Phase 7 POC 生成 | `skills/poc-generator/SKILL.md` | ❌ 跳过 |
| 12 | Phase 8a 合规报告 | `skills/report-compliance/SKILL.md` | ✅ 执行 |
| 13 | Phase 8b 攻击报告 | `skills/report-attack/SKILL.md` | ❌ 跳过 |
| 14 | Phase 8c 全景报告 | `skills/report-summary/SKILL.md` | ✅ 执行 |
| 15 | Phase 9 模式进化 | `skills/evolve/SKILL.md` | ❌ 跳过（仅 --evolve 时） |

### 断点续传

每个 Phase 调用前：
1. 读取 `progress.json`，检查该 Phase 状态
2. 若状态为 `complete`，跳过
3. 若状态为 `in_progress` 或 `failed`，询问用户是否重新执行
4. 执行前将状态更新为 `in_progress`
5. 子代理返回后，若成功更新为 `complete`，若失败更新为 `failed`

### Phase 间进度反馈

每个 Phase 完成后，向用户输出一行进度：

```
✅ Phase {N} 完成 — {Phase名称} — {关键产出摘要}
```

示例：
```
✅ Phase 1a 完成 — 环境侦察 — 3节点/45Pod/12SA 已收集
✅ Phase 2a 完成 — K8s合规 — 134条规则检测，12项fail
✅ Phase 4a 完成 — 模式匹配 — 5个模式触发，2个C1确认
```

### 可选：gencpt-supervisor 增强调度

若运行环境支持自定义 agent 类型（如 `gencpt-supervisor`），可用以下方式替代本步的顺序调度，获得更智能的编排（如并行调度 Phase 2a/2b/2c）：

```
Task(gencpt-supervisor, params={...})
```

但 **不依赖此 agent 类型**——上述子代理顺序调度是默认且兼容所有环境的方式。

---

## 第五步：展示摘要

所有 Phase 完成后，读取最终报告，输出：

### 关键数字

- 检测项数
- 发现数（按严重等级分布）
- 验证等级分布（L0 / L1 / L2）
- 覆盖矩阵完成率

### 文件路径列表

- 合规报告：`reports/compliance/<report>.md`
- 攻击报告：`reports/attack/<report>.md`
- 全景报告：`reports/summary/panorama.md`
- POC 包：`evidence/poc/`

---

## 禁止事项

本 SKILL **严格禁止**以下行为：

- **不执行检测命令**：只收集参数、调度子技能和展示结果，不在远程服务器执行检测命令
- **不读取原始检测数据**：原始数据由各 Phase 的子技能 SKILL 负责读取和处理
- **不跳过 Phase 间数据传递**：Phase 间数据通过知识图谱文件传递，不可直接在 Phase 间传内存数据
- **不跳过断点续传检查**：每个 Phase 调用前必须读取 progress.json 检查状态