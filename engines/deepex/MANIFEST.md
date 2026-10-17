# deepex 派生层 MANIFEST（契约 08 十二字段）

kind: cli

| 字段 | 值 |
|---|---|
| name | deepex |
| kind | cli（纯本地派生变换：findings 流入→意图卡/取证包流出，无 OS 工具依赖、无网络） |
| version | 0.1.0（W3-P1-1②③） |
| 适用场景 | 利用深挖派生：读取类发现（备份/配置/密钥文件）→凭据检查意图卡；命令执行类发现→RCE 取证包 |
| 参数 | derive.py --findings-file=F --out-dir=D [--submission-file=S] |
| 产物路径 | submissions/<intent-id>/artifacts/{derived-cred-intents.json, forensic-packages.json} + operations.log |
| 超时 | 即时（纯变换，<1s） |
| 重试策略 | 不适用（本地确定性变换：同输入同产物，金样可重放） |
| 幂等键 | 输入 findings 流内容（同流重导出=byte 级同产物） |
| 纪律能力声明 | max_op_level: 读／视角上限: L2（派生层不执行；取证三连执行面在消费引擎经 guard） |
| 工具依赖 | 无外部工具（deny 机械复用 cli/ledger/enforce 单源） |
| 验签公钥 | 不适用 |

## ② 文件读取→凭据闭环第一段（P1-1「读到配置/密钥→add-cred→cred-obtained→身份差分」）

读取类发现 → 凭据检查**意图卡**（kind=deep-dive, origin=precedent, engine=deepex-cred,
budget=0;0;0 纯本地）→ 总控验收落 intents（引擎不写账本，单写者）。闭环后段
（add-cred kind=session / cred-obtained 事件 / 身份差分 authz-diff 触发）在总控侧，
本层只产意图卡。

纪律三件（结构化非措辞）：
- **不外发**：constraints.egress=forbidden；检查计划=本地三查（格式/规则/重复使用）；
  网络验证面须经授权另立意图走 guard 通道。
- **密值不带出**：源发现含 password=/token=/sk-live 字面也不复制——赋值形截断+
  字面形整段替换为 [已脱敏:本地校验]；密值落 vault 是总控 add-cred 的事。
- **签名面**：备份（backup/.bak/dump.sql/.sql/.sqlite）｜配置（.env/wp-config/
  database.yml/application.properties/.git/config/.aws/credentials/.kube/config）｜
  密钥（id_rsa/.pem/.key/secrets*/credentials*）。边界用 ASCII 类前瞻非 \b
  （中文全角括号属 Unicode \w，「.env（」在 \b 下不成边界会漏配）。

## ③ RCE 取证模板（P1-1「RCE 取证执行模板」）

命令执行类发现（RCE/命令执行/OS command injection/远程代码执行…）→ 取证包：

- **非破坏三连**：whoami / id / hostname——固定序、无参数、零写入、禁增删
  （extra 任何追加=ValueError，含「看起来无害」的追加——口子一开即是删改通道）。
- **黑名单兼容**：三连逐条过 guard deny 机械（deny_forms 原形/归一形/sh 包装形 +
  deny_hit，cli/ledger/enforce 单源）——不兼容即 RuntimeError 拒出包。
- **证据卡落账锚**：一命令一卡（capture=stdout, redaction=vault-tokenize,
  expected_matcher=输出形状锚：whoami 非空 / id 含 uid= / hostname 主机名形）；
  执行通道=tanyin-guard exec（request-ticket 落账）。
- **载荷剥离**：发现标题含破坏载荷（deny-list 命中形）整段置换 [载荷已剥离]，
  包体不回带原文。
