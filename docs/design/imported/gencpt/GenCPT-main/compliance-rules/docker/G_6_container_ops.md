# G_6 Docker 容器运维（2 条）

CIS Docker Benchmark v1.6.0 — 5 Container Runtime 部分（运维相关）。
覆盖 Docker-60 至 Docker-61，共 2 条规则。

---

### Docker-60 容器健康状态

**检查命令 [L0]**:
```bash
ssh_execute(server, "docker ps --filter 'health=unhealthy' --format '{{.ID}} {{.Names}} {{.Status}}' 2>/dev/null; echo '---'; docker ps -a --filter 'health=starting' --format '{{.ID}} {{.Names}} {{.Status}}' 2>/dev/null")
```

进一步检查所有容器健康状态：
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): health=$(docker inspect --format '{{.State.Health.Status}}' \"$c\" 2>/dev/null || echo 'no healthcheck')\"; done")
```

**期望值**: 所有运行中容器健康状态为 `healthy`
**判定标准**: pass=所有容器 healthy，fail=存在 unhealthy 或 starting 状态的容器，na=容器无 HEALTHCHECK 配置
**修复建议**: 为所有镜像添加 HEALTHCHECK 并监控：
```bash
# 检查不健康容器
docker ps --filter 'health=unhealthy'

# 重启不健康容器
docker restart <container_id>

# 查看健康检查日志
docker inspect --format '{{.State.Health.Log}}' <container_id>
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.19 "Ensure that containers are healthy"（运维最佳实践）
**攻击面关联**: AS-5 可用性（不健康容器可能是被攻陷或资源耗尽的标志，需要及时响应）

---

### Docker-61 容器资源使用监控

**检查命令 [L0]**:
```bash
ssh_execute(server, "docker stats --no-stream --format '{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}' 2>/dev/null")
```

进一步检查各容器资源限制和使用情况：
```bash
ssh_execute(server, "for c in $(docker ps -q); do echo \"$(docker inspect --format '{{.Name}}' \"$c\"): mem_limit=$(docker inspect --format '{{.HostConfig.Memory}}' \"$c\" 2>/dev/null), cpu_shares=$(docker inspect --format '{{.HostConfig.CpuShares}}' \"$c\" 2>/dev/null)\"; done")
```

**期望值**: 所有容器的 CPU 和内存使用率在合理范围内（< 80% 限制值）
**判定标准**: pass=所有容器资源使用在限制范围内，fail=存在资源使用超限或无限制使用的容器，na=无运行中容器
**修复建议**: 为所有容器设置资源限制并配置监控：
```bash
# 设置资源限制
docker run --memory=512m --cpu-shares=512 myapp

# 配置 Docker 日志驱动收集指标
docker run --log-driver=json-file --log-opt max-size=10m myapp
```
**CIS映射**: CIS Docker Benchmark v1.6.0 - 5.20 "Ensure that container resource usage is monitored"（运维最佳实践）
**攻击面关联**: AS-4 资源耗尽（无资源监控时容器异常使用可能被忽视，影响安全事件响应）