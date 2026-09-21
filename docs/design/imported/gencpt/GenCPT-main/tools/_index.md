# 工具索引

> 来源：设计文档 5.15.2 节
> 核心原则：原生命令优先，工具库仅为备用补充。不影响架构能力和检测逻辑。

---

## 1. 通用工具

以下工具用于环境侦察和合规检测阶段的基础操作，原生命令优先，仅在远端缺失时上传。

| 工具名 | 用途 | 大小 | 关联攻击面 | 平台 | 上传条件 |
|--------|------|------|-----------|------|---------|
| jq | JSON 解析（kubectl/docker 输出结构化提取） | 300KB | 通用 | k8s, docker, containerd | Phase 1a 预上传（所有后续 Phase 需要） |
| yq | YAML 解析（K8s 清单/配置解析） | 500KB | 通用 | k8s, docker, containerd | Phase 1a 预上传（合规规则 YAML 处理需要） |
| socat | 端口转发 / 双向网络中继 | 200KB | AS-3 网络 | k8s, docker | 按需（curl/nc 不足以验证网络连通性时） |
| curl | HTTP 请求 / API 探测 | 系统自带 | AS-2 认证, AS-3 网络 | 全平台 | 通常已有 |
| ncat/netcat | 网络端口探测 / 反弹 Shell 验证 | 100KB | AS-3 网络 | 全平台 | 按需（远端无 nc 且需端口验证时） |
| openssl | TLS 证书检测 / 加密通信验证 | 系统自带 | AS-3 网络 | 全平台 | 通常已有 |

> **说明**：通用工具中 jq 和 yq 在 Phase 1a 环境侦察完成后立即上传，因为后续合规检测和攻击验证阶段均依赖 JSON/YAML 结构化提取。其余通用工具按需上传。

---

## 2. 攻击验证工具

以下工具仅在攻击验证阶段（Phase 4a/4b）按需上传，用于深度验证原生命令无法确认的漏洞。

| 工具名 | 用途 | 大小 | 关联攻击面 | 平台 | 上传条件 |
|--------|------|------|-----------|------|---------|
| cdk | 容器逃逸/提权综合工具（evaluate、check-docker-socket 等） | 2MB | AS-1 逃逸, AS-2 认证 | k8s, docker | Phase 4a 按需（socket-escape/cgroup-escape 等模式命中且原生命令不足以验证） |
| amicontained | 容器安全配置检测（Capabilities/AppArmor/Seccomp） | 1MB | AS-1 逃逸 | 全平台 | Phase 4a 按需（需精确检测容器安全配置时） |
| checksec | 二进制安全属性检查（NX/Stack Canary/PIE/RELRO） | 50KB | AS-1 逃逸 | 全平台 | Phase 4a 按需（需检查内核/user-space 二进制保护机制时） |
| capsh | Linux capabilities 查询与打印 | 系统自带 | AS-1 逃逸 | 全平台 | 通常已有 |
| nsenter | Namespace 切换工具（进入容器 Namespace 验证逃逸） | 系统自带 | AS-1 逃逸 | 全平台 | 通常已有 |
| unshare | Namespace 创建工具（验证 Namespace 隔离） | 系统自带 | AS-1 逃逸 | 全平台 | 通常已有 |
| trivy | 镜像漏洞扫描（CVE 检测/配置审计） | 30MB | AS-4 数据泄露, AS-6 供应链 | 全平台 | 按需（较大，仅在需镜像深度扫描时上传） |
| grpcurl | gRPC 调试（containerd API 探测） | 2MB | AS-2 认证 | containerd | 按需（需与 containerd gRPC API 交互时） |

> **说明**：攻击验证工具仅在对应攻击模式命中且原生命令无法完成验证时上传。每个攻击模式 SKILL.md 的 `required_tools` 字段声明所需工具，`fallback_native` 字段提供原生命令降级方案。

---

## 3. 上传条件说明

### 3.1 上传时机

| 时机 | 上传内容 | 说明 |
|------|---------|------|
| Phase 1a 预上传 | jq, yq | 环境侦察完成后立即上传，所有后续 Phase 需要 JSON/YAML 解析能力 |
| Phase 4a 按需上传 | cdk, amicontained, checksec, trivy, grpcurl 等 | 攻击模式命中且原生命令不足以验证时，收集命中模式的 `required_tools`，合并去重后上传 |

### 3.2 工具不存在时的 Fallback 策略

每个攻击模式 SKILL.md 的 `required_tools` 字段附有 `fallback_native`，指定原生命令降级方案。上传策略：

1. **检查远端是否已有同版本工具**（避免重复上传）
2. 工具存在 → 直接使用远端工具
3. 工具不存在 → `ssh_upload` 上传到 `/tmp/cpt-tools/`
4. 上传失败 → 回退到 `fallback_native` 原生命令方案
5. 记录上传结果到 `evidence/qa/tool_upload_log.md`

**Fallback 示例**：

| 工具 | Fallback 原生命令 |
|------|-----------------|
| jq | `grep` + `awk` / `python3 -c "import json; ..."` |
| yq | `python3 -c "import yaml; ..."` |
| cdk（check-docker-socket） | `ls -la /var/run/docker.sock` + `cat /proc/1/cgroup \| head -1` + `mount \| grep docker` |
| amicontained | `cat /proc/self/status \| grep Cap` + `cat /proc/1/status \| grep Cap` |
| checksec | `readelf -l <binary> \| grep GNU_STACK` |

### 3.3 OS/架构适配

Phase 1a 环境侦察时收集 OS 和架构信息，写入 `session_config.json`：

```json
{
  "env_fingerprint": {
    "os_type": "{{os_type}}",
    "arch": "{{arch}}"
  }
}
```

工具二进制从 `tools/{{os_type}}-{{arch}}/` 目录选择。若目标架构目录不存在：
- 记录到 `evidence/qa/tool_upload_log.md`
- 该模式只能使用 `fallback_native` 原生命令
- 报告中标注"工具覆盖受限"

### 3.4 清理机制

- **会话正常结束**：`ssh_execute "rm -rf /tmp/cpt-tools/"`
- **会话中断**：`/tmp/cpt-tools/` 目录遵循 Linux /tmp 清理规则，重启后自动清理
- **清理日志**：记录在 `evidence/qa/tool_upload_log.md`

---

## 4. 非破坏性声明

工具库仅用于检测和验证，不引入持久性修改。具体约束：

1. **所有上传的工具文件仅在 `/tmp/cpt-tools/` 目录运行**，不安装到系统路径
2. **攻击验证命令遵循审批门控**（5 级审批机制），破坏性操作最高执行到 L3 条件验证
3. **差分证明优先使用无害 marker 文件**，不修改系统配置
4. **测试结束后上传的工具文件清理删除**，不留残留
5. **每个 POC 脚本包含清理/恢复步骤**，确保环境可恢复

---

*索引结束*