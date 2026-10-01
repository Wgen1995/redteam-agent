# 扫雷信息板（每批追加；WU 派发时附带相关条目，DEFINE 判据必须对照）

## fact（确定性事实——工具可复验，必须带 file:line 证据）

| id | 内容 | 证据(file:line) | 发现 WU | 状态 |
|---|---|---|---|---|
| F-001 | 框架反序列化防护=ObjectInputFilter 类白名单，实现在 B.java 的 resolveClass | java/a/B.java:8 | WU-0001 | verified |

## clue（判定线索——LLM 发现可独立复核的基准，结论仍独立下）

| id | 内容 | 证据 | 适用 sink 类 | 状态 |
|---|---|---|---|---|
| C-001 | resolveClass() 对全部反序列化入口做类名校验 | java/a/B.java:8 | SINK-DESERIALIZE | verified |

## break（已确认断点——负向级联；下游引用时仍需一次独立复核）

| id | 路径段 | 证据 | 状态 |
|---|---|---|---|
| B-001 | r2 输入→exec 分支不流（execArgs 为常量拼接） | java/c/D.java:30 | verified |

## 精查清单（雷邻：雷的 flow 链上游未查检查点）

| checkpoint_id | 原因 | 关联雷(sink_id) |
|---|---|---|
| CP-000004 | 雷 C-00001-00001-1d832469 链上游 source 前向复核 | C-00001-00001-1d832469 |
