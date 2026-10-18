# term ｜ 文件级兜底判据

> kind=term 的卡使用本判据（不按漏洞类组织）。
> 归属口径（D-075）: 净化决策表与传播判定归各类页面⑤节（LLM 判读形态），暂不下沉 pattern 文件；机器读需求出现时经 CALIBRATION 下沉为 sanitizer/propagator pattern（pattern-file-schema §1 三角色）。
> 来源/校准: v1.3.2 定稿基线 ｜ 最近校准: S1 起步集（2026-08） ｜ 演化纪律: append-only+人工批准（CALIBRATION 通道，B-115/B-116）
> 目标：识别本文件内一切形似 source/sink/分发器但**不在冻结清单**中的结构。

## 判定流程

C1 本文件是否有清单外的危险 API 调用（不在 sink_inventory 中的执行/查询/写入类调用）？｜引用:文件内可疑行｜推翻:文件内全部危险点已在清单｜反向:动态拼接的函数名
C2 本文件是否有清单外的入口（不在 source_inventory 中的路由/监听/定时触发）？｜引用:入口注册行｜推翻:全部入口已枚举｜反向:反射/DI 注入的隐式入口
C3 本文件是否包含硬编码凭据/密钥/连接串（yml/config/env 类文件）？｜引用:凭据行原文｜推翻:全部凭据走环境变量｜反向:注释中的示例凭据
C4 本文件是否有安全配置问题（debug=true / csrf 注释 / 权限配置错误）？｜引用:配置行原文｜推翻:配置安全｜反向:被注释的安全中间件

## 终态

- C1-C4 全部推翻 → `refuted`，reason: `no-unlisted-hazard`
- 任一 C 成立 → `candidate`，reason 说明形态和位置
- 文件为空（0 行）→ `refuted`，reason: `empty-file`
- 文件为测试/示例（role 列已标注）→ `not_applicable`
