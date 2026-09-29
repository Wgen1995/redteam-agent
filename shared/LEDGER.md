# LEDGER.md——账本命令签名冻结面索引（批次 10 P2#10 实体化）

> **状态**：指针页（非签名正文）。命令签名「附录 A」在 v2 定稿中未随文发布（02-commands.md 探知项 1），
> 本页收口 12 处 `shared/LEDGER.md 附录 A` 悬空引用——引用一律解析到本页，由本页指路。

## 附录 A 底稿在哪

- **底稿**：`contracts/02a-command-signatures-draft.md`（被授权推导稿；**升格正式稿=人工终审项**，通过后本页改指正式稿）。
- **机器面单源（真签名执法）**：`cli/ledger/registry.py` 的 KNOWN_COMMANDS 派生注册表——CLI 分发/自检（selfcheck）按此校验，文档与实现漂移以 registry 为准。
- **誊录对照面**：`contracts/09-cli-surface.md`（只誊不创，探知项同律）。

## 漂移裁决律

签名争议时位序：registry.py（实现执法面）→ 02a（推导底稿）→ 09（誊录面）。三者不一致=缺陷，登记 docs/design/ 台账。

*(2026-09-30，批次 10 T6；02a 去 -draft 后缀与终审升格=人工项，见 HANDOFF。)*
