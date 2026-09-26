# KEY-MANAGEMENT · 生产钥生成/保管/重签流程（G-22；批次 6 T9）

> 裁决 C 落地面：本文件=流程+脚本+通道交付。**真钥生成仪式本身须人工在离线介质机
> 执行**（如实披露：本仓当前**不持有**任何生产私钥；仓内现役签名=TEST-ONLY 夹具钥，
> 与生产信任锚无信任关系——测试不依赖生产钥在场）。

## 1 生成（离线介质机，人工仪式）

- 算法：EC P-256（与验签单源 `cli/ledger/supply_chain.py` openssl pkeyutl 链路一致）。
- 命令（在**永不联网**的介质机上执行）：

  ```
  openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out release-priv.pem
  openssl pkey -in release-priv.pem -pubout -out release.pub
  ```

- 仪式记录：记录生成日期、执行人（≥1 人）、介质封存编号；私钥**永不进仓**、永不落
  联网机文件系统（仅离线介质+口令封存）。
- 公钥指纹留痕：`openssl pkey -pubin -in release.pub -outform DER | openssl sha256`
  ——指纹写入发布记录（release 记录=人读通道，不进 tools.lock）。

## 2 保管（离线介质+双控）

- 私钥仅存离线介质（加密 U 盘/智能卡），恢复口令双人分持（双控：任一人不掌握完整
  口令材料）；介质封存编号与 §1 仪式记录联动。
- 丢失/疑似泄露处置：立即走 §4 替换流程换新钥，并以新钥整锁重签（§3）；旧公钥在
  发布记录中标记 revoked（tools.lock 无需回滚——重签即换锚）。

## 3 重签（install/resign-tools-lock.py）

- 脚本：`python3 install/resign-tools-lock.py --lock tools.lock --key release-priv.pem`
  （离线介质机上执行；`--out` 可另存）。非交互：不读 stdin；缺省打印「须离线介质机
  执行」提示行后照常执行（提示非拦截——CI 测试链用 TEST-ONLY 夹具钥在仓内可重签，
  脚本可测性优先）。
- 签名覆盖=行前四字段规范串「键\t版本\tsha256\t」的 sha256 digest
  （`supply_chain.canonical_digest` 单源）；注释行/format_version 行不签名原样保留。

### 3.4 digest 复算（目录键/系统工具键）

- **目录键**（engines-web-blackbox / engines-vuln-agent / engines-session-viz，
  version=snapshot-N）：
  `sha256( "".join(f"{relpath_posix}\t{sha256(文件)}\n" for 相对路径排序的全部文件) )`
  （排除 `__pycache__`；一次扩键/引擎内容变更后重算并重签）。
- **系统工具键**（python / docker）：无发布工件可哈希——
  `sha256("键\t版本\tsystem-tool-no-artifact")`，版本钉死即锚（版本行变更=重签）。
- **nuclei-templates**：sha256 列=`engines/nuclei/templates.lock` 整文件 sha256；
  模板行变更走 engines/nuclei/README.md 四步流程后整锁重签。

### 3.5 upstream_commit 真锚（获取时点与复验纪律）

- T9 落地值：`3e0e38f50a4159ada6cf20acf6cccfea03f1bee1`（main 分支 tip）。
- 获取通道（如实记录）：git 协议 clone/ls-remote 在执行环境超时不可达，改走 GitHub
  REST API 双端点互证——`/repos/projectdiscovery/nuclei-templates/commits?sha=main&per_page=1`
  与 `/repos/projectdiscovery/nuclei-templates/branches/main` 同值方锚定
  （pushed_at=2026-09-26T03:15:37Z）。**API 缓存风险已识别**：曾出现 `/branches/master`
  返回陈旧缓存值——两端点不一致时**不得锚定**（不造数据纪律）。
- 复验：换锚重签前按同双端点流程重查一次；不一致=挂起人工裁决。

## 4 替换（release.pub 换生产公钥）

- 生产钥就绪后：`engines/nuclei/release.pub` 替换为生产公钥（显式
  `tanyin-install --release` 通道，交互确认行确认后生效；本批 --release 交互通道
  待批次 6 出口评审统一接线，当前替换动作=人工换文件+整锁重签+全套验证）。
- 同步动作：①§3 整锁重签（生产钥）②发布记录追加公钥指纹行 ③旧 TEST 钥保留于
  `tests/fixtures/keys/`（CI 永用，见 §5）。

## 5 CI 关系（信任锚分离，永续纪律）

- CI 与全部测试**永续使用 TEST-ONLY 夹具钥**（`tests/fixtures/keys/test-signing-key.pem`，
  与仓内 `engines/nuclei/release.pub` 配对自证）——**与生产钥无信任关系**：测试不因
  生产钥缺席而红，生产钥永不进仓、不进 CI。
- §4 替换=原子变更：release.pub（公钥）与整锁重签（新签名）必须同一次提交落地——
  仓内任意中间态（新钥旧锁/旧钥新锁）均验签失败=fail-closed，绝不静默放行。
