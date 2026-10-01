# SINK-DESERIALIZE 簇结论

## 攻击模式对抗表

| 攻击模式 | 知识引用 | 目标防御点 | 对抗结果 | 证据行 |
|---|---|---|---|---|
| 无过滤反序列化 | FALSE-rules 无命中 | ObjectInputFilter | 击破 | java/a/B.java:10 |
覆盖 basis: s1 s2 s3 r1
