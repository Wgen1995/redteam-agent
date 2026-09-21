# 12 安装矩阵与目录布局契约（接口⑮）

> 来源：定稿 §10.1-§10.3（辅引 §0.1 ADR-P2/§0.3 口径 5/§3.4/§11 批次 6/§12 R8-R9，随行标注）· schema_version=2 · 状态：待终审冻结

本文件为批次 0 接口⑮（安装矩阵布局＋交战区路径约定，§11 批次 0 行）的誊录件。只誊不创：全部语义来自定稿。

## 1 安装骨架（§10.1，全部宿主共用）

- **单权威目录**：`$TANYIN_INSTALL`，默认 `~/.local/share/tanyin`。
- 幂等安装器 tanyin-install 流程（6 步）：

| 步 | 动作（§10.1 原文语义） |
|---|---|
| ① | 校验 tools.lock（每工具 sha256＋ECDSA 验签） |
| ② | 建权威目录 |
| ③ | 向各宿主 skill/规则目录**符号链接** |
| ④ | 按宿主挂载 hook 模板（如有） |
| ⑤ | 初始化 `$TANYIN_HOME`（交战区＋知识库，与安装区分离） |
| ⑥ | 跑 tanyin-selfcheck |

- 升级＝替换权威目录（knowledge/ 与 engagements/ 不动）；schema_version 不匹配拒绝恢复并提示迁移命令；运行时**绝不自动安装缺失工具**。

## 2 安装区与交战区分离（§3.4/§0.3 口径 5）

- 交战区在安装树外：`$TANYIN_HOME/engagements/<goal-id>/`（每次测试一个）；`$TANYIN_HOME` 默认 `~/.tanyin`（§3.4）。
- 目录树（§3.4 原文誊录）：

```
安装区（git 管理，只读使用）              交战区（$TANYIN_HOME，默认 ~/.tanyin）
tanyin/                                  ├── engagements/<goal-id>/          # 每次测试一个
├── SKILL.md          # 总控路由器        │   ├── *.tsv                      # 13 表
├── phases/           # P0-P6 指令        │   ├── findings-cards/FD-*.md     # finding 外置卡片
├── engines/          # CONTRACT.md       │   ├── evidence/EV-*.md + EV-*.raw# 证据卡片+工件
│   │  web-blackbox/ vuln-agent/          │   ├── vault/                     # 加密凭据库
│   │  session-viz/  nuclei/(批次4)       │   ├── submissions/<intent-id>/
├── cli/              # 薄 CLI 工具箱      │   │   └── submission.json + artifacts/ + operations.log
├── shared/           # 六件契约数据        │   ├── report/                   # draft/signed
├── install/          # 安装器+hook模板     │   ├── matrix.freeze.tsv / state.md / resume-kit.md
├── tools.lock        # 供应链锁定          │   └── cleanup.md / .gitignore
└── docs/                                  └── knowledge/                    # 知识库（升级不冲掉）
```

- 规则（§3.4）：交战区与知识库**永不在 skill 安装树内**（git pull/升级不冲突、状态不混居程序文件）；knowledge/ 与 SKILL 代码分离布局带 format_version，版本不匹配拒绝恢复并提示迁移命令；artifacts 运行时以 `submissions/<intent-id>/artifacts/` 为准。

## 3 五宿主矩阵（§10.2）

| 宿主 | 安装路径/装载机制 | hook 挂载点差异 | egress 档位 | 兼容性测试清单 | 验证现状 |
|---|---|---|---|---|---|
| **DSH** | skill 会话技能装载＋AGENTS.md 系统级注入常驻集 | 宿主命令策略层＋bash 沙箱档位承载 Tier 2（以实测为准；无原生 hook API 时降 Tier 1＋沙箱白名单并披露） | **默认 Tier 3，可显式降档**（--no-egress；降档落 timeline＋报告披露；ADR-P4④） | 夹具全量/evals 全量/canary×4 档/受管重启自动档/报告流水线——**五宿主最全链路** | **本仓可实测** |
| **opencode** | 符号链接入其 skill/agent 目录＋AGENTS.md | 插件与工具权限配置承载 Tier 2（命令执行前拦截 fail-closed） | 默认 Tier 3；代理组件不可用时自检降档披露 | 夹具/evals/canary/headless（opencode run） | 有公开环境，CI 可测 |
| **codex** | 符号链接＋AGENTS.md＋config 注入 | sandbox 模式＋审批策略承载 Tier 2（workspace-write 边界与 guard 协同） | 默认 Tier 3（sandbox 网络面与代理叠加；不可叠加时披露） | 夹具/evals/canary/headless（codex exec） | 有公开环境，CI 可测 |
| **walcode** | 其技能目录符号链接（headless：walcode run/serve 实测可用） | 按其 hook/权限机制探测挂载；无则 Tier 1＋披露 | 默认 Tier 3（组件可运行时）；否则降档披露 | 夹具/干跑/headless 自动档/受管重启演练 | **验证盲区**（无环境，§10.3） |
| **CodeBuddy** | 其技能/规则目录符号链接 | 按其机制探测；无则 Tier 1＋披露 | 同上 | 夹具/干跑/常驻集注入验证（系统级 vs 会话级） | **验证盲区**（无环境，§10.3） |

常驻集注入要求（§10.2）：全部宿主**系统级**（AGENTS.md/skill 系统注入）而非会话消息级（否则宿主自动压缩稀释纪律）——各宿主装载机制差异由安装器模板吸收，skill 主体不改。

## 4 评审裁决与验证现状（ADR-P2/§10.3/§12 R8）

- **首批实测三宿主：DSH / opencode / codex**（有环境可 CI；ADR-P2）。
- **walcode/CodeBuddy＝装得上＋披露未实测**：安装矩阵保留五宿主全量（安装器/符号链接/降档披露照常交付），但 CI 实测与验收签发只覆盖 DSH/opencode/codex；该两宿主验证状态在报告中如实标注「未实测」（§10.3 首批定位）。
- 补测升格路径（§10.3）：

| 机制 | 内容（§10.3 原文语义） |
|---|---|
| 静态验证（CI 可跑，宿主无关，六项） | ①命令索引一致性——phases/*.md 与 engines/ 中引用的命令 ⊆ shared/LEDGER.md 附录 A 37 条签名；②编码规范 lint（TSV 样本 UTF-8 无 BOM＋LF＋转义）；③phases.yaml schema 校验＋九门断言命令存在性；④目录布局断言（安装区/交战区分离、符号链接目标存在）；⑤tools.lock 验签；⑥黄金夹具全量（CLI 层）。合并为 `tanyin-selfcheck --static`，CI 对五宿主同跑 |
| 用户手测脚本 | `tanyin-selfcheck --host <name> --guided`：安装命令→能力探测（子代理并发/shell/headless/系统级注入/hook 挂载点逐项自动探测＋人工确认）→冒烟清单（`用探隐自检` 干跑 P0-P2：零对外请求，产出 goals/scope/matrix 样本＋timeline）→**回传模板**（探测结果 JSON＋干跑产物哈希＋异常截图），用户贴回 issue 即计入该宿主验证记录 |
| 发布口径 | walcode/CodeBuddy 标注「静态验证通过＋待实测」；首个实测回传前其执法档位声明默认 **Tier 1（保守披露）**；实测回传后按探测结果更新档位与能力矩阵 |

- 批次 6 出口验收（§11）：五宿主矩阵验证（DSH/opencode/codex 实测；walcode/CodeBuddy 静态＋手测脚本 §10.3）。

## 探知项（待仲裁）

1. walcode/CodeBuddy 默认档位两说冲突：§10.2 五宿主矩阵 walcode 行 egress 档位「**默认 Tier 3**（组件可运行时）；否则降档披露」（CodeBuddy 行「同上」）vs §10.3 发布口径「首个实测回传前其执法档位声明默认 **Tier 1（保守披露）**」（§12 R8 同：「该两宿主默认保守披露 Tier 1」）。安装期 egress 默认值与发布期执法档位声明默认值两处口径不一致，待仲裁。

## 自验

命令实跑证据（D＝定稿路径，本文件＝contracts/12-install-layout.md）：

- 五宿主行数：`sed -n '681,685p' $D | grep -c '^| \*\*'` → **5**（DSH/opencode/codex/walcode/CodeBuddy）＝本文件 §3 表 5 数据行。
- 首批实测宿主＝**3**（DSH/opencode/codex，ADR-P2/§10.3）；报告标注「未实测」宿主＝**2**（walcode/CodeBuddy）。
- 安装器步骤：本文件 §1 表 `awk '/^\| ①/,/^\| ⑥/' 本文件 | grep -c '^| '` → **6**（§10.1 六步链：校验 tools.lock→建目录→符号链接→hook 模板→初始化 $TANYIN_HOME→selfcheck）。
- 静态验证六项＝**6**（①命令索引一致性…⑥黄金夹具全量，§10.3）。
- 目录树：本文件 §2 代码块 12 行与定稿 L156-167 `diff` → exit **0**（逐字节一致）。
- 探知项＝**1**。
