# 批次 0：契约冻结——实施计划

> 目标：把设计定稿（docs/design/2026-09-21-tanyin-v2-design.md，评审通过版 baf0a2f）中的 16 项接口逐项誊成 `contracts/` 冻结文档。出口=用户终审通过；冻结后任何变更走 schema_version+迁移命令。
> 纪律：每份契约**只誊不创**——内容以定稿为唯一来源；发现定稿内部矛盾时停下登记"探知项"，不自行仲裁。

## 文件结构

```
contracts/
  README.md             索引+冻结规则（16 项清单、schema_version=2、变更流程）
  01-ledger-schema.md   ①13 表 schema 全字段 + ②10 边词汇
  02-commands.md        ③37 条账本命令签名（逐条：签名/输入/输出/拒收条件）
  03-credentials.md     ④{{vault:cred-N}} 占位符语法+vault 条目格式 + ⑬creds 契约（kind 二分/material meta 位/authz-diff 语义/硬门）
  04-phases.md          ⑤phases.yaml schema + 九门断言
  05-scope.md           ⑥scope schema（include/exclude/oob/account-grant/amendment_of 链）
  06-evidence-cards.md  ⑦POC 四要素+EV/FD 卡片 front-matter + ⑧findings 字段+六字段映射
  07-submission.md      ⑨统一提交 schema（引擎→总控提交文件协议）
  08-manifest.md        ⑩manifest 模板+纪律能力声明
  09-cli-surface.md     ⑪CLI 工具箱命令面+铁律 7 边界
  10-toolchain-lock.md  ⑫tools.lock 格式+ECDSA 验签流程
  11-enforcement.md     ⑭四层执法档位表+egress compile 输入输出
  12-install-layout.md  ⑮安装矩阵布局+交战区路径约定（三宿主实测+两宿主披露定位）
  13-report-template.md ⑯报告模板章节骨架（中文合规段六要素）
```

## 任务清单（每任务=抽取+对照+提交）

- **T1 README 索引**：16 项↔文件↔定稿章节对照表；冻结规则三条（只誊不创/矛盾登记探知项/变更走 schema_version）。
- **T2 账本 schema（01）**：源=定稿 §4.2-§4.10。逐表：字段名/类型/枚举值/默认值/哈希输入范围（timeline 全行）。验：13 表逐个字段数与定稿一致（grep 计数对照），10 边一条不少。
- **T3 命令签名（02）**：源=§5.3+附录 A。37 条逐条：签名/必填参数/输出 schema/写前拒收条件。验：命令数=37，每条有拒收条件。
- **T4 凭据契约（03）**：源=§8.4（vault 四关卡）+§4.10（creds 表）+§6.6（authz-diff 语义）。含评审裁决：material meta 位（ntlm-hash|ssh-key|x509）、kind 二分。验：四关卡+硬门+差分语义三块齐。
- **T5 阶段门（04）**：源=§5.2。phases.yaml 逐门：title/duty/断言/出口。验：九门 P0-P6 数齐（含 P5.5/P6.0）。
- **T6 范围（05）**：源=§4 scope 表+§8.5+§5.4 范围生长。三层语义（授权边界可修订/图谱 append-only/锚点冻结）+amendment_of 链+out_of_scope 复判。
- **T7 证据卡片（06）**：源=§4.9/§4.11。E-index 字段、EV/FD front-matter、POC 四要素、六字段映射表。
- **T8 提交 schema（07）**：源=§6.1。统一提交文件字段+submission-ok 判定。
- **T9 manifest（08）**：源=§6.3。模板+纪律能力声明字段。
- **T10 CLI 命令面（09）**：源=§2.4。命令清单+铁律 7 边界（LLM 只调用不实现）。
- **T11 工具链锁（10）**：源=§10.1。tools.lock 字段+ECDSA 验签流程+运行时不自动安装。
- **T12 执法档位（11）**：源=§8.5。Tier 0-3 档位表+各层职责+egress compile 输入输出+降档披露规则。
- **T13 安装布局（12）**：源=§10.1-§10.3。单权威目录/符号链接/交战区分离/三宿主实测+两宿主披露定位。
- **T14 报告骨架（13）**：源=§11 契约⑯。六要素章节骨架（授权与范围声明/WSTG 映射/覆盖度与局限/风险分级/整改优先级/等保占位）。
- **T15 交叉终验**：①每份契约与定稿源章节逐项对照（字段数/枚举/数量三对照，grep 证据留档）②16 项全覆盖检查③术语一致性扫描（同物同名）。
- **T16 冻结**：用户终审 → git tag contracts-v2 → 汇报。

## 执行方式

T1 主线程；T2-T14 三组并行（账本组 T2-T4 / 门禁组 T5-T6+T10-T12 / 引擎交付组 T7-T9+T13-T14），每组一个子代理，指令含"只誊不创+矛盾登记"纪律；T15-T16 主线程亲自做。
