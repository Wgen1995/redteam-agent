#!/usr/bin/env python3
# INT-r27-0005 script0: DNS resolve svc-login + HTTP GET / on 8001-8008 (no redirect, timeout 5s, interval 0.2s)
import socket, urllib.request, urllib.error, time, json

HOST = "svc-login"
UA = "Mozilla/5.0 (compatible; recon/1.0)"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

out = {"host": HOST}
try:
    infos = socket.getaddrinfo(HOST, None)
    out["dns"] = {"resolved": True, "addrs": sorted({i[4][0] for i in infos})}
except Exception as e:
    out["dns"] = {"resolved": False, "error": repr(e)}
print(json.dumps({"dns": out["dns"]}, ensure_ascii=False), flush=True)

out["ports"] = []
for port in range(8001, 8009):
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
        rec["error"] = "%s: %s" % (type(e).__name__, e)
    out["ports"].append(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    time.sleep(0.2)

live = [p["port"] for p in out["ports"] if "status" in p]
print(json.dumps({"summary": "probe-done", "live_ports": live}, ensure_ascii=False), flush=True)
