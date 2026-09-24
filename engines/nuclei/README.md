# nuclei 离线模板快照（批次 4 T10）

## 快照内容与来源

- `templates/*.yaml`：三份**自写**精选模板（MIT/自创——上游 nuclei-templates 仓库仅作
  结构范本，不搬运其内容）：exposed-panel（管理面板暴露）/ actuator-leak（Spring Boot
  actuator/env 泄露）/ swagger-leak（swagger api-docs 暴露）。
- `templates.lock`：快照清单——首行 `upstream_commit`（钉 40hex commit）+ 每模板一行
  `<相对路径>\t<sha256>`。适配器启动先逐文件重算 sha256 比对（验签先于归一化）。
- `release.pub`：ECDSA 验签公钥（与 tools.lock 各行签名配对）。

## 快照更新流程（四步）

1. **选 commit**：确定上游 nuclei-templates 目标 commit（40hex），写入 templates.lock
   首行 `upstream_commit=` 与 tools.lock `nuclei-templates` 行末列（两处一致）。
2. **自写/审模板**：新增或修订 `templates/*.yaml`（保持自写，不搬运上游内容；结构与
   matcher 子集对齐契约 06 勘误：word/status+AND）。
3. **sha256 重算**：重算每模板 sha256 刷新 templates.lock 数据行；重算 templates.lock
   整文件 sha256 刷新 tools.lock `nuclei-templates` 行 `sha256` 列。
4. **重签 tools.lock**：用发布私钥对改动行重签（签名覆盖=行前四字段规范串的 sha256
   digest，见 cli/ledger/supply_chain.py `canonical_digest`），提交发布。

## 供应链与缺口披露（G-22，如实声明）

- **测试钥 TEST-ONLY**：当前 `release.pub` 与 `tests/fixtures/keys/test-signing-key.pem`
  为**批次 4 验签测试钥**（私钥进仓仅为测试自证，不构成信任根）——生产签名密钥的
  生成/保管/重签流程与 release.pub 替换=**批次 6 安装器出口**（G-22 流程缺口，本批
  仅以测试钥锚定快照结构与验签链路）。
- **commit 占位**：`upstream_commit` 与 tools.lock `nuclei-templates.commit` 当前为
  固定样例占位（40×a）——批次 6 换真上游 commit 重签。
- **运行时绝不自动安装**：nuclei 可执行缺失→适配器落 status=blocked 提交（环境受阻
  语义），绝不自动安装（契约 10 §4 铁律）；安装=批次 6 tanyin-install 幂等安装器
  （tools.lock 验签 6 步流程）。
