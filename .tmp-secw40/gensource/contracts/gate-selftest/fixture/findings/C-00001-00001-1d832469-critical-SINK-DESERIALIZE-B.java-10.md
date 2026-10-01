# V01: B.java 反序列化无类过滤

## 1. 识别信息

| 字段 | 值 |
|---|---|
| candidate_id | C-00001-00001-1d832469 |
| finding_id | V1 |

## 2. 漏洞摘要

测试夹具：readObject 无 ObjectInputFilter。

## 3. 调用链

source: doPost(req) -> sink: readObject（java/a/B.java:10）

## 4. CVSS 3.1 评分

CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H (9.8)

## 5. 详细分析

测试夹具详情。

## 6. 数据流语义变迁表

| step | location | variable | semantics | state | cause |
|---|---|---|---|---|---|
| 1 | java/a/B.java:10 | data | raw | tainted | request |

## 7. 证据分级标注

全 direct（测试夹具）。

## 8. 三态结论

verdict: confirmed, confidence: 0.6, runtime_tier: 6
## 三态结论补充

置信度推导：tier6 静态、三要素证据级全 direct（java/a/B.java:10、java/a/B.java:20、java/c/D.java:5 三条观测），逐项推导非套版。

门禁核对：E5 四相等通过、E21 时序通过。
## 详细分析补充

测试夹具：readObject 无 ObjectInputFilter，防护缺失的直接证据在 java/a/B.java:10（readObject 调用行）、java/a/B.java:12（未设置 filter 的行）、java/c/D.java:5（同族对照）。

影响分析：任意类反序列化 → gadget 链 RCE。

修复建议：增加类白名单过滤。

证据补充：clusters/SINK-DESERIALIZE.md 对抗表行 1（击破，证据行 java/a/B.java:10）。

