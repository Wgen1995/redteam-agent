# 交叉关联查询库（Cross-Reference Queries）

> 来源：设计文档 5.3 节"三库联动"
> 作用：三库联动核心查询模板，合规结果 → 合规假设 → 攻击假设 → 侦察比对

## 查询模板

---

### XREF-001：合规违规 → 攻击假设前置条件

- **查询类型**: 合规→攻击
- **输入**: Phase 2 合规检查结果（pass/fail/warn 列表）+ `compliance-hypotheses.md` 假设卡片
- **匹配逻辑**:
  1. 遍历 Phase 2 合规结果中所有 `fail` 和 `warn` 状态的规则
  2. 对每条 fail/warn 规则，扫描 `compliance-hypotheses.md` 中所有 `CHK-CAND` 卡片的"违规族"字段
  3. 若规则 ID 匹配违规族中的条目（精确匹配或作为叠加条件的组成部分），标记该 CHK-CAND 为"命中"
  4. 对于"叠加"条目（用 `+` 连接），只有当所有组成规则都 fail 时才标记命中
  5. 收集所有命中的 CHK-CAND，使用其"映射的攻击模式"和"合规规则编号"链接到 `attack-hypotheses.md` 中的 ATK-HYP
  6. 按 CHK-CAND 严重等级排序输出：Critical → High → Medium → Low
- **输出**: 命中的合规→攻击假设映射列表，每个条目包含：
  ```
  合规违规 → CHK-CAND → ATK-HYP（攻击模式文件）
  严重等级：Critical/High/Medium/Low
  前置条件满足状态：✅ 完全满足 / ⚠️ 部分满足 / ❌ 不满足
  ```
- **示例**:
  ```
  输入：Phase 2 结果中 K8s-7.1.1=FAIL, K8s-7.1.6=FAIL
  映射步骤：
    1. CHK-CAND-001 命中（违规族含 K8s-7.1.1）
         → 映射 attack-patterns/escape/capability-privesc/SKILL.md
         → ATK-HYP-003（CAP_SYS_ADMIN 逃逸）
         → 前置条件满足状态：⚠️ 需 L1 探测验证 CapEff
    2. CHK-CAND-004 命中（违规族含 K8s-7.1.6）
         → ATK-HYP-003 + ATK-HYP-004
         → 前置条件满足状态：⚠️ 需确认 capabilities.add 是否含 SYS_ADMIN
  行动：P(escape/capability-privesc) = HIGH，进入 Phase 4a 攻击验证
  ```

---

### XREF-002：叠加放大

- **查询类型**: 叠加放大
- **输入**: Phase 2 合规检查结果 + `compliance-hypotheses.md` 假设卡片 + 同一目标标识（Pod/Node/容器）
- **匹配逻辑**:
  1. 遍历 Phase 2 合规结果，按目标（Pod/Node/容器）分组合规违规
  2. 对每个目标，收集其所有 fail/warn 规则
  3. 计算"叠加深度"：同一目标命中的 CHK-CAND 数量
  4. 叠加深度 ≥3 → 标记为"风险放大"，严重等级提升一级（High→Critical, Medium→High）
  5. 叠加深度 ≥5 → 标记为"严重放大"，严重等级直接提升为 Critical
  6. 特别关注"叠加危险组合"：
     - 特权容器(CHK-CAND-001) + docker.sock(CHK-CAND-002) + 无Seccomp(CHK-CAND-034) → 逃逸确认
     - 匿名访问(CHK-CAND-005) + RBAC过宽(CHK-CAND-006) → 权限提升确认
     - 无NetworkPolicy(CHK-CAND-008) + 云元数据可访问(CHK-CAND-027) → 凭据窃取确认
  7. 输出时标注叠加组合的可利用性评估
- **输出**: 每个目标的叠加分析报告，格式：
  ```
  目标 <标识>:
    违规数：N（列表）
    叠加深度：<深度>
    放大评级：<等级>
    触发 ATK-HYP：<列表>
    叠加危险组合：<组合名>（如果命中）
  ```
- **示例**:
  ```
  目标 pod/backend-api-deployment-abc123:
    违规数：4（K8s-7.1.1 + K8s-7.1.2 + Docker-44 + K8s-7.1.13）
    叠加深度：4
    CHK-CAND 命中：CHK-CAND-001, CHK-CAND-003, CHK-CAND-034, CHK-CAND-020
    放大评级：🔴 CRITICAL
    叠加危险组合：特权容器 + hostPath挂载 + 无Seccomp + 无PSA
    触发攻击假设：ATK-HYP-003 + ATK-HYP-002 + ATK-HYP-004
    推荐攻击路径：hostPath挂载逃逸（ATK-HYP-002，条件最充分）→ CAP_SYS_ADMIN逃逸（ATK-HYP-003）→ cgroup逃逸（ATK-HYP-004）

  目标 node-worker-01:
    违规数：3（K8s-1.2.1 + K8s-8.2.10 + CHK-CAND-027异常）
    叠加深度：3
    CHK-CAND 命中：CHK-CAND-005, CHK-CAND-008, CHK-CAND-027
    放大评级：🟠 HIGH（从Medium提升）
    叠加危险组合：匿名API访问 + 无NetworkPolicy + 云元数据可访问
    触发攻击假设：ATK-HYP-005 + ATK-HYP-008 + ATK-HYP-009
    推荐攻击路径：匿名API扫描 → 横向移动 → 元数据窃取（链式攻击）
  ```

---

### XREF-003：攻击假设前置条件 → 侦察结果比对

- **查询类型**: 攻击→侦察比对
- **输入**: `attack-hypotheses.md` 假设卡片 + Phase 1a 侦察输出（`evidence/recon/`）
- **匹配逻辑**:
  1. 遍历所有 `ATK-HYP` 卡片
  2. 逐条读取"前置条件"字段
  3. 在 Phase 1a 侦察结果中搜索验证证据（`knowledge_graph/nodes/` 和 `evidence/recon/`）
  4. 将侦察结果与前置条件做模式匹配：
     - 文件存在性匹配（如 docker.sock 挂载、hostPath 存在）
     - 配置值匹配（如 privileged=true、anonymous-auth=true）
     - 网络连通性匹配（如 169.254.169.254 可达）
  5. 为每条前置条件标记满足状态：
     - ✅ 已满足：侦察结果明确证实前置条件存在
     - ⚠️ 部分满足：侦察结果显示部分特征，需进一步探测
     - ❌ 不满足：侦察结果明确否定前置条件
     - ❓ 未检查：侦察结果未覆盖，需在 Phase 4a 中补充探测
  6. 对每个 ATK-HYP 计算前置条件综合满足度：
     - 全部 ✅ → P(HIGH)，直接进入 Phase 4a 验证
     - 含 ⚠️ → P(MEDIUM)，需补充探测后验证
     - 含 ❌ → 放弃该攻击路径
     - 含 ❓ → P(UNKNOWN)，需要先执行探测命令
- **输出**: 每个攻击假设的前置条件比对结果，格式：
  ```
  ATK-HYP-NNN（攻击名称）:
    前置条件"N": ✅/⚠️/❌/❓ 依据来源
    综合满足度：P(HIGH/MEDIUM/LOW/UNKNOWN)
    建议行动：直接验证/补充探测/放弃
  ```
- **示例**:
  ```
  ATK-HYP-001（docker.sock 逃逸）:
    前置条件"容器内可见 docker.sock": ✅ 侦察确认存在（recon_summary.md 中 docker.sock 挂载记录）
    前置条件"有读写权限": ⚠️ 权限未知，需 L1 探测
    综合满足度：P(MEDIUM)
    建议行动：补充 L1 探测 `ls -la /var/run/docker.sock`，确认后进入 Phase 4a

  ATK-HYP-002（hostPath 逃逸）:
    前置条件"Pod 挂载 hostPath 卷": ✅ 侦察确认（nodes/pods.json 中 hostPath 挂载记录）
    前置条件"挂载指向敏感路径": ✅ 挂载路径为 /etc（recon 确认）
    综合满足度：P(HIGH)
    建议行动：直接进入 Phase 4a 验证

  ATK-HYP-005（匿名 API 访问）:
    前置条件"API Server 匿名认证启用": ❌ 侦察显示 --anonymous-auth=false
    综合满足度：P(LOW)
    建议行动：放弃此攻击路径，转向 ATK-HYP-007（SA token 利用）

  ATK-HYP-009（云元数据窃取）:
    前置条件"容器可访问 169.254.169.254": ❓ 侦察未覆盖网络连通性
    前置条件"无 NetworkPolicy 阻断": ✅ 侦察确认命名空间无 NetworkPolicy
    综合满足度：P(UNKNOWN)
    建议行动：补充 L1 探测 `curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/`
  ```

---

## 交叉关联示例

以下示例展示三库联动在实际场景中的交叉查询过程。

### 示例 1：特权容器 + docker.sock + 无 Seccomp → socket-escape 逃逸确认

```
Phase 2 合规结果：
  K8s-7.1.1: FAIL（存在特权容器）
  Docker-42: FAIL（容器特权模式）
  Docker-44: FAIL（Seccomp unconfined）

XREF-001 映射：
  K8s-7.1.1 FAIL → CHK-CAND-001（特权容器→逃逸）✅ 命中
  Docker-42 FAIL → CHK-CAND-021（特权容器+无Seccomp）✅ 命中
  Docker-44 FAIL → CHK-CAND-034（无AppArmor/Seccomp）✅ 命中

XREF-002 叠加分析（目标 pod/app-server-7d9f8）：
  违规数：3
  叠加深度：3 → 风险放大
  叠加危险组合：特权容器(CHK-CAND-001) + docker.sock(CHK-CAND-002 需确认) + 无Seccomp(CHK-CAND-034)
  放大评级：🔴 CRITICAL
  触发 ATK-HYP：ATK-HYP-001 + ATK-HYP-004

XREF-003 侦察比对：
  ATK-HYP-001（docker.sock 逃逸）:
    前置条件"docker.sock 挂载": ❓ 侦察未确认 docker.sock 挂载
    → 补充 L1 探测: kubectl exec <pod> -- ls -la /var/run/docker.sock
  ATK-HYP-004（cgroup 逃逸）:
    前置条件"CAP_SYS_ADMIN": ✅ 特权容器默认拥有全部能力
    前置条件"cgroup 可写": ⚠️ 需 L1 确认
    → 补充 L1 探测: kubectl exec <pod> -- ls -la /sys/fs/cgroup/

最终行动：
  1. L1 探测 docker.sock 挂载状态
  2. L1 探测 cgroup 可写状态
  3. 基于探测结果确定进入 ATK-HYP-001 还是 ATK-HYP-004 验证
```

### 示例 2：RBAC 过宽 + 匿名访问 + 无 NetworkPolicy → 权限提升 + 横向移动

```
Phase 2 合规结果：
  K8s-1.2.1: FAIL（匿名认证启用）
  K8s-8.2.1: FAIL（cluster-admin 绑定过多）
  K8s-8.2.2: FAIL（通配符权限）
  K8s-8.2.10: FAIL（无 NetworkPolicy）

XREF-001 映射：
  K8s-1.2.1 FAIL → CHK-CAND-005（匿名访问）✅ 命中
  K8s-8.2.1 + K8s-8.2.2 FAIL → CHK-CAND-006（RBAC过宽）✅ 命中
  K8s-8.2.10 FAIL → CHK-CAND-008（无NetworkPolicy）✅ 命中

XREF-002 叠加分析：
  叠加危险组合：匿名访问(CHK-CAND-005) + RBAC过宽(CHK-CAND-006) + 无NetworkPolicy(CHK-CAND-008)
  叠加深度：3 → 风险放大
  放大评级：🔴 CRITICAL
  攻击链：匿名API → enumerate SA/RBAC → 横向移动
  触发 ATK-HYP：ATK-HYP-005 + ATK-HYP-006 + ATK-HYP-008

XREF-003 侦察比对：
  ATK-HYP-005（匿名API）:
    前置条件"匿名认证启用": ✅ --anonymous-auth=true 或默认值
    综合满足度：P(HIGH)
  ATK-HYP-006（RBAC提权）:
    前置条件"cluster-admin绑定过多": ✅ 侦察确认3个非系统cluster-admin绑定
    综合满足度：P(HIGH)
  ATK-HYP-008（横向移动）:
    前置条件"无NetworkPolicy": ✅ 多个命名空间无 NetworkPolicy
    综合满足度：P(HIGH)

最终行动：三个攻击假设均 HIGH，优先链式验证：
  Phase 4a: ATK-HYP-005 → ATK-HYP-006 → ATK-HYP-008
```

### 示例 3：SA token + 环境变量凭据 + 无资源限制 → 多维度攻击面

```
Phase 2 合规结果：
  K8s-7.1.14: FAIL（SA token 未禁用）
  K8s-8.2.5: FAIL（default SA token 仍挂载）
  K8s-8.2.9: FAIL（无 ResourceQuota）
  Docker-36: FAIL（无内存限制）

XREF-001 映射：
  K8s-7.1.14 + K8s-8.2.5 FAIL → CHK-CAND-007（SA token利用）✅ 命中
  K8s-8.2.9 FAIL → CHK-CAND-010（无资源限制）✅ 命中
  Docker-36 FAIL → CHK-CAND-022（无Docker资源限制）✅ 命中

XREF-002 叠加分析（目标 pod/app-worker-5f3b2）：
  叠加深度：3 → 风险放大
  放大评级：🟠 HIGH
  攻击组合：SA token利用 + 环境变据窃取 + DoS
  触发 ATK-HYP：ATK-HYP-007 + ATK-HYP-012 + ATK-HYP-013

XREF-003 侦察比对：
  ATK-HYP-007（SA token利用）:
    前置条件"default SA 仍挂载 token": ✅ 侦察确认多个 Pod automountServiceAccountToken 未设 false
    前置条件"SA 权限过宽": ⚠️ 需 L0 探测 auth can-i
  ATK-HYP-012（环境变量凭据）:
    前置条件"环境变量含凭据": ❓ 侦察未覆盖容器内部环境变量
    → 需 L1 探测
  ATK-HYP-013（资源滥用DoS）:
    前置条件"无资源限制": ✅ 侦察确认 Pod 无 limits
    综合满足度：P(HIGH)
```

### 示例 4：hostPath + hostPID → 文件系统逃逸 + 进程注入

```
Phase 2 合规结果：
  K8s-7.1.2: FAIL（hostPath 挂载）
  K8s-7.1.3: FAIL（hostPID=true）
  K8s-7.1.5: FAIL（hostNetwork=true）

XREF-001 映射：
  K8s-7.1.2 FAIL → CHK-CAND-003（hostPath逃逸）✅ 命中
  K8s-7.1.3 FAIL → CHK-CAND-019（共享PID命名空间）✅ 命中
  K8s-7.1.5 FAIL → CHK-CAND-024（hostNetwork逃逸）✅ 命中

XREF-002 叠加分析（目标 node-monitoring-daemonset）：
  违规数：3
  叠加深度：3 → 风险放大
  叠加危险组合：hostPath(CHK-CAND-003) + hostPID(CHK-CAND-019) + hostNetwork(CHK-CAND-024)
  放大评级：🔴 CRITICAL
  触发 ATK-HYP：ATK-HYP-002 + ATK-HYP-025 + ATK-HYP-008

XREF-003 侦察比对：
  ATK-HYP-002（hostPath逃逸）:
    前置条件"hostPath挂载敏感路径": ✅ 侦察确认挂载 /var/log 和 /etc
    综合满足度：P(HIGH)
  ATK-HYP-025（进程注入）:
    前置条件"hostPID=true": ✅ 合规确认
    综合满足度：P(HIGH)
```

### 示例 5：Docker 特权 + 无 AppArmor + 无 Seccomp → 全逃逸

```
Phase 2 合规结果（Docker 主机扫描）：
  Docker-42: FAIL（特权容器运行）
  Docker-34: FAIL（AppArmor unconfined）
  Docker-44: FAIL（Seccomp unconfined）
  Docker-39: FAIL（host 网络模式）

XREF-001 映射：
  Docker-42 FAIL → CHK-CAND-021（特权容器+无Seccomp）✅ 命中
  Docker-34 + Docker-44 FAIL → CHK-CAND-034（无AppArmor/Seccomp）✅ 命中
  Docker-39 FAIL → CHK-CAND-024（host网络模式）✅ 命中

XREF-002 叠加分析（目标 container/web-app）：
  叠加深度：4 → 严重放大
  叠加危险组合：特权容器 + 无AppArmor + 无Seccomp + host网络
  放大评级：🔴 CRITICAL
  触发 ATK-HYP：ATK-HYP-003 + ATK-HYP-004 + ATK-HYP-001

XREF-003 侦察比对：
  ATK-HYP-001（docker.sock逃逸）:
    前置条件"特权容器": ✅ Docker inspect 确认 Privileged=true
    前置条件"docker.sock 可访问": ⚠️ 需确认
  ATK-HYP-004（cgroup逃逸）:
    前置条件"CAP_SYS_ADMIN": ✅ 特权容器默认拥有
    前置条件"cgroup可写": ✅ 无Seccomp/AppMailer限制
    综合满足度：P(HIGH)
```

### 示例 6：云元数据 + 无 NetworkPolicy + 环境变量凭据

```
Phase 2 合规结果：
  K8s-8.2.10: FAIL（无 NetworkPolicy）
  CHK-CAND-027: 云元数据可访问（侦察确认）

XREF-001 映射：
  K8s-8.2.10 FAIL → CHK-CAND-008（无NetworkPolicy）✅ 命中
  CHK-CAND-027 → CHK-CAND-027（云元数据）✅ 命中

XREF-002 叠加分析（目标 pod/cloud-app-xyz）：
  叠加危险组合：无NetworkPolicy + 云元数据可访问
  放大评级：🟠 HIGH
  攻击链：curl 元数据 → 获取 IAM 凭据 → 访问云资源

XREF-003 侦察比对：
  ATK-HYP-009（云元数据窃取）:
    前置条件"可访问169.254.169.254": ✅ curl 返回 200（侦察确认）
    前置条件"返回IAM凭证": ⚠️ 需 L1 探测具体路径
  ATK-HYP-008（横向移动）:
    前置条件"无NetworkPolicy": ✅ 合规确认
    综合满足度：P(HIGH)
```

### 示例 7：Webhook 后门 + CronJob 持久化

```
Phase 2 合规结果：
  K8s-1.2.x: WARN（准入插件配置未审计）
  K8s-8.2.2: FAIL（ClusterRole 通配符权限）
  K8s-8.2.6: FAIL（SA 权限过宽）

XREF-001 映射：
  K8s-1.2.x WARN → CHK-CAND-017（Webhook未限制）✅ 命中
  K8s-8.2.2 + K8s-8.2.6 FAIL → CHK-CAND-018（CronJob可创建）✅ 命中

XREF-002 叠加分析：
  攻击组合：Webhook后门 + CronJob持久化 = 双重持久化路径
  放大评级：🟠 HIGH
  触发 ATK-HYP：ATK-HYP-017 + ATK-HYP-018

XREF-003 侦察比对：
  ATK-HYP-017（Webhook后门）:
    前置条件"可创建Webhook": ⚠️ 需 auth can-i 确认
  ATK-HYP-018（CronJob持久化）:
    前置条件"可创建CronJob": ⚠️ 需 auth can-i 确认
  → 补充 L0 探测: kubectl auth can-i create mutatingwebhookconfigurations
  → 补充 L0 探测: kubectl auth can-i create cronjobs
```

### 示例 8：无 PSA + 最新标签 + 无签名验证 → 供应链攻击面

```
Phase 2 合规结果：
  K8s-7.1.13: FAIL（PSA 未 enforce restricted）
  Docker-51: FAIL（DOCKER_CONTENT_TRUST 未启用）

XREF-001 映射：
  K8s-7.1.13 FAIL → CHK-CAND-020（无PSA）✅ 命中
  Docker-51 FAIL → CHK-CAND-012（无镜像签名验证）✅ 命中

XREF-002 叠加分析：
  攻击组合：Pod安全缺失 + 镜像签名缺失 = 供应链攻击面
  叠加深度：2（无放大，但攻击面互补）
  放大评级：🟡 MEDIUM
  触发 ATK-HYP：ATK-HYP-015 + ATK-HYP-016

XREF-003 侦察比对：
  ATK-HYP-015（镜像标签篡改）:
    前置条件"使用latest标签": ❓ 侦察未覆盖镜像标签审计
    → 补充 L0 探测
  ATK-HYP-016（仓库投毒）:
    前置条件"仓库无认证": ❓ 侦察未覆盖仓库认证
    → 补充 L0 探测: curl -s https://<registry>/v2/_catalog
```