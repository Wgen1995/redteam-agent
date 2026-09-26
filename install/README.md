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
| 4 | hooks | hook_mechanism 宿主装 install/hooks 模板（T8 落地）；无机制宿主=Tier 1+披露 | — |
| 5 | init-home | 交战区初始化：engagements/knowledge/report 与安装区分离；knowledge 种树拷入（R-T12-4：k1-baseline.tsv 随装） | — |
| 6 | selfcheck | 接 `tanyin-selfcheck --static` 门（T6 落地前为中间态披露行） | 门不过=随其退出码 |

安装日志 `<home>/install-log.tsv`：`<ts>\t<step>\t<detail>`（时间戳显式传入，禁墙钟）。

## 五宿主矩阵（§10.3）

| host | verification | 默认执法档 | hook | compat |
|---|---|---|---|---|
| dsh | 本仓可实测 | Tier 3 | 有 | 夹具全量/evals 全量/canary×4 档/受管重启/报告流水线 |
| opencode | 公开环境 CI 可测 | Tier 3 | 有 | 夹具/evals/canary/headless |
| codex | 公开环境 CI 可测 | Tier 3 | 有 | 夹具/evals/canary/headless |
| walcode | 静态验证+待实测（§10.3） | Tier 1 | 无 | 静态验证通过；待实测保守披露 |
| codebuddy | 静态验证+待实测（§10.3） | Tier 1 | 无 | 静态验证通过；待实测保守披露 |

- 发布口径：walcode/CodeBuddy 在实测完成前只标注「静态验证+待实测」，执法档位默认 Tier 1（保守披露）；宿主路径字段按各宿主公开文档在 T8 落地时核对一次，偏差=改 JSON 不改代码。
- 手测引导：`tanyin-selfcheck --host <name> --guided`（T6）。

## 交战区分离（设计 §3.4）

- 安装区（install_root，缺省 `~/.local/share/tanyin`）与交战区（home，缺省 `~/.tanyin`）两树分居；home 永不落安装树内——`tanyin-selfcheck --static` layout 项机检（T6）+ `tests/test_install_core.py` 断言双备案。
- 交战区内只有 engagements/knowledge/report 运行时面；安装区内是只读权威副本（skill 链接指回 install_root）。

## 信任锚

- 缺省 `engines/nuclei/release.pub`（当前=TEST-ONLY 夹具钥，批次 4 原样）；`--pubkey` 覆盖。
- 生产钥生成/保管/重签流程=G-22，随批次 6 T9 落 `KEY-MANAGEMENT.md`+`resign-tools-lock.py`（本目录）；CI/测试永用 TEST-ONLY 夹具钥，与生产钥无信任关系。

## hooks 模板

`install/hooks/` 随批次 6 T8（五宿主矩阵落地）交付；无 hook 机制宿主安装时落 Tier 1+披露行。
