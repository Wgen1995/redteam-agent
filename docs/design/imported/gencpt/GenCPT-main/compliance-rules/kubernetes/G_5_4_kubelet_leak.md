# G_5_4 Kubelet 信息泄露防护（5 条）

CIS Kubernetes Benchmark v1.8.0 — 5.4 Worker Node Configuration: Kubelet 信息泄露端点与调试功能关闭。
覆盖 K8s-5.4.1 至 K8s-5.4.5，共 5 条规则。
覆盖 profiling、cAdvisor、调试端点、PodLogs 限制、metrics 暴露。

---

### K8s-5.4.1 Kubelet --profiling=false

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--profiling=[^ ]*' || grep 'enableProfiling' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: `--profiling=false` 或 `enableProfiling: false`
**判定标准**: pass=profiling 为 false，fail=未设置（默认 true）或为 true，na=不适用
**修复建议**: 在 config.yaml 中设置 `enableProfiling: false`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.4.1 "Ensure that the --profiling argument is set to false"
**攻击面关联**: AS-4 数据泄露（kubelet /debug/pprof 暴露 goroutine 栈可能含密钥片段）

---

### K8s-5.4.2 Kubelet 关闭 --enable-debugging-handlers

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--enable-debugging-handlers=[^ ]*' || grep 'enableDebuggingHandlers' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: `--enable-debugging-handlers=false`（生产环境建议关闭 /exec /run /port-forward）
**判定标准**: pass=false 显式声明，fail=true 或未设置（默认 true），na=不适用（开发/调试集群可豁免）
**修复建议**: 在 config.yaml 中设置 `enableDebuggingHandlers: false`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.4.2 "Ensure that the --enable-debugging-handlers argument is set to false"
**攻击面关联**: AS-1 逃逸（在认证通过前提下 exec 接口是容器内 RCE 入口）

---

### K8s-5.4.3 Kubelet --stderrthreshold 限制日志写盘

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--stderrthreshold=[^ ]*' || grep -A2 'logging' /var/lib/kubelet/config.yaml 2>/dev/null | grep 'stderrThreshold' || echo 'NOT_SET')")
```

**期望值**: `--stderrthreshold=2` 或类似（INFO 级别日志可被 systemd-journald 集中收集）
**判定标准**: pass=stderrthreshold 设置合理（0-3），fail=未设置导致默认 INFO 日志丢失或被本地循环覆盖，na=不适用
**修复建议**: 在 kubelet 启动参数中设置 `--stderrthreshold=2 --logtostderr=true`，避免 kubelet 写入节点本地不受轮转的日志文件
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.4.3 "Ensure that the kubelet logging configuration is set appropriately"
**攻击面关联**: AS-4 数据泄露（日志未集中收集则攻击痕迹可通过本地 /var/log 覆盖清理）

---

### K8s-5.4.4 Kubelet --housekeeping-interval 合理

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kubelet | grep -v grep | grep -o -- '--housekeeping-interval=[^ ]*' || grep 'housekeepingInterval' /var/lib/kubelet/config.yaml 2>/dev/null || echo 'NOT_SET')")
```

**期望值**: 设置为合理间隔（默认 10s，过长会延迟资源监控）
**判定标准**: pass=10s ≤ value ≤ 60s，fail=value < 5s（频繁统计过载）或 > 5m，na=不适用
**修复建议**: 在 config.yaml 中设置 `housekeepingInterval: 10s`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.4.4 "Ensure that the --housekeeping-interval is set appropriately"
**攻击面关联**: AS-5 拒绝服务（过频统计可放大 DoS）

---

### K8s-5.4.5 Kubelet metrics 端点未暴露公网

**检查命令 [L0]**:
```bash
ssh_execute(server, "ss -tlnp 2>/dev/null | grep -E 'kubelet|10250|10255|10248' || netstat -tlnp 2>/dev/null | grep -E 'kubelet|10250|10255|10248')")
```

**期望值**: kubelet 10250/10248 仅监听本机或节点内网网卡，不含 0.0.0.0
**判定标准**: pass=监听地址不含 0.0.0.0/::，fail=包含 0.0.0.0 或可外网访问 IP，na=不适用
**修复建议**: 在 config.yaml 中将 `address: 0.0.0.0` 改为内网 IP 或 127.0.0.1（保留 healthz 端口的探针需求）
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 5.4.5 "Ensure that the kubelet secure/metrics ports are not exposed to the public network"
**攻击面关联**: AS-3 网络（kubelet 端口暴露公网可被暴力破解或漏洞利用）