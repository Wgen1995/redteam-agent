# install/ · 安装矩阵总览（批次 6 T5）

六步安装器 `cli/tanyin-install`（+Windows `.cmd` 配对）：单源 `cli/ledger/install_core.py`。

## 判定命令（出口 #6）

```
py -3 cli/tanyin-install --home <tmp> --timestamp <TS>   # 连跑两次，第二轮零变更（幂等，§10.1）
py -3 cli/tanyin-selfcheck --static                       # 六项静态验证全 PASS（T6 落地）
```

## 六步

| 步 | 名 | 语义 | 失败形态 |
|---|---|---|---|
| 1 | verify-lock | tools.lock 逐键 ECDSA 验签（批次 4 单源 supply_chain，openssl 子进程 fail-closed） | 签名不过=1；openssl/公钥缺=2 |
| 2 | authoritative-dir | 白名单拷贝仓内容→install_root（`_AUTH`；.git/tests/docs/panorama 不进安装树） | 权威项缺=1 |
| 3 | host-link | 按宿主模板 `hosts/<host>.json` 的 skill_link_dirs 建 symlink（重链幂等） | 目标被占=1；symlink 权限=2 |
| 4 | hooks | hook_mechanism 宿主真挂载 `install/hooks/<host>.md`→`<install_root>/hooks/`（幂等覆盖；I-1 交付：生命周期事件→tanyin CLI 调用示例+占位说明）；无机制宿主=Tier 1+披露 | 模板缺=1（fail-closed 拒装） |
| 5 | init-home | 交战区初始化：engagements/knowledge/report 与安装区分离；knowledge 种树拷入（R-T12-4：k1-baseline.tsv 随装） | — |
| 6 | selfcheck | 接 `tanyin-selfcheck --static` 门（T6 落地前为中间态披露行） | 门不过=随其退出码 |

安装日志 `<home>/install-log.tsv`：`<ts>\t<step>\t<detail>`（时间戳显式传入，禁墙钟）。

## 五宿主矩阵（§10.3）

| host | verification | 默认执法档 | hook | AGENTS 注入落点 | compat |
|---|---|---|---|---|---|
| dsh | 本仓可实测 | Tier 3 | 有 | ~/.tanyin-hosts/dsh/AGENTS.md | 夹具全量/evals 全量/canary×4 档/受管重启/报告流水线 |
| opencode | 公开环境 CI 可测 | Tier 3 | 有 | ~/.tanyin-hosts/opencode/AGENTS.md | 夹具/evals/canary/headless |
| codex | 公开环境 CI 可测 | Tier 3 | 有 | ~/.tanyin-hosts/codex/AGENTS.md | 夹具/evals/canary/headless |
| walcode | 静态验证+待实测（§10.3） | Tier 1 | 无 | ~/.tanyin-hosts/walcode/AGENTS.md | 静态验证通过；待实测保守披露 |
| codebuddy | 静态验证+待实测（§10.3） | Tier 1 | 无 | ~/.tanyin-hosts/codebuddy/AGENTS.md | 静态验证通过；待实测保守披露 |

- 发布口径：walcode/CodeBuddy 在实测完成前只标注「静态验证+待实测」，执法档位默认 Tier 1（保守披露）；宿主路径字段按各宿主公开文档在 T8 落地时核对一次，偏差=改 JSON 不改代码。
- 手测引导：`tanyin-selfcheck --host <name> --guided`（T6）。
- AGENTS 系统级注入（T8）：模板 `install/AGENTS-INJECT.md`（常驻八条，<2K token 量级护栏）＋渲染/幂等注入单源 `cli/ledger/hosts_matrix.py`（`<!--TANYIN:BEGIN/END-->` 标记包裹，二次注入零变更）；块内含本宿主档位披露行（铁律 5——盲区宿主块内直书「待实测保守披露」）。

### 实测路径（宿主验证通道；T8 落地）

- **dsh（本仓可实测）**：本仓全套即实测面——`python3 -m unittest discover -s tests`（635+ 例）+`python3 tests/run_golden.py`（金样 54 面）+`python3 cli/tanyin-evals run --suite=static --goal-dir . --timestamp <TS>`（evals 硬门）+`python3 cli/tanyin-install --home <tmp> --timestamp <TS>` 连跑两次幂等+`python3 cli/tanyin-selfcheck --static`。
- **opencode / codex（公开环境 CI 可测）**：headless 实测命令行——安装落位后经宿主 headless 入口下发干跑任务（opencode=`opencode run "用探隐自检"`／codex=`codex exec "用探隐自检"`），验收口径=交战区产 goals/scope/matrix 样本+timeline（零对外请求）；回传贴 `tanyin-selfcheck --host <name> --guided` 第 4 步 probe_results 模板。
- **walcode / codebuddy（静态验证+待实测 §10.3）**：静态验证=`tanyin-selfcheck --static` 全 PASS；手测脚本=`tanyin-selfcheck --host walcode --guided`／`--host codebuddy --guided` 一页引导（安装命令→能力探测→冒烟清单→回传模板）。
- **G-38 台账（如实登记）**：walcode/CodeBuddy 宿主实测回传后升档——回传形态=guided 第 4 步 probe_results 模板贴回验签入册；未回传前保持「静态验证+待实测」标注与 Tier 1 保守披露，不谎称已实测。

## 交战区分离（设计 §3.4）

- 安装区（install_root，缺省 `~/.local/share/tanyin`）与交战区（home，缺省 `~/.tanyin`）两树分居；home 永不落安装树内——`tanyin-selfcheck --static` layout 项机检（T6）+ `tests/test_install_core.py` 断言双备案。
- 交战区内只有 engagements/knowledge/report 运行时面；安装区内是只读权威副本（skill 链接指回 install_root）。

## 信任锚

- 缺省 `engines/nuclei/release.pub`（当前=TEST-ONLY 夹具钥，批次 4 原样）；`--pubkey` 覆盖。
- 生产锚替换=显式 `tanyin-install --release --pubkey <生产 release.pub>` 通道（批次 6 评审收尾 I-2 接线；裁决 C）：新钥路径传入 verify 面替换缺省锚——整锁须已在新钥下重签（不过=exit 1，§5 原子变更）→交互确认（REPLACE 令牌；缺确认=exit 2）→锚文件原子替换，release-anchor 行落 install-log。详见 `KEY-MANAGEMENT.md` §4。
- 生产钥生成/保管/重签流程=G-22，随批次 6 T9 落 `KEY-MANAGEMENT.md`+`resign-tools-lock.py`（本目录）；CI/测试永用 TEST-ONLY 夹具钥，与生产钥无信任关系。

## hooks 模板

AGENTS 系统级注入=五宿主统一常驻通道（批次 6 T8 交付，见上节）；`install/hooks/` 逐宿主 hook 模板（dsh/opencode/codex，批次 6 评审收尾 I-1 落库）：安装器 step4 真挂载——hook_mechanism 宿主将 `install/hooks/<host>.md` 幂等覆盖至 `<install_root>/hooks/<host>.md`（模板缺=fail-closed 拒装，占位披露中间态废除）；模板形态=最小可用（生命周期事件→tanyin CLI 调用示例+占位说明+G-38 实测回传时点注记）；判定语义与 cli/ledger/enforce.py 单源同源，真宿主原生 hook API 接线属实测回传通道。无 hook 机制宿主（walcode/CodeBuddy）安装时落 Tier 1+披露行、零文件落装。

## 守门声明（Tier 3 egress 代理；批次 6 T10）

- 起服：`python3 cli/tanyin-egress serve --acl <goal-dir>/egress.acl --port <N> --egress-log <goal-dir>/egress-log.jsonl`（前台常驻，Ctrl-C 优雅退出；无守护进程纪律合规）。
- **TLS 限制披露（裁决 H）**：代理不做 TLS 中间人、不解析 TLS 内容——CONNECT 隧道按 CONNECT 目标主机名:端口 ACL 判定后双向字节中继；隧道内行为不可见是架构边界而非能力缺口。
- **DNS pin 三态**：`pin <host>`（无 ip）=声明态；目标 IP 字面量≠`dns-pin` 期望=拒绝（pin_ok=False）；域名+pin 带 ip=直连 pin（解析面免疫，不可比对=pin_ok=None 如实披露）。
- **运行时工件**：`egress-log.jsonl` 行={"ts","verdict","host","port","kind","pin_ok"}（kind=forward|connect|oob|canary）——代理绝不写 13 表（单写者纪律）；canary 域触碰=kind=canary 行（T11 流量级零容忍证据源）。
- **G-41 性能披露（如实）**：并发/吞吐/时延上限未测——机械执法组件，性能非首批目标；上限数字待实测通道，不预写指标。
