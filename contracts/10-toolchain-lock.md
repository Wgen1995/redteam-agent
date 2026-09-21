# 接口⑫ · tools.lock 契约（供应链锁定+ECDSA 验签）

> 来源：定稿 §10.1（辅 §1 D1.1/§3.4/§6.1/§6.2/§10.3） · schema_version=2 · 状态：待终审冻结

## 1 定位

- tools.lock 是安装区供应链锁定文件，位于安装树 `tanyin/tools.lock`（§3.4）。
- 锁定口径：每工具 sha256+ECDSA 验签（§10.1）；tools.lock 锁版本（§6.2）；CLI 工具箱「tools.lock 锁定（哈希+ECDSA 验签）」（§1 D1.1/§2.4）。
- 引用方：引擎 manifest 字段「工具依赖(tools.lock 键)」（§6.1）——工具依赖以 tools.lock 键引用。

## 2 每工具字段

| 字段 | 类型 | 枚举/约束 | 说明 |
|---|---|---|---|
| 工具键 | string | =manifest「工具依赖(tools.lock 键)」 | 条目主键 |
| 版本 | string | 钉死 | 版本锁定（§6.2「tools.lock 锁版本」） |
| sha256 | string(hex) | 每工具一值 | 供应链完整性校验（§10.1「每工具 sha256」） |
| ECDSA 签名 | string | 每工具一值 | 发布方验签（§10.1「ECDSA 验签」） |
| 模板 commit | string | 仅模板类工具（如适用） | nuclei-templates 钉 commit+ECDSA 验签（§6.2） |

## 3 验签与安装流程（tanyin-install 幂等安装器，6 步）

| 步 | 动作 |
|---|---|
| 1 | 校验 tools.lock（每工具 sha256+ECDSA 验签） |
| 2 | 建权威目录（单权威目录 `$TANYIN_INSTALL`，默认 `~/.local/share/tanyin`） |
| 3 | 向各宿主 skill/规则目录符号链接 |
| 4 | 按宿主挂载 hook 模板（如有） |
| 5 | 初始化 `$TANYIN_HOME`（交战区+知识库，与安装区分离） |
| 6 | 跑 tanyin-selfcheck |

「复制即装」=幂等安装器（§1 D1）：建立权威目录+符号链接+tools.lock 校验。

## 4 铁律与升级

| 规则 | 内容 |
|---|---|
| 绝不自动安装 | 运行时**绝不自动安装缺失工具**（§10.1；§6.2 同句重申） |
| 升级=替换权威目录 | 升级=替换权威目录（knowledge/ 与 engagements/ 不动） |
| 版本不匹配拒绝恢复 | schema_version 不匹配拒绝恢复并提示迁移命令 |
| 静态验签项 | 静态验证⑤=tools.lock 验签（§10.3，并入 `tanyin-selfcheck --static`，CI 对五宿主同跑） |
| 批次落位 | tools.lock 全量=批次 6 出口验收范围（§11 批次 6） |

## 探知项（待仲裁）

无。

## 自验（以下命令与计数均为实跑结果）

- 『运行时绝不自动安装缺失工具』：定稿 `grep -c '绝不自动安装缺失工具' 定稿` → **2**（§6.2 行 517、§10.1 行 675 两处原句）；本文件 §4 同句在场。
- 定稿 tools.lock 提及次数：`grep -c 'tools\.lock' 定稿` → **14**。
- 验签与安装流程：本文件 `grep -cE '^\| [1-6] \| ' contracts/10-toolchain-lock.md` → **6** 步（验签→建权威目录→符号链接→hook 模板→初始化 $TANYIN_HOME→selfcheck，与 §10.1 原序一致）。
- 每工具字段：`grep -cE '^\| (工具键|版本|sha256|ECDSA 签名|模板 commit) '` → **5**（各字段均标注定稿出处短语）。
- 探知项=0。
