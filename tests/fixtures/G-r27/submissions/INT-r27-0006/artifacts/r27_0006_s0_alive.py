#!/usr/bin/env python3
# INT-r27-0006 s0: DNS resolve svc-billing + HTTP GET / liveness on 8001-8008
# no redirect follow, timeout 5s, >=0.2s interval
import socket, json, time, urllib.request, urllib.error

KEEP_HDR = ("server", "content-type", "location", "www-authenticate",
            "allow", "x-powered-by", "access-control-allow-origin")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def http_get(url, timeout=5):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (recon)"})
    opener = urllib.request.build_opener(NoRedirect)
    try:
        r = opener.open(req, timeout=timeout)
        hdrs = {k: v for k, v in r.headers.items() if k.lower() in KEEP_HDR}
        cookies = [c.split("=")[0].strip() for c in (r.headers.get_all("Set-Cookie") or [])]
        return {"status": r.status, "headers": hdrs, "set_cookie_names": cookies,
                "body400": r.read(400).decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        hdrs = {k: v for k, v in e.headers.items() if k.lower() in KEEP_HDR}
        cookies = [c.split("=")[0].strip() for c in (e.headers.get_all("Set-Cookie") or [])]
        return {"status": e.code, "headers": hdrs, "set_cookie_names": cookies,
                "body400": e.read(400).decode("utf-8", "replace")}
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, e)}

out = {"dns": {}, "ports": []}
try:
    infos = socket.getaddrinfo("svc-billing", None, socket.AF_INET)
    out["dns"]["svc-billing"] = sorted(set(i[4][0] for i in infos))
except Exception as e:
    out["dns"]["svc-billing"] = "ERROR %s: %s" % (type(e).__name__, e)

for port in range(8001, 8009):
    ent = {"port": port}
    try:
        s = socket.create_connection(("svc-billing", port), timeout=3)
        s.close()
        ent["tcp"] = "open"
    except Exception as e:
        ent["tcp"] = "closed(%s)" % type(e).__name__
        out["ports"].append(ent)
        time.sleep(0.2)
        continue
    ent["http_get_root"] = http_get("http://svc-billing:%d/" % port)
    out["ports"].append(ent)
    time.sleep(0.2)

print(json.dumps(out, ensure_ascii=False, indent=1))
