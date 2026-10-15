# -*- coding: utf-8 -*-
"""SEC-2 舰 S2（v0.9.6 执法面升权批）：Tier3 egress 实挂——runner 内嵌代理 +
子进程 env 强制 + request-ticket 机械记账（覆盖率 0%→机械强制）。

评审依据：docs/reviews/2026-10-15-direction-review/02-security-enforcement.md
S2 节（「Tier3 egress 代理全仓唯一消费者是 tests/」）+ 计划档 SEC-2 舰条目 4。

【安装/自检步骤（RUNBOOK；不动 ZhuLong——8900 常驻服务不在本舰作业面）】
 1. python3 cli/tanyin-egress compile --goal-dir <D> --timestamp=<ISO8601>
    # scope.tsv 生效链 -> egress.acl（执法策略源=账本，deny-by-default）
 2. python3 cli/tanyin-egress selfcheck --acl <D>/egress.acl
    # ACL 可解析 + 代理可起停自检（rc 0/2）
 3. python3 cli/tanyin-runner start ... --ledger-dir <D> ...
    # runner 自动内嵌起 EgressProxy（127.0.0.1 随机端口）并强制子进程 env
    #   HTTP_PROXY/HTTPS_PROXY/NO_PROXY——战士进程零配合、零感知；
    #   egress.acl 缺失=不挂载并如实记 EGRESS-MOUNT off（披露非静默）；
    #   ACL 损坏=fail-closed 拒启动（ValueError 上抛，runner exit 2）。
 4. 战斗期间 runner 每 tick 轮询 egress-log.jsonl 增量，逐笔判决自动铸
    request-ticket 入 timeline（actor=egress——机械记账不经战士手）。
 5. 战毕 runner 退出时代理随战斗生命周期 shutdown（无常驻进程纪律合规）。

【机械性与边界（如实披露）】
- env 注入在 spawn 侧：curl/httpx/urllib 等 HTTP(S) 外联工具天然吃代理 env，
  判定走 egress_proxy.decide 四态（deny/canary/oob/allow）；
- docker exec 等 非 HTTP 通道不在 env 代理捕获面——argv 级拦截属 Tier2
  opencode plugin（评审 S2 修正方向第一序，不在本舰白名单，另批收口）；
- 代理本体绝不写 13 表（单写者纪律）——记账由本模块（runner 侧监督者）
  经 ledger.timeline.append_tl_locked（goal 锁包链）落账。"""
import json
import os
import threading

from . import egress_proxy
from .timeline import append_tl_locked

# loopback 豁免清单：代理自身监听 127.0.0.1，代理 loopback 会自环；
# localhost 业务（mock/本机服务）不走代理。
NO_PROXY_DEFAULT = "localhost,127.0.0.1,::1"


def proxy_env(port, no_proxy=NO_PROXY_DEFAULT):
    """强制子进程 env（大小写双写——curl 认小写、部分工具认大写）。"""
    url = "http://127.0.0.1:%d/" % port
    return {"HTTP_PROXY": url, "HTTPS_PROXY": url,
            "http_proxy": url, "https_proxy": url,
            "NO_PROXY": no_proxy, "no_proxy": no_proxy}


def ticket_event(row):
    """egress-log 行 -> request-ticket 事件词（机械记账口径，与 guard
    request-ticket 同事件族——流量画像可从账本重建）。"""
    return "request-ticket egress verdict=%s kind=%s host=%s port=%s" % (
        row.get("verdict"), row.get("kind"), row.get("host"), row.get("port"))


class Mount:
    """一次战斗的代理挂载句柄：serve 线程 + env 工厂 + 增量记账 + 生命周期关停。"""

    def __init__(self, proxy, egress_log):
        self.proxy = proxy
        self.egress_log = egress_log
        self._offset = self._filesize(egress_log)   # 挂载前的存量不重复记账
        self._thread = threading.Thread(target=proxy.serve_forever, daemon=True)
        self._thread.start()

    @staticmethod
    def _filesize(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0

    @property
    def port(self):
        return self.proxy.server_address[1]

    def env(self, no_proxy=NO_PROXY_DEFAULT):
        """注入 launch() 的 env 增量（测试可覆写 no_proxy 以走代理打 mock）。"""
        return proxy_env(self.port, no_proxy)

    def poll_tickets(self, gd):
        """egress-log 增量行逐笔铸 timeline request-ticket（返回铸票数）。

        半行（并发写撕裂）与坏 JSON 跳过不炸——下轮 poll 从已读偏移续读；
        行缺 ts（不该发生）跳过（append_tl ts 必填纪律）。"""
        try:
            with open(self.egress_log, encoding="utf-8") as f:
                f.seek(self._offset)
                fresh = f.read()
                self._offset = f.tell()
        except OSError:
            return 0
        n = 0
        for ln in fresh.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                row = json.loads(ln)
            except ValueError:
                continue
            ts = row.get("ts") or ""
            if not ts:
                continue
            append_tl_locked(gd, ts, ticket_event(row), actor="egress", phase="P3")
            n += 1
        return n

    def shutdown(self):
        """随战斗生命周期关停（幂等；serve 线程 join 上限防悬挂）。"""
        try:
            self.proxy.shutdown()
            self.proxy.server_close()
        except OSError:
            pass
        if self._thread.is_alive():
            self._thread.join(timeout=5)


def mount(gd, port=0):
    """goal 目录 -> Mount（egress.acl 在场才挂载；缺=None；坏 ACL=ValueError
    fail-closed——由 runner 拒启动，不静默降级为零执法）。"""
    acl = os.path.join(gd, "egress.acl")
    if not os.path.isfile(acl):
        return None
    d = os.path.join(gd, "egress")
    os.makedirs(d, exist_ok=True)
    logp = os.path.join(d, "egress-log.jsonl")
    proxy = egress_proxy.serve(acl, port, egress_log=logp)   # ValueError 透传
    return Mount(proxy, logp)
