# b9 · dsh-plugin-tanyin v0.3（真 API 工具面 + 技能 provider）

> 日期：2026-10-09 ｜ 状态：已批准（用户"继续构建"）｜ 前置：架构细图 v3（docs/design/architecture-map-v3.md）
> 决策 1 修正案在册：核心保持纯 SKILL 全宿主通吃；DSH 插件=薄面厚核（技能 provider+工具桥，不复制状态）。

## 目标与出口判据
DSH 会话（装了本插件的 profile）里：①模型能列出 tanyin_book/gate/query 三工具（真 ctx.tools.register）；②技能目录出现 tanyin 技能（ctx.skills provider）；③单测+真 cordis 加载双绿。
验收命令（用户跑）：`dsh headless '列出名字以 tanyin 开头的工具，每行一个；没有答 NONE'`

## 事实源（真样本接线，全部已源码核验）
- 工具注册：`import { defineTool } from '@deepseek-ai/dsh-tools'` + `ctx.tools.register(defineTool({...}))`；模块头 `export const inject = ['tools']`（样本 redteam-bundle/lib/tools.js:16,24-27,322）
- 技能 provider：superpowers-dsh/lib/index.js 模式——扫描包内 skills/<name>/SKILL.md，YAML frontmatter 取 name/description/whenToUse，注册进 ctx.skills（HOST 层，PACKAGED_SKILL_RANK=550，source='custom'，modelInvocable+userInvocable），list() 发现/get() 按需读正文，resourceBase={kind:'directory'}
- patch 行：每子路径一行 `- id: <前缀>-<名>, name: '<pkg>/<subpath>'`；行 id 带前缀防撞（redteam-mode 教训：insert 是追加语义，撞 id=boot 失败）
- 依赖：宿主 profile workspace 提供 @deepseek-ai/dsh-tools（样本包零 runtime deps 照跑）

## 文件结构（改/建）
```
platform/dsh-plugin-tanyin/
├── package.json        # v0.3.0；exports 加 ./lib/skills.js；dsh.bundle.patch 不变
├── cordis.patch.yml    # 两行：tanyin-tools(./lib/tools.js) + tanyin-skills(./lib/skills.js)，id 前缀 tanyin-
├── lib/index.js        # 服务面保持（ctx.tanyin）
├── lib/tools.js        # 重写：defineTool 工厂+ctx.tools.register；保留 13 命令白名单/信封输出/exec.signal
├── lib/skills.js       # 新：superpowers 模式 provider（tanyin 技能入 DSH）
├── skills/tanyin/      # 新：从 .opencode/skills/tanyin 同步（SKILL.md+phases/）
├── scripts/sync-skill.sh  # 新：同步脚本（单一真源在 .opencode，插件只做镜像）
└── test/tools.test.mjs # 扩：mock ctx 断言 register 被调×3+defineTool 形；skills list/get
```

## 任务（TDD，每任务一提交）
- **T0** 本计划入册。
- **T1** scripts/sync-skill.sh + skills/tanyin 同步（前提声明：仓在盘，CLI 以仓根相对路径调用）。
- **T2** lib/skills.js provider + 单测（list 发现 tanyin/get 返回正文+frontmatter 解析容错）。
- **T3** lib/tools.js 重写（defineTool；参数 schema 沿用 v0.2 schemastery 形状→纯 JSON Schema 形；白名单/exec.signal/信封不变）+ 单测绿。
- **T4** cordis.patch.yml 两行 + package.json v0.3.0 exports。
- **T5** 真 cordis 加载集成测（断言 apply 后 ctx.tools.register 调用×3、ctx.skills 有 tanyin）。
- **T6** 重装 default profile（remove+add 防缓存陈本）+ dump-config 验证；README/架构图 🔮→✅/🟡 更新；push。
- **T7** headless 可见性终验（用户一条命令；或 key 可得时自验）。

## 风险与对策
- pnpm 复用陈缓存 → remove+add 强刷（b24 教训）
- SKILL.md 内相对引用（phases/）→ provider resourceBase=directory 天然支持；技能头加"仓在盘"前提
- 与 v0.2 已装层冲突 → 行 id 换前缀即新行，旧行 disabled 迁移条款照 redteam-mode 样式
