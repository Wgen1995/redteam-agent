# 批1「止血与兑现」施工计划(蓝图 a0dc3ad 的批1细化;等 D-e 批准即动工)

## 目标(一句话)
把授权真实性/UI 点火/一键战斗/D2 三臂同考/VulnClaw 插槽落地六件小件高杠杆活干完——让现有骨架立刻产出对外价值。

## 任务分解(每件独立可验收,TDD:先红后绿)

### T1 授权八问真实化(03+06+09 同件;口径等 D-d①:推荐真上传)
- new.html 八问表单补齐(授权文件上传+sha256 计算+窗口期/范围/OOB/预算/凭据/强度)
- server.py 废 --allow-missing-auth 豁免路径,走 write_cmds.py:304-324 真校验
- 测试: 未带授权件建战=拒;带件=过;旧豁免路径删除钉
- 工期 1.5-2 天

### T2 launch 点火钮+摆设字段处理(06)
- CTRL_ACTIONS 增 launch;new.html 四个 disabled 字段:接线或砍(推荐砍,不假装)
- 测试: 浏览器全程「建战→点火」链路;写路由协议钉
- 工期 1 天

### T3 tanyin serve 收口+输出契约(01+06+09 同件)
- 单命令起 webui;CLI 面:--json/退出码分离(rc=2 环境/gate-error 区分)
- 测试: serve 冒烟+退出码矩阵+--json 回读
- 工期 1-2 天

### T4 battle auto 一键链(08)
- battle.py auto: init→launch→看护→自动 settle→自动报告
- 测试: 假战士全链 SIM(无 LLM 依赖);夜回归底座
- 工期 1-2 天

### T5 D2 三臂基线同考(07+08;统计换血+污染执法+记分牌)
- 配对置换 N≥4 主检验+诱饵负对+GT-free sanitized 工作区+三臂(探隐/ARTEX/VulnClaw@4.7)+20 字段登记+记分牌 tsv
- 测试: 尺子单测+干跑一卷小样
- 工期 4-5 天(含真打)

### T6 VulnClaw 插槽落地(05)
- 消费 final_answer+verified_claims(findings[] 只当线索队列);副作用黑名单进 TaskConstraints;成本外挂网关侧;绕 P0#2 收尾崩(手动 report)
- 测试: 插槽适配器单测+对靶场一战验通
- 工期 2-3 天

## 验收门(批1整体)
- 全量测试绿;授权伪造路径零残留;浏览器可全程建战到报告;D2 记分牌出第一行真数;插槽一战有效发现≥1 复现成立
## 纪律
- 每任务独立 commit+HANDOFF 行(宪法#36);文件产出即呈(宪法#37);不动用户 ZhuLong 仓
