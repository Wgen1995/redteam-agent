# G_1_5 API Server 审计日志（6 条）

CIS Kubernetes Benchmark v1.8.0 — 1.5 Control Plane Configuration: API Server 审计日志配置。
覆盖 K8s-1.5.1 至 K8s-1.5.6，共 6 条规则。
确保 API Server 开启审计日志、配置合理的轮转策略和审计策略文件。

---

### K8s-1.5.1 设置审计日志文件路径

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--audit-log-path=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--audit-log-path=[^ ]*' || echo 'NOT_SET')")
```

**期望值**: 参数设置为有效的文件路径，如 `--audit-log-path=/var/log/kubernetes/audit/audit.log`
**判定标准**: pass=--audit-log-path 设置为有效路径，fail=未设置（无审计日志），na=不适用
**修复建议**: 在 kube-apiserver 启动参数中设置 `--audit-log-path=/var/log/kubernetes/audit/audit.log`，并确保目录可写
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.5.1 "Ensure that the --audit-log-path argument is set"
**攻击面关联**: AS-4 数据泄露（无审计日志则攻击行为不可追溯，攻击者可清除痕迹后遁去）

---

### K8s-1.5.2 设置审计日志最大保留天数

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--audit-log-maxage=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--audit-log-maxage=[^ ]*' || echo 'NOT_SET')")
```

**期望值**: `--audit-log-maxage=30` 或更高（单位：天）
**判定标准**: pass=--audit-log-maxage 设置且值大于等于 30，fail=未设置或值小于 30，na=不适用（未启用审计日志时）
**修复建议**: 在 kube-apiserver 启动参数中设置 `--audit-log-maxage=30`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.5.2 "Ensure that the --audit-log-maxage argument is set to 30 or as appropriate"
**攻击面关联**: AS-4 数据泄露（保留期不足则安全事件回溯窗口被截断）

---

### K8s-1.5.3 设置审计日志最大保留份数

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--audit-log-maxbackup=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--audit-log-maxbackup=[^ ]*' || echo 'NOT_SET')")
```

**期望值**: `--audit-log-maxbackup=10` 或更高（单位：份）
**判定标准**: pass=--audit-log-maxbackup 设置且值大于等于 10，fail=未设置或值小于 10，na=不适用（未启用审计日志时）
**修复建议**: 在 kube-apiserver 启动参数中设置 `--audit-log-maxbackup=10`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.5.3 "Ensure that the --audit-log-maxbackup argument is set to 10 or as appropriate"
**攻击面关联**: AS-4 数据泄露（保留份数不足则日志轮转时历史数据被过早覆盖）

---

### K8s-1.5.4 设置审计日志单文件最大大小

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--audit-log-maxsize=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--audit-log-maxsize=[^ ]*' || echo 'NOT_SET')")
```

**期望值**: `--audit-log-maxsize=100` 或更高（单位：MB）
**判定标准**: pass=--audit-log-maxsize 设置且值大于等于 100，fail=未设置或值小于 100，na=不适用（未启用审计日志时）
**修复建议**: 在 kube-apiserver 启动参数中设置 `--audit-log-maxsize=100`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.5.4 "Ensure that the --audit-log-maxsize argument is set to 100 or as appropriate"
**攻击面关联**: AS-5 拒绝服务（单文件过大可能塞满磁盘导致 API Server 停摆）

---

### K8s-1.5.5 设置审计策略文件

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--audit-policy-file=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--audit-policy-file=[^ ]*' || echo 'NOT_SET')")
```

**期望值**: 参数设置为存在的策略文件路径，如 `--audit-policy-file=/etc/kubernetes/audit-policy.yaml`
**判定标准**: pass=--audit-policy-file 设置且文件存在（包含 Metadata/RequestResponse 等审计级别），fail=未设置或文件不存在，na=不适用
**修复建议**: 创建 `/etc/kubernetes/audit-policy.yaml` 文件，至少对 Secret、ConfigMap、RBAC、认证授权类操作记录 `RequestResponse` 级别；在 kube-apiserver 启动参数中设置 `--audit-policy-file=/etc/kubernetes/audit-policy.yaml`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.5.5 "Ensure that the --audit-policy-file argument is set"
**攻击面关联**: AS-4 数据泄露（默认只记录 Metadata 不足以还原攻击载荷与影响范围）

---

### K8s-1.5.6 设置审计日志格式为 JSON

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--audit-log-format=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--audit-log-format=[^ ]*' || echo 'NOT_SET')")
```

**期望值**: `--audit-log-format=json`（或 `legacy`，但推荐 json）
**判定标准**: pass=--audit-log-format 设置为 json（推荐）或 legacy，fail=未设置（默认 legacy 但未显式声明不合规），na=不适用（未启用审计日志时）
**修复建议**: 在 kube-apiserver 启动参数中设置 `--audit-log-format=json`，便于 SIEM 系统结构化解析
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.5.6 "Ensure that the --audit-log-format argument is set"
**攻击面关联**: AS-4 数据泄露（无格式约束导致日志不易被 SIEM 索引，攻击痕迹更易被遗漏）