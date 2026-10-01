# Phase 2 Verification & Rating

> version=v0.3.9 | runtime_verification=denied

## Stage Gate Summary

| Candidate | Verdict | Confidence |
|---|---|---|
| C-00001-00001-1d832469 | confirmed | 0.6 |

## Candidates

### C-00001-00001-1d832469: B.java 反序列化无类过滤

**FALSE-rules**: none hit.

**Three Elements**:

| Element | Annotation | evidence_grade |
|---|---|---|
| controllable_source | direct | direct |
| reachable_path | direct | direct |
| failed_control | direct | direct |

**默认配置可达性（v0.3.9 配置越界关卡）**: 组件默认启用，无认证前置——默认配置下可达（证据: java/a/B.java:10）。
