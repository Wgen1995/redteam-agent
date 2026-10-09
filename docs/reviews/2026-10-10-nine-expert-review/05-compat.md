# 05 兼容性专家（多宿主与跨平台）深度分析（2026-10-10 九维专家会诊）

## 现状强项
1. 五宿主安装矩阵数据驱动+如实分档（install/README.md 五宿主表 Tier1-3 档 G-38 回传台账；hosts/*.json 全字段化；渲染单源 hosts_matrix.py 标记幂等注入）。
2. 账本核心 Windows 兼容真做了：filelock msvcrt/flock；lock_v2 三平台 boot_id；ensure_utf8_stdio（GBK 炸中文注释直言）；13 CLI 全 .cmd 配对；battle.py 零 POSIX 依赖；CI 双 OS×双 Python 矩阵。
3. DSH 插件 v0.3.0 真 API 三面+镜像纪律（defineTool/registerProvider 协议镜像官方 provider；单测5+真 cordis 集成测；sync-skill.sh 实测 IDENTICAL）。
4. 核/面分离决策明确（纯技能核全宿主通吃、插件薄面厚核不复制状态）。
5. 执法语义单源跨宿主（enforce.py 供 guard/hooks 三宿主模板同源 fail-closed）。

## 关键缺口
1. 【最高】插件运行时依赖错位+RC 级 API+零 LLM 终验：dsh-tools 在 devDependencies（运行时 import 却不在 dependencies）——npm pack 干净安装即 module not found；0.0.1-rc.1+^宽松范围无稳定性承诺；in-LLM 终验从未跑过（v0.2 曾有死码前科）。
2. 【高】技能保真靠 cwd 约定非机制，三套 allowlist 互相漂移：SKILL=仓根相对路径（cwd 不在仓根 44 命令全断）；typed tools 13/44、service 又 10 条、append-timeline 两面不一致；codex 端到端未实战、Claude Code 未落、AGENTS-INJECT 不含 SKILL 路径。
3. 【高】单机绝对路径残留分发面：opencode.json 硬编码 /Users/wgen/.tanyin/**（换机即权限墙=RT 记载击杀形态）；插件 defaultRepo() 硬编码 ~/redteam-agent。
4. 【中高】模型兼容零度量：四战全 opencode+GLM-5.3；战书 33 律是对 GLM-5.3 的隐式拟合；"DSH 0.5893 vs opencode 0.70"是宿主+模型双变量混淆未拆分；RT 归因链模型项缺位。
5. 【中】Windows 覆盖不均：runner/gateloop 无 .cmd；kill_group os.killpg 在 Windows 必崩（AttributeError 不在捕获集）；symlink 无 junction 回退（非开发者模式拒装）；插件 spawn 硬编码 python3。
6. 【中】Python 下限口径分裂：README 3.10+/CI 3.11-3.12/本机 3.9.6 实跑；无 python_requires 断言。

## 可执行建议
| 建议 | 收益 | 量 |
|---|---|---|
| dsh-tools 移 dependencies 钉精确版+删无用 schemastery+npm pack 冒烟 | 消除发布即崩 | S |
| 44 命令 allowlist 单源 JSON+补齐写命令或声明 cwd 前提 | 三面漂移归零 | S-M |
| 绝对路径改安装器渲染（TANYIN_HOME）+config.repo 文档化 | 他人可装可复现 | S |
| 2×2 模型 A/B（GLM vs 备选 × 战书）各 3 战+RT 加 model 字段 | 量化模型敏感度 | M |
| runner/gateloop 补 .cmd+kill_group nt 分支+junction 降级 | Windows 能真跑一战 | M |
| CI 加 3.10 格或改口 3.11++selfcheck 版本断言 | 口径合一 | S |

## 对标
PentestGPT 双后端已发布（探隐宿主实测覆盖落后）；superpowers 镜像纪律同源但缺 CI diff=0 钉测；AGENTS.md 生态惯例较工程化但缺 Claude 模板；Caldera 级 plugin 规范（peerDeps+semver）未达最低及格线。

## 总评
账本核心跨平台工程单人罕见高水准，但分发面（插件依赖错位+RC 宿主 API+零 LLM 终验、cwd/单机绝对路径隐性依赖、零度量模型兼容）使"全宿主通吃"实为"opencode+GLM-5.3+这台 Mac 上通吃"——文档的 🟡🔮 诚实披露恰恰标出了真实分发边界。
