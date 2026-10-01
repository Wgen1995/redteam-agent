# 安全审计报告 — 测试夹具

## 违规汇总

| 严重度 | 数量 |
|---|---|
| Critical | 1 |

## 分级分区表

| # | 严重度 | 摘要 | 对象定位 | 详情 |
|---|---|---|---|---|
| 1 | Critical | B.java 反序列化无类过滤 | java/a/B.java:10 | [查看](findings/C-00001-00001-1d832469-critical-SINK-DESERIALIZE-B.java-10.md) |

## Gate-1

Gate-1 由宿主对账块执行，结果见 gate_record.md，gate_result=pass。
