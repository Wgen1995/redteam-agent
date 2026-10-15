# -*- coding: utf-8 -*-
"""webui server（v0.9a T3）——tanyin-web 只读观察面 HTTP 路由。

法律（docs/design/tanyin-target-form.md §3）：纯 stdlib、ThreadingHTTPServer 线程模型、
禁 asyncio；观察面只读投影（零写入账本）。路由（v0.9a 三分支 + v0.9b 三页）：
  GET /                 → static/index.html（手写仪表盘）
  GET /api/state.json   → snapshot 快照 JSON
  GET /api/stream       → SSE timeline 追尾流（?tail=N 覆盖存量尾条数）
  GET /coverage|/graph|/evidence            → v0.9b 观察面三页（静态）
  GET /api/matrix|graph|evidence.json       → v0.9b 三只读投影（projections 单源）
  GET /metrics                               → v0.9c 度量页（静态：双臂召回曲线）
  GET /api/metrics.json                      → v0.9c 双臂战例度量（metrics 单源）
启动：cd cli && python -m webui.server --ledger-dir D（T5 接 CLI 入口）。
"""
import json, os, socket, sys, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_CLI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CLI_DIR not in sys.path:                     # -m/直跑兜底：cli/ 上 path 才有 ledger
    sys.path.insert(0, _CLI_DIR)
# 法律：服务端 import 只来自 stdlib + ledger（本模块只读投影，零账本写入）

from . import snapshot as _snap  # noqa: E402
from . import sse as _sse        # noqa: E402
from . import projections as _proj  # noqa: E402  (v0.9b 三页只读装配)
from . import metrics as _met  # noqa: E402  (v0.9c 度量页只读装配)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DEFAULT_HOST, DEFAULT_PORT, DEFAULT_TAIL = "127.0.0.1", 8900, 50
POLL_S, KEEPALIVE_S = _sse.DEFAULT_POLL_S, _sse.DEFAULT_KEEPALIVE_S
_PAGE_API = {"/api/matrix.json": _proj.matrix_view,     # v0.9b 三页 API（只读装配单源）
             "/api/graph.json": _proj.graph_view,
             "/api/evidence.json": _proj.evidence_view,
             "/api/metrics.json": (lambda ledger_dir: _met.metrics_view())}  # v0.9c（battles 装配与 ledger 无涉）


class Handler(BaseHTTPRequestHandler):
    server_version = "tanyin-web/0.9c"
    protocol_version = "HTTP/1.1"
    timeout = 60                                  # 空闲 keep-alive 连接回收（SSE 写循环不受影响）

    def log_message(self, fmt, *args):           # 静默（长连接轮询会刷屏；env 开话痨）
        if os.environ.get("TANYIN_WEBUI_DEBUG"):
            sys.stderr.write("[webui] %s\n" % (fmt % args))

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            return self._serve_page("index.html")
        if u.path in ("/coverage", "/graph", "/evidence",
                      "/metrics"):                                 # v0.9b 三页+v0.9c 度量页
            return self._serve_page(u.path.lstrip("/") + ".html")
        if u.path in _PAGE_API:                                    # 页 API 单源表（v0.9b+v0.9c）
            return self._serve_json(_PAGE_API[u.path](self.server.ledger_dir))
        if u.path == "/api/state.json":
            return self._serve_state()
        if u.path == "/api/stream":
            return self._serve_stream(u)
        self._send(404, "text/plain; charset=utf-8", b"404 not found\n")

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _serve_page(self, name):
        try:
            with open(os.path.join(STATIC_DIR, name), "rb") as f:
                body = f.read()
        except OSError:
            return self._send(500, "text/plain; charset=utf-8",
                              name.encode("ascii", "ignore") + b" missing\n")
        self._send(200, "text/html; charset=utf-8", body)

    def _serve_json(self, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(200, "application/json", data)

    def _serve_state(self):
        self._serve_json(_snap.snapshot(self.server.ledger_dir, tail=self.server.tail))

    def _serve_stream(self, u):
        q = urllib.parse.parse_qs(u.query)
        tail = self.server.tail
        if "tail" in q and q["tail"][0].isdigit():
            tail = int(q["tail"][0])
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")     # 代理禁缓冲（SSE 直通）
        self.send_header("Connection", "close")         # 无限流无长度：帧后即断语义
        self.end_headers()
        self.close_connection = True
        path = os.path.join(self.server.ledger_dir, "timeline.tsv")
        try:
            for fr in _sse.events(path, start_tail=tail,
                                  poll_interval=self.server.poll_s,
                                  keepalive_s=self.server.keepalive_s,
                                  stop=lambda: self.server.stopping):
                self.wfile.write(fr.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError,
                socket.timeout, OSError):
            pass    # 客户端断开即收尾（写失败=断连的唯一直通信号）


class WebServer(ThreadingHTTPServer):
    daemon_threads = True                          # SSE 长连接随进程收尾

    def __init__(self, addr, handler, ledger_dir=".", tail=DEFAULT_TAIL,
                 poll_s=POLL_S, keepalive_s=KEEPALIVE_S):
        super().__init__(addr, handler)
        self.ledger_dir = ledger_dir
        self.tail = tail
        self.poll_s = poll_s
        self.keepalive_s = keepalive_s
        self.stopping = False                      # SSE 轮询停机旗

    def handle_error(self, request, client_address):
        """默认静默：客户端未礼别断开（读请求行 ConnectionReset）是浏览器常态噪音；
        TANYIN_WEBUI_DEBUG=1 时走默认回溯打印（排障）。"""
        if os.environ.get("TANYIN_WEBUI_DEBUG"):
            super().handle_error(request, client_address)


def make_server(host=DEFAULT_HOST, port=0, ledger_dir=".", tail=DEFAULT_TAIL,
                poll_s=POLL_S, keepalive_s=KEEPALIVE_S):
    """造服务器（port=0=临时端口，server_address[1] 取实际口）。"""
    return WebServer((host, port), Handler, ledger_dir, tail, poll_s, keepalive_s)


USAGE = ("用法: python -m webui.server --ledger-dir D [--host H] [--port N] "
         "[--tail N] [--help]")


def parse_args(argv):
    """--k=v 与 --k v 双形态归一（tanyin-viz _kv 同款）；--help/-h 裸旗标。
    返回 {ledger_dir,host,port,tail[,help][,error]}；用法错置 error 键（中文理由）。"""
    out = {"ledger_dir": "", "host": DEFAULT_HOST,
           "port": DEFAULT_PORT, "tail": DEFAULT_TAIL}
    kv, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a in ("--help", "-h"):
            out["help"] = True
            i += 1
            continue
        if not a.startswith("--"):
            out["error"] = "未知参数: " + a
            return out
        if "=" in a:
            kv[a.split("=", 1)[0]] = a.partition("=")[2]   # 键归一：剥 =值 尾
            i += 1
        elif i + 1 < len(argv):
            kv[a] = argv[i + 1]
            i += 2
        else:
            kv[a] = ""
            i += 1
    out["ledger_dir"] = kv.pop("--ledger-dir", "")
    for flag, key in (("--host", "host"), ("--port", "port"), ("--tail", "tail")):
        if flag in kv:
            out[key] = kv.pop(flag)
    if kv:
        out["error"] = "未知旗标: " + ",".join(sorted(kv))
        return out
    try:
        out["port"] = int(out["port"])
        out["tail"] = int(out["tail"])
    except ValueError:
        out["error"] = "--port/--tail 须整数"
        return out
    if not out["ledger_dir"] and "help" not in out:
        out["error"] = "缺 --ledger-dir"
    return out


def main(argv):
    from ledger.runtime import bootstrap   # v0.7a 装配单源（path 垫片+utf8 stdio）
    bootstrap(__file__)
    kv = parse_args(argv[1:])
    if kv.get("help"):
        print(USAGE)
        return 0
    if kv.get("error"):
        sys.stderr.write(kv["error"] + chr(10) + USAGE + chr(10))
        return 2
    gd = kv["ledger_dir"]
    if not os.path.isdir(gd):
        sys.stderr.write("环境问题: ledger 目录不存在 " + gd + chr(10))
        return 2
    srv = make_server(kv["host"], kv["port"], gd, tail=kv["tail"])
    port = srv.server_address[1]
    print("tanyin-web v0.9c 只读观察面: %s:%d/ ledger=%s tail=%d"
          % (kv["host"], port, gd, kv["tail"]))
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.stopping = True
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
