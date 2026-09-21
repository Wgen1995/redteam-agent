# G_4 Containerd 镜像构建（2 条）

CIS Containerd Benchmark — 镜像构建安全检查。
覆盖 Containerd-4.1 至 Containerd-4.2，共 2 条规则。

---

### Containerd-4.1 镜像签名验证

**检查命令 [L0]**:
```bash
ssh_execute(server, "grep -E 'image_decryption|key|verify' /etc/containerd/config.toml 2>/dev/null; crictl config 2>/dev/null | grep -i verify; echo '---'; cat /etc/containerd/config.toml 2>/dev/null | grep -A5 -i 'registry.*mirrors\\|plugins.*cri.*registry'")
```

**期望值**: 配置了镜像签名验证策略（如 cosign、notation 或 containerd 原生验证）
**判定标准**: pass=已配置镜像签名验证机制，fail=未配置任何签名验证，na=仅使用私有可信仓库且无需签名验证
**修复建议**: 配置镜像签名验证，例如使用 cosign：
```bash
# 安装 cosign
cosign init
# 或在 config.toml 中配置 registry 凭证和验证策略
# 然后拉取时验证：ctr images pull --verify cosign registry/image:tag
```
**CIS映射**: CIS Containerd Benchmark - 4.1 "Ensure image signature verification is configured"
**攻击面关联**: AS-4 数据泄露（未验证签名的镜像可能被篡改，植入恶意后门或窃取数据）

---

### Containerd-4.2 镜像最小化配置

**检查命令 [L0]**:
```bash
ssh_execute(server, "ctr images ls -q 2>/dev/null | head -20; echo '---'; crictl images 2>/dev/null | head -20")
```

**期望值**: 仅保留必要的基础镜像，无多余调试工具和冗余软件包
**判定标准**: pass=镜像列表精简，无冗余非生产镜像（如 debug 工具镜像、latest 标签的临时镜像），fail=存在大量非必要镜像或 latest 标签镜像，na=无镜像运行
**修复建议**: 清理非必要镜像：
```bash
# 列出所有镜像并审查
ctr images ls -q
# 删除非必要镜像
ctr images rm <unnecessary-image>
# 使用最小化基础镜像（如 distroless、alpine）
# 构建时使用多阶段构建减小镜像体积
```
**CIS映射**: CIS Containerd Benchmark - 4.2 "Ensure minimal images are used"
**攻击面关联**: AS-1 容器逃逸（大型镜像含更多攻击面和工具，被入侵后可被攻击者利用进行横向移动）