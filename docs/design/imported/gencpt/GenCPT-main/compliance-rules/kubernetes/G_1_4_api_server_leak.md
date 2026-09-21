# G_1_4 API Server 信息泄露防护（3 条）

CIS Kubernetes Benchmark v1.8.0 — 1.4 Control Plane Configuration: API Server 信息泄露防护。
覆盖 K8s-1.4.1 至 K8s-1.4.3，共 3 条规则。
针对调试端点、HTTP 明文端口和对外监听地址等信息泄露入口的防护。

---

### K8s-1.4.1 禁用 API Server profiling 调试端点

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--profiling=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--profiling=[^ ]*' || echo 'NOT_SET')")
```

**期望值**: `--profiling=false`
**判定标准**: pass=参数值为 false，fail=参数值为 true 或未设置（默认 true），na=不适用
**修复建议**: 在 kube-apiserver 启动参数中设置 `--profiling=false`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.4.1 "Ensure that the --profiling argument is set to false"
**攻击面关联**: AS-4 数据泄露（pprof 端点暴露内部状态、goroutine 堆栈、内存样本，可泄露密钥片段和运行时数据）

---

### K8s-1.4.2 禁用 API Server 不安全 HTTP 绑定地址

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--insecure-bind-address=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--insecure-bind-address=[^ ]*' || echo 'NOT_SET')")
```

**期望值**: `NOT_SET`（参数未设置）或值为 `127.0.0.1`（仅本地回环）
**判定标准**: pass=--insecure-bind-address 未设置或仅绑定 127.0.0.1，fail=--insecure-bind-address 绑定非回环地址（如 0.0.0.0），na=不适用
**修复建议**: 移除 kube-apiserver 启动参数中的 `--insecure-bind-address`，或将其设置为 `127.0.0.1`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.4.2 "Ensure that the --insecure-bind-address argument is not set"
**攻击面关联**: AS-3 网络（明文 HTTP 绑定对外网卡允许未加密跨网段访问 API Server）

---

### K8s-1.4.3 关闭 API Server 不安全 HTTP 端口

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--insecure-port=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -o -- '--insecure-port=[^ ]*' || echo 'NOT_SET')")
```

**期望值**: `NOT_SET`（参数未设置）或 `--insecure-port=0`
**判定标准**: pass=--insecure-port 未设置或值为 0，fail=--insecure-port 值为非零正整数（如 8080），na=不适用
**修复建议**: 移除 kube-apiserver 启动参数中的 `--insecure-port`，或将其设置为 `0`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 1.4.3 "Ensure that the --insecure-port argument is set to 0"
**攻击面关联**: AS-2 认证授权（insecure-port 上的请求不受 TLS/认证/授权约束，等效于 把 API Server 开放为匿名特权接口）