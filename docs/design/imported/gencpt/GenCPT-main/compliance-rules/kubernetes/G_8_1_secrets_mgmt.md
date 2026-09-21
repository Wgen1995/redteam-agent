# G_8_1 Secret 管理（2 条）

CIS Kubernetes Benchmark v1.8.0 — 8.1 Kubernetes Policies: Secret 加密与轮换策略。
覆盖 K8s-8.1.1 至 K8s-8.1.2，共 2 条规则。
确保 etcd 中 Secret 加密存储且无长生命周期明文对外暴露。

---

### K8s-8.1.1 etcd 中所有 Secret 已加密存储

**检查命令 [L0]**:
```bash
ssh_execute(server, "ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--encryption-provider-config=[^ ]*' || cat /etc/kubernetes/manifests/kube-apiserver.yaml 2>/dev/null | grep -o -- '--encryption-provider-config=[^ ]*' || echo 'NOT_SET'; ENC_FILE=$(ps -ef | grep kube-apiserver | grep -v grep | grep -o -- '--encryption-provider-config=[^ ]*' | cut -d= -f2); cat \$ENC_FILE 2>/dev/null | grep -oE 'aescbc|aesgcm|secretbox|kms' || echo 'WEAK_OR_NONE'")
```

接着抽样验证：
```bash
ssh_execute(server, "kubectl get secrets -A -o json 2>/dev/null | jq -r '.items[0].data' | head -5")
```

**期望值**: --encryption-provider-config 已设置且配置包含非 identity 强加密提供器（如 aescbc/kms/secretbox）
**判定标准**: pass=已设置 EncryptionConfiguration 含非 identity 提供器，fail=未设置或仅 identity，na=不适用
**修复建议**: 创建 EncryptionConfiguration：
```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources: ["secrets"]
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-key-32-bytes>
      - identity: {}
```
并设置 `--encryption-provider-config=/etc/kubernetes/enc-config.yaml`，然后通过 `kubectl get secrets --all-namespaces -o yaml | kubectl replace -f -` 重新加密现有 Secrets
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.1.1 "Ensure that secrets are encrypted at rest"
**攻击面关联**: AS-4 数据泄露（未加密 etcd 直接 dump 即得明文 Secret 与数据库凭证）

---

### K8s-8.1.2 Secret 不通过环境变量明文传递

**检查命令 [L0]**:
```bash
ssh_execute(server, "kubectl get pods -A -o json 2>/dev/null | jq -r '.items[] | .spec.containers[] | .env[]? | select(.valueFrom.secretKeyRef != null) | .name' | wc -l")
```

**期望值**: 必要时令 env 从 secret 引用，但应避免明文写死；最佳实践为卷挂载 `/var/secrets/...` 以便运行时审计
**判定标准**: pass=大量 Secret 通过 envRef 暴露的环境变量有可信扫描策略或采用卷挂载替代，fail=大量明文 secret 通过 envRef 注入且无法审计，na=不适用
**修复建议**: 改用 Secret 卷挂载：`volumeMounts: [{name: secret-vol, mountPath: /var/secrets/app}]`
**CIS映射**: CIS Kubernetes Benchmark v1.8.0 - 8.1.2 "Ensure that secrets are mounted as volumes rather than environment variables"
**攻击面关联**: AS-4 数据泄露（env 变量泄漏经应用日志/heapdump/proc fs 直接暴露密钥）