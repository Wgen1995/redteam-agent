# 攻击路线图升级批（ARTEX 对标,2026-10-16 用户裁决: 现图差远了）
依据: ARTEX 导出页实测拆解(节点卡=类型徽章+编号+完整句子;画布=缩放平移+小地图+0.15倍全景;数据=真战斗叙事)。
## 数据段(先行,不碰页面)
graph 投影每节点带: {num 编号, kind, badge 类型中文名, title 完整句(意图=目的原文截断/发现=完整标题/事实=摘要80字), status(进行中/已完成/未证实), impact(发现), layer}; 边保持 10 型+标签。tests 钉: 卡片字段齐/编号唯一/标题非空率。
## 画布段(文案舰收工后)
graph.html 重做: 手写 pan/zoom(wheel+drag, CSS transform, 零库)+fit 全景按钮+右下小地图+节点卡(ARTEX 式: 徽章/编号/完整标题/状态色,未证实=淡)+点卡开侧详情(全文)+边标签常显。禁碰: 其他页。
## 白名单
数据段: cli/webui/projections.py(或 graph 专用投影文件)+tests。画布段: cli/webui/static/graph.html+相关测试。
