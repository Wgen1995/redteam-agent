# -*- coding: utf-8 -*-
"""Tier3 egress 代理本体（批次 6 T10；裁决 H——机械执法组件，铁律 7 合规）。

职责：egress.acl 加载 → HTTP 明文转发 + CONNECT 隧道按目标判定 → DNS pin 比对 →
OOB 回连落账 → canary 域触碰实时告警。性能非首批目标（G-41 披露：并发/吞吐上限
未测，机械执法非性能件）。

TLS 限制披露（裁决 H，守门声明）：CONNECT 按 CONNECT 目标主机名判定，代理不做
TLS 中间人、不解析 TLS 内容——隧道内行为不可见是架构边界而非能力缺口。

ACL 行约定（egress.acl v2 compile 真实产物为锚；计划行约定并存）：
  # 注释 / 空行 / 段头 [acl] [dns-pinning] [oob] [canary] [infra]
  default deny                     默认拒绝（现产物恒在）
  deny <spec>                      显式拒绝（exclude 展开；优先级最高）
  allow <host:port|host:*|host|*.suf|CIDR>   允许（计划行约定=host:port 精确/host:*）
  pin <host|*.suf>                 DNS pin 声明（无 ip 形态——比对=声明态 pin_ok=None）
  dns-pin <host> <ip>              DNS pin 带期望地址（计划行约定；地址级执法）
  oob <host> / allow-oob <host>    OOB 回连域（allow 后落 kind=oob 行）
  canary <host>                    canary 域（allow 后落 kind=canary 告警行；compile
                                   v2 不产出本段——canary 面随 T11 手工/扩展 ACL）
  其余任意行=ValueError（fail-closed）

DNS pin 执法语义（三态）：pin 无 ip=声明态（pin_ok=None）；host 为 IP 字面量且≠pin
期望=拒绝（pin_ok=False）；host 为域名且 pin 带 ip=直连 pin（解析面免疫，pin_ok=None，
如实披露不可比对）；host==pin=放行（pin_ok=True）。

运行时工件：仅 egress-log.jsonl（行={"ts","verdict","host","port","kind","pin_ok"}，
kind=forward|connect|oob|canary）——代理绝不写 13 表（单写者纪律）。"""
import ipaddress
import json
import os
import select
import socket
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

_SECTIONS = ("[acl]", "[dns-pinning]", "[oob]", "[canary]", "[infra]")
_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
        "proxy-connection", "te", "trailer", "transfer-encoding", "upgrade"}
_DEFAULT_PORT = "*"


def parse_acl(text):
    """egress.acl 文本 → 判定结构。未知行=ValueError（fail-closed）。"""
    acl = {"allow": set(), "deny": set(), "dns_pin": {}, "oob": set(),
           "canary": set(), "default_deny": False}
    section = None
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if ln in _SECTIONS:
            section = ln
            continue
        if ln == "default deny":
            acl["default_deny"] = True
            continue
        head, _, rest = ln.partition(" ")
        rest = rest.strip()
        if head == "allow" and section in (None, "[acl]"):
            acl["allow"].add(_spec(rest))
        elif head == "deny" and section in (None, "[acl]"):
            acl["deny"].add(_spec(rest))
        elif head == "pin" and section == "[dns-pinning]":
            acl["dns_pin"][rest] = None
        elif head == "dns-pin":
            parts = rest.split()
            if len(parts) != 2:
                raise ValueError("dns-pin 行须 <host> <ip>: %r" % ln)
            acl["dns_pin"][parts[0]] = parts[1]
        elif head == "oob" and section in (None, "[oob]"):
            acl["oob"].add(rest)
        elif head == "allow-oob" and section == "[oob]":
            acl["oob"].add(rest)
        elif head == "canary" and section in (None, "[canary]"):
            acl["canary"].add(rest)
        elif head == "allow-infra" and section == "[infra]":
            acl["allow"].add((rest, _DEFAULT_PORT))
        else:
            raise ValueError("egress.acl 未知行（fail-closed）: %r" % ln)
    return acl


def _spec(s):
    """allow/deny 规格归一：(host, port|int|"*")；CIDR 以 network 字符串为 host。"""
    host, _, port = s.partition(":")
    if not host:
        raise ValueError("allow/deny 规格缺 host: %r" % s)
    if port in ("", "*"):
        return (host, _DEFAULT_PORT)
    try:
        return (host, int(port))
    except ValueError:
        raise ValueError("allow/deny 端口须整数或 *: %r" % s)


def _ip_literal(host):
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def _match(entry_host, host):
    """host 匹配：精确 / 通配后缀（*.suf 严格不含裸域，apex 由独立行声明）/ CIDR。"""
    if entry_host == host:
        return True
    if entry_host.startswith("*.") and host.endswith("." + entry_host[2:]):
        return True
    if _ip_literal(host) is not None and "/" in entry_host:
        try:
            return _ip_literal(host) in ipaddress.ip_network(entry_host, strict=False)
        except ValueError:
            return False
    return False


def decide(acl, host, port):
    """判定单源：显式 deny 优先 → allow（精确/通配/CIDR）→ 其余一律 deny
    （deny-by-default 纪律：default_deny 标志在册即可读，判定结果恒收口 deny）。"""
    for dh, dp in acl["deny"]:
        if _match(dh, host) and dp in (_DEFAULT_PORT, port):
            return "deny"
    for ah, ap in acl["allow"]:
        if _match(ah, host) and ap in (_DEFAULT_PORT, port):
            return "allow"
    return "deny"


def _pin_for(acl, host):
    """host 的 pin 期望地址：精确 → 通配后缀；无= None。"""
    v = acl["dns_pin"].get(host)
    if v is not None or host in acl["dns_pin"]:
        return v
    for pat, val in acl["dns_pin"].items():
        if pat.startswith("*.") and host.endswith("." + pat[2:]):
            return val
    return None


def _wild_hit(entry_set, host):
    for e in entry_set:
        if _match(e, host):
            return True
    return False


class EgressProxy(ThreadingHTTPServer):
    """判执一体代理服务器：acl 判定+egress-log 追加（唯一运行时工件）。"""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, acl, egress_log=None, port=0, now="2026-09-24T00:00:00Z"):
        ThreadingHTTPServer.__init__(self, ("127.0.0.1", port), _Handler)
        self.acl = acl
        self.egress_log = egress_log
        self.now = now

    def log_line(self, kind, host, port, verdict, pin_ok=None):
        if not self.egress_log:
            return
        row = {"ts": self.now, "verdict": verdict, "host": host, "port": port,
               "kind": kind, "pin_ok": pin_ok}
        with open(self.egress_log, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # 运行时工件=egress-log；stderr 保持安静
        pass

    def do_GET(self):
        self._forward("GET")

    def do_POST(self):
        self._forward("POST")

    def do_HEAD(self):
        self._forward("HEAD")

    def do_PUT(self):
        self._forward("PUT")

    def do_DELETE(self):
        self._forward("DELETE")

    def do_OPTIONS(self):
        self._forward("OPTIONS")

    def _forward(self, method):
        u = urlsplit(self.path)
        host, port = u.hostname or "", u.port or 80
        acl = self.server.acl
        v = decide(acl, host, port)
        if v != "allow":
            self.server.log_line("forward", host, port, "deny")
            self.send_error(403)
            return
        pin = _pin_for(acl, host)
        pin_ok, target = None, host
        if pin is not None:
            ip = _ip_literal(host)
            if ip is not None:
                if str(ip) == pin:
                    pin_ok = True
                else:
                    # 解析目标≠pin 期望=拒绝（DNS rebinding/劫持执法面）
                    self.server.log_line("forward", host, port, "deny", pin_ok=False)
                    self.send_error(403)
                    return
            else:
                target = pin  # pin 直连：解析面免疫；名称 host 无可比地址（pin_ok=None）
        selector = u.path + (("?" + u.query) if u.query else "")
        try:
            conn = http.client.HTTPConnection(target, port, timeout=10)
            hdrs = {k: val for k, val in self.headers.items()
                    if k.lower() not in _HOP}
            body = None
            if "Content-Length" in self.headers:
                body = self.rfile.read(int(self.headers["Content-Length"]))
            conn.request(method, selector, body=body, headers=hdrs)
            r = conn.getresponse()
            data = r.read()
            conn.close()
        except (OSError, http.client.HTTPException):
            self.server.log_line("forward", host, port, "up-error", pin_ok)
            self.send_error(502)
            return
        # 落账先于响应写回：客户端收到响应字节时 egress-log 行已全部落盘
        # （触探/告警证据源对消费者无竞态——T11 probe 读 log 判定依赖此序）
        self.server.log_line("forward", host, port, "allow", pin_ok)
        if _wild_hit(acl["oob"], host):
            self.server.log_line("oob", host, port, "allow", pin_ok)
        if _wild_hit(acl["canary"], host):
            self.server.log_line("canary", host, port, "allow", pin_ok)
        self.send_response(r.status, r.reason)
        for k, val in r.getheaders():
            if k.lower() in _HOP or k.lower() == "content-length":
                continue
            self.send_header(k, val)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)
        self.close_connection = True

    def do_CONNECT(self):
        host, _, port_s = self.path.partition(":")
        host = host.strip()
        try:
            port = int(port_s or 443)
        except ValueError:
            self.send_error(400)
            return
        acl = self.server.acl
        v = decide(acl, host, port)
        pin = _pin_for(acl, host)
        pin_ok = None
        if v == "allow" and pin is not None:
            ip = _ip_literal(host)
            if ip is not None:
                if str(ip) == pin:
                    pin_ok = True
                else:
                    self.server.log_line("connect", host, port, "deny", pin_ok=False)
                    self.send_error(403)
                    return
        self.server.log_line("connect", host, port, v, pin_ok)
        if v != "allow":
            self.send_error(403)
            return
        target = pin if (pin is not None and _ip_literal(host) is None) else host
        self.send_response(200)
        self.end_headers()
        try:
            up = socket.create_connection((target, port), timeout=10)
        except OSError:
            self.close_connection = True
            return
        # TLS 不解密披露：双向字节中继（无中间人；CONNECT 目标主机名判定已在前）
        try:
            self._tunnel(up)
        finally:
            up.close()
        self.close_connection = True

    def _tunnel(self, up):
        socks = [self.connection, up]
        while True:
            r, _, x = select.select(socks, [], socks, 60)
            if x or not r:
                return
            for s in r:
                data = s.recv(65536)
                if not data:
                    return
                other = up if s is self.connection else self.connection
                other.sendall(data)


def serve_text(acl_text, port=0, egress_log=None, now="2026-09-24T00:00:00Z"):
    """文本入口（测试/程序内）。"""
    return EgressProxy(parse_acl(acl_text), egress_log=egress_log, port=port, now=now)


def serve(acl_path, port, egress_log=None, now="2026-09-24T00:00:00Z"):
    """文件入口：parse_acl(f.read()) → EgressProxy；调用方 serve_forever/shutdown。"""
    with open(acl_path, encoding="utf-8") as f:
        return serve_text(f.read(), port=port, egress_log=egress_log, now=now)
