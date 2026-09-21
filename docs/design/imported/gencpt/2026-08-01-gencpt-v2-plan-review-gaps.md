# GenCPT V2 计划文档写漏清单（评审记录）

> 日期：2026-08-01
> 评审对象：`/root/GenCPT V2/` 下 10 份设计/计划文档
> 结论：整体写作质量高（实现契约到函数体级别、三向 Finding 绑定、每任务 5 步 TDD），但存在 **4 处实质写漏 + 3 处边界项**。
> 本文档仅记录评审发现，不表示任何代码已实现或门禁已通过。

---

## 一、实质写漏（按严重度排序）

### 1.【最重要】Wave 2/3/4 各自的"安装+回滚 smoke"没有落实为任务

**承诺方：**
- `2026-07-30-gencpt-v2-roadmap.md:143-153`（逐波安装与回滚表）：每波退出前必须生成可安装制品、升级说明和 `rollback-manifest.json`，在新隔离目录完成安装与回滚，并纳入 `wave-N-gate.json`。
- `2026-07-30-gencpt-v2-implementation.md:61-75`（§1.1 逐波安装与回滚门禁）：同样承诺，并写明"不能等到 Wave 5 才验证前序版本可交付"。

**实际落地情况：**
- Wave 1：完整实现 ✓（`scripts/install_alpha1.py`、`scripts/package_alpha1.py`、`tests/unit/test_alpha1_package` 的精确回滚断言，见 wave1:2254-2295、2414-2444）。
- Wave 2/3/4：19/17/13 个任务中**没有任何一个**是本波打包、隔离安装、回滚 smoke 任务；各波完成门禁（如 wave2:1933-1959）也没有对应断言。搜"rollback-manifest"全库仅命中 wave1。
- Wave 5：只有 `docs/install.md`、`docs/upgrade.md` 文档（wave5:2025-2109），没有"隔离目录安装 + 回滚验证"的 smoke 任务；W5-T11 生成 release bundle，但无安装/回滚测试。

**后果：** 若照计划执行，alpha2/beta1/beta2 的"可交付/可回滚"声明只有总索引背书、无实现证据，违反计划自己定的"每波必须验证前序版本可交付"。

**建议补法：** 在 Wave 2/3/4 各新增一个任务（如 W2-T20 / W3-T18 / W4-T14）：本波制品打包、隔离目录安装 smoke、按 rollback manifest 恢复并断言文件集合与 SHA-256，结果写入 `wave-N-gate.json`。参照 W1-T12 的 `test_reproducible_install_and_exact_rollback` 模板。

---

### 2. 威胁模型/安全边界文档缺失

**出处：** 设计规格 §4.4 明确要求"该边界必须在报告和安全文档中明确"（不声称防御 Broker 管理员、签名根密钥持有者或 OS root）。

**实际落地情况：** 五个波次没有任何任务产出这份安全/威胁模型文档。wave2:86 只要求"测试名、模块依赖和发布说明必须维持此分层"，没有文档产物。交付文档清单（设计规格 §20）也未列出该项。

**建议补法：** 在 Wave 2（发布安全运行时边界时）或 Wave 5（发布文档时）增加"威胁模型与安全边界文档"任务，输出受信边界声明并纳入发布 bundle。

---

### 3. Session 归档/retention 只有命令名、没有语义

**出处：** 设计规格 §20 交付文档承诺"Session 恢复、归档和 retention"。

**实际落地情况：** W2-T17 在 CLI 里列出了 `session ... archive` 子命令（wave2:1754），但没有任何任务定义 archive 的行为、retention 规则（保留期/清理策略）、归档 bundle 的恢复流程及测试。搜索 retention/归档，仅命中 self_cleaning 的归档禁令与 raw retention 字段，无 session 级策略。

**建议补法：** 在 Wave 2 W2-T17 中补齐 `session archive` 语义：归档内容集合、只读 bundle 生成、恢复流程、retention 策略测试。

---

### 4. 凭据后端机制模糊（标准库与 keychain 的矛盾）

**出处：** 设计规格 §8.2 要求凭据保存在"系统 keychain、secret service 或权限隔离文件"。

**实际落地情况：**
- W2-T10（wave2:1047）：nonce checkpoint 需写入"系统 keychain 或外部 attestor 的 write_anchor"。
- W2-T11（wave2:1118）：`CredentialProvider` 仅从"系统 keychain、secret service 或 broker-owned 0600 文件"读取。
- 但技术栈约束为 **Python 3.11 纯标准库**（wave2:11），标准库无法访问 macOS Keychain / Windows DPAPI / Linux secret service。

**后果：** 计划未指明用哪个外部工具（`security`? `secret-tool`?）、什么 fallback、以及这是否违反"标准库-only"约束。执行者到此必然卡壳或自创实现，与本计划"精确到实现契约"的风格不符。

**建议补法：** 明确 keychain 访问机制（外部 CLI 白名单 + 失败降级到 broker-owned 0600 文件），或显式把 keychain 列为可选后端并说明标准库 fallback，更新技术栈声明。

---

## 二、边界项（轻微）

### 5. Windows 宿主端到端无验收任务
W2-T11 覆盖 Windows SID/DACL 单元层（wave2:1116,1120），W2-T4 有三平台默认路径（wave2:442-446），但 CI、Chromium、安装/回滚全部 Linux-only。Windows 的 Strict 集成验证无归属。
**建议：** 在 W5-T13 宿主兼容任务中补 Windows 集成验收（或显式声明 Windows 为 future work）。

### 6. 非目标无显式 gate
设计规格 §2.2 的 7 个非目标（GraphRAG、Code-native Runner、远程 registry 服务、Web 控制面、图数据库、模型自动应用修复、自动晋升生产知识）只有范围声明，无"禁止实现"测试或 gate 防回潮。wave4:15 是唯一例外（明确非目标段落）。
**建议：** 每波完成门禁增加一条"非目标扫描"断言（如 rg 禁止引入对应模块/依赖）。

### 7. 运行模式矩阵（设计规格 §24）逐条传播规则未逐条对应测试
只有 Fast/Custom 依赖闭包测试（T-FAST-DEPENDENCY-CLOSURE、T-CUSTOM-CAPABILITY-CLOSURE），矩阵中的具体传播行为（如"8c Fast 生成 compliance-only summary"、"平台不适用为 skipped 而非 completed"）未逐条映射测试 ID。
**建议：** 在 Wave 2 W2-T3 或 Wave 5 补一张"运行模式矩阵 × 测试 ID"对照表，逐条核对。

---

## 三、附注

- 文档与仓库状态不一致已另行确认：当前 `/root/gencpt` main 分支（`2a0acf8`）无 `registry/`、`tests/`、`schemas/`、`releases/`、`tools/gencpt_runtime/`，V2 零实现；wave1 附录声称的 `feature/gencpt-v2-wave1` 分支（约 40 提交）在当前仓库不存在；`skills/graph-viz/` 目录也不存在。
- 上述补丁建议在动工前落入对应 Wave 计划，否则 Wave 2/3/4 完成门禁会因缺少回滚证据而不诚实。
