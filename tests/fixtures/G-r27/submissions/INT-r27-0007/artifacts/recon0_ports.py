#!/usr/bin/env python3
# INT-r27-0007 脚本0：DNS 解析 svc-dashboard + 8001-8008 逐端口 HTTP GET / 探活
# 铁律：禁跟随重定向；timeout 5s；请求间隔 >=0.2s；只做发现不发攻击载荷
import socket, json, time, sys
import urllib.request, urllib.error

HOST = "svc-dashboard"
PORTS = list(range(8001, 8009))
DELAY = 0.25
TIMEOUT = 5

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

KEY_HEADERS = ["Server", "X-Powered-By", "Content-Type", "Location",
               "WWW-Authenticate", "Set-Cookie", "X-Frame-Options",
               "Access-Control-Allow-Origin", "Allow", "Content-Length"]

def dns_info():
    out = {}
    for fn, name in ((socket.gethostbyname_ex, "gethostbyname_ex"),
                     (socket.getaddrinfo, "getaddrinfo")):
        try:
            if name == "gethostbyname_ex":
                out[name] = fn(HOST)
            else:
                infos = fn(HOST, None)
                out[name] = sorted({i[4][0] for i in infos})
        except Exception as e:
            out[name] = "ERR: %r" % e
    return out

def probe(port):
    url = "http://%s:%d/" % (HOST, port)
    rec = {"url": url}
    try:
        req = urllib.request.Request(url, method="GET",
                                     headers={"User-Agent": "recon/0.1"})
        resp = opener.open(req, timeout=TIMEOUT)
        rec["status"] = resp.status
        rec["headers"] = {k: v for k, v in resp.getheaders() if k in KEY_HEADERS}
        body = resp.read(65536).decode("utf-8", "replace")
        rec["body_head"] = body[:400]
        rec["body_len"] = len(body)
    except urllib.error.HTTPError as e:
        rec["status"] = e.code
        rec["headers"] = {k: v for k, v in e.headers.items() if k in KEY_HEADERS}
        try:
            body = e.read(65536).decode("utf-8", "replace")
        except Exception:
            body = ""
        rec["body_head"] = body[:400]
        rec["body_len"] = len(body)
    except Exception as e:
        rec["status"] = None
        rec["error"] = "%s: %s" % (type(e).__name__, e)
    return rec

def main():
    result = {"ts": "2026-10-23T15:30:00Z", "host": HOST, "dns": dns_info(), "ports": []}
    for p in PORTS:
        rec = probe(p)
        rec["port"] = p
        result["ports"].append(rec)
        time.sleep(DELAY)
    print(json.dumps(result, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
