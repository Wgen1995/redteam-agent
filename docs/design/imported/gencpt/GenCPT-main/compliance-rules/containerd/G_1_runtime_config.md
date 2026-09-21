# G_1 Containerd 运行时配置（3 条）

CIS Containerd Benchmark — 运行环境配置检查。
覆盖 Containerd-1.1 至 Containerd-1.3，共 3 条规则。

---

### Containerd-1.1 Containerd 版本检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "ctr --version 2>/dev/null || containerd --version 2>/dev/null")
```

**期望值**: 当前受支持的稳定版本（如 1.6.x 或 1.7.x）
**判定标准**: pass=containerd 已安装且版本为受支持的稳定版本，fail=版本过旧（1.4 及以下）或未安装，na=主机不运行容器运行时
**修复建议**: 参照官方文档升级 containerd：`apt-get update && apt-get install -y containerd.io` 或从 https://github.com/containerd/containerd/releases 下载二进制包安装
**CIS映射**: CIS Containerd Benchmark - 1.1 "Ensure Containerd version is up to date"
**攻击面关联**: AS-2 认证授权（旧版本含已知漏洞，可被利用进行权限提升或逃逸）

---

### Containerd-1.2 Containerd 安装检查

**检查命令 [L0]**:
```bash
ssh_execute(server, "which containerd 2>/dev/null && which ctr 2>/dev/null && which containerd-shim 2>/dev/null")
```

**期望值**: 三个可执行文件均存在
**判定标准**: pass=containerd、ctr、containerd-shim 均已安装，fail=任一组件缺失，na=主机不运行容器运行时
**修复建议**: 安装缺失组件：`apt-get install -y containerd.io` 或手动部署二进制到 `/usr/bin/`
**CIS映射**: CIS Containerd Benchmark - 1.2 "Ensure Containerd is installed correctly"
**攻击面关联**: AS-2 认证授权（缺失组件导致运行时不完整，可能引发安全策略失效）

---

### Containerd-1.3 Containerd 独立分区与审计

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -E 'containerd|ctr' /etc/audit/rules.d/audit.rules 2>/dev/null || auditctl -l 2>/dev/null | grep -E 'containerd|ctr'")
```

**期望值**: containerd 相关路径已配置审计规则
**判定标准**: pass=已配置 containerd 审计规则，fail=未配置审计规则，na=系统未启用 auditd
**修复建议**: 添加审计规则：
```bash
echo "-w /usr/bin/containerd -p wa -k containerd" >> /etc/audit/rules.d/audit.rules
echo "-w /usr/bin/ctr -p wa -k containerd" >> /etc/audit/rules.d/audit.rules
echo "-w /etc/containerd/config.toml -p wa -k containerd" >> /etc/audit/rules.d/audit.rules
service auditd restart
```
**CIS映射**: CIS Containerd Benchmark - 1.3 "Ensure audit rules are configured for Containerd"
**攻击面关联**: AS-4 数据泄露（缺少审计无法追踪 containerd 配置篡改和异常操作）