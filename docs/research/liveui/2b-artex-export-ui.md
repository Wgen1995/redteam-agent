# 2b · ARTEX 导出页 UI 实事求是分析（2026-10-15）

样本: ~/Downloads/ARTEX — 自主渗透测试控制台.html（676KB,676K/18K 对比探隐 v3 双胎）。方法: 全文提取 CSS 变量+布局类名逐条核。

## 借鉴（实证）
1. **12 级灰阶令牌** gray1(99%)~gray12(9%): 文字层次用 9~12、表面用 2~5——探隐 8 变量不够，升级为 12 级结构（数值按 ZhulongFire 重调）。
2. **左侧栏骨架**: 图标+文字导航/分组标题/可折叠。ARTEX 33 视图、ZhuLong/multica/dsh 全用侧栏——工作台类产品的行业唯一共识。**v0.9d 顶栏八链改为侧栏**（页面将超 10 个）。
3. 圆角 8px、轻阴影、全站仅 pulse+spin 动画——与 ZhulongFire 动效预算律一致。
4. 语义徽章色系（已在 CSAI 偷单）。

## 不搬（实证）
1. 技术栈: Tailwind/shadcn/React→676KB 页重; 探隐手写 18KB 同密度（tanyin-architecture-v3 互证手写路线可行）。零依赖律不破。
2. zinc 全灰品牌: 探隐品牌=ZhulongFire 蓝 #2563EB。
3. RTL 双向布局变量、lucide 图标依赖（图标手绘 SVG path 内联）。

## 结论
视觉体系照抄骨架，技术一个字节不搬。UI 布局定稿图见 docs/design/ui-design-v1.md（同日）。
