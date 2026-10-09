#!/usr/bin/env python3
# INT-r27-0004 script0: DNS resolve svc-admin + HTTP GET / on 8001-8008 (no redirect, timeout 5s)
import socket, urllib.request, urllib.error, time, json

HOST = "svc-admin"
PORTS = list(range(8001, 8009))
UA = "Mozilla/5.0 (compatible; recon/1.0)"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

def resolve():
    out = {"host": HOST}
    try:
        infos = socket.getaddrinfo(HOST, None)
        out["resolved"] = True
        out["addrs"] = sorted({i[4][0] for i in infos})
    except Exception as e:
        out["resolved"] = False
        out["error"] = repr(e)
    return out

def probe(port):
    url = "http://%s:%d/" % (HOST, port)
    rec = {"port": port, "url": url}
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": UA})
    try:
        r = opener.open(req, timeout=5)
        body = r.read(4096)
        rec["status"] = r.status
        rec["headers"] = {k: v for k, v in r.headers.items()}
        rec["body_head"] = body[:400].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        rec["status"] = e.code
        rec["headers"] = {k: v for k, v in e.headers.items()} if e.headers else {}
        try:
            rec["body_head"] = e.read(400).decode("utf-8", "replace")
        except Exception:
            rec["body_head"] = ""
    except Exception as e:
        rec["status"] = None
        rec["error"] = repr(e)
    return rec

result = {"dns": resolve(), "ports": []}
print("DNS " + json.dumps(result["dns"], ensure_ascii=False))
for p in PORTS:
    r = probe(p)
    result["ports"].append(r)
    print("PORT " + json.dumps(r, ensure_ascii=False))
    time.sleep(0.25)
print("DONE")
