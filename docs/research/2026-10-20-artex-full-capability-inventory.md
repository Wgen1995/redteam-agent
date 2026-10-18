# ARTEX 全量能力清点(2026-10-20 源码实勘,用户质问后补全)

背景: 此前仅有 UI 实录+三次抽查,用户质问「到底有没有看全部能力」。本清点=路由表+server 130 件+agent 目录+docs 逐面过。

## 一、证据中心工程(此前最大遗漏)
- 漏洞↔流量绑定: 角色制(baseline/proof/verification/supporting)+排序+解绑+乐观并发版本(旧版本拒写)
- 独立报告Agent: 入库→自动触发→traffic_search/traffic_get核对→绑定→按最新证据版本写报告(挖洞与报告分离)
- 双ID: finding_id(独立漏洞记录)≠finding_node_id(探索节点)
- 零猜测纪律: 不猜ID/不按域名时间推定/无包不强制/失败不产部分漏洞/绑定失败全回滚
- 设置生命周期: agent_traffic_binding默认关(token成本感知),下轮生效,运行中会话拒新设置

## 二、一切皆API可编辑
planner/prompt+preview+visibility(规划器大脑可编辑) | 技能zip上传+使用量统计(skill_zip/skill_usage/tool_usage) | task_templates | 通知渠道管理 | companies/:id/scope多租户 | 批量全家桶(archive/control/category/delete batch) | task_archive_package整仗导出 | tasks/:id/llm/resolution逐任务LLM

## 三、运维成熟度
自更新带保险(校验/冒烟/3败自动回滚artex.old) | ScopeSentry资产同步(域名/子域/IP/端口/端点按项目任务维度) | webui_embed单二进制

## 四、Agent内部件
blackboard继承(任务继承证据只读) | deferred延迟动作 | coldgraph冷摘要 | constraints约束 | capture_approval | planner/mainagent分离 | promptcatalog | compaction上下文压缩

## 五、对GraphLed设计冲击(三处)
1. 账本证据链升格: 意图产出挂证据版本,写报告核版本;报告Agent=验证官变体(与验证官非LLM错开互补)
2. 六维配置「指引」=界面可编辑+预览对象,不写死
3. 飞轮仪表: 技能卡使用量+命中统计进知识库页
