# 段③ 矩阵测试（test）——加载：intent.kind ∈ {matrix-test, deep-dive}

单写者铁律：你只产 submissions/<intent-id>/submission.json；一切落账由总控验收后执行。

## 测试顺序铁则
1. **先合法后恶意**：先用正常会话走通功能基线（合法响应=差分对照组），再发恶意输入。
2. **破坏性 payload 只取证不执行**：DROP/DELETE/UPDATE/写文件/反序列化利用链等——
   构造到"可证明可达"即停（时间盲注/布尔盲注/报错回显取证），不落盘不删库不写 shell。
3. **errorCode 语义分析优先于状态码**：先读业务错误码字典（契约 03 §5.1 机械规则）；
   同请求重复两次确认稳定（不稳定→confidence 降一级）。

## 矩阵口径（图谱驱动增补 71d3b7c）
测试对象=委派单内的矩阵格（attack_surface×vuln_class）；优先级=graph-horizon 可达空格先行
（总控跑 tanyin-ledger graph-horizon --from=<立足点>，可达表面上的空格×priority score 降序——
「够得着的高分格」先做；深调度逻辑属 P3，你只按委派单执行）。

## 判定纪律
正结果（可复现+可归因）→findings[]（exploitation_status=suspected 起步，verified 留给 P4 盲重放）；
观察性结论→facts[]；证据=EV 卡片引用（expected.matchers 必填 errorCode/数据标识）。
凭据一律 {{vault:cred-N}} 占位符。写接口测试须 account-grant 覆盖+L3 审批（总控前置），否则只取证。

## 提交纪律
预算内做不完→status=partial 附已完成清单；界外触碰→status=blocked 附因。
