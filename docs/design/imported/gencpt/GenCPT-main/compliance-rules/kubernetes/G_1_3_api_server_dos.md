# G_1_3 API Server DoS 防护（1 条）

CIS Kubernetes Benchmark v1.8.0 — 1.3 Control Plane Configuration: API Server DoS 防护。
覆盖 K8s-1.3.1，共 1 条规则。

---

### K8s-1.3.1 设置 API Server 请求超时

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--request-timeout=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--request-timeout=[^ ]*' || echo 'NOT_SET')")
```

**期望值**: `--request-timeout=300s` 或具体非零值（如 `30s`、`60s`；不建议过大如 `24h`）
**判定标准**: pass=--request-timeout 已设置且值为有限时长（如 30s、60s、300s），fail=未设置（默认 0 表示无限制），na=不适用
**修复建议**: 在 kube-apiserver 启动参数中设置 `--request-timeout=300s`（按集群规模和合规要求调整具体值，但务必设置有限时长）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.3.1 "Ensure that the --request-timeout argument is set as appropriate"
**攻击面关联**: AS-5 拒绝服务（无超时限制则慢速攻击者可长期占用连接句柄耗尽 API Server 资源）