#!/usr/bin/env python3
# INT-r27-0006 s3: baseline + method fingerprint (no payloads, no cred guessing)
# - nonexistent path GET/POST/OPTIONS vs known probes (path-blindness baseline)
# - OPTIONS/HEAD method fingerprint on / and /login
import json, time, urllib.request, urllib.error

PORT = 8005
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def req(method, path, data=None, ctype=None):
    hdrs = {"User-Agent": "Mozilla/5.0 (recon)"}
    if ctype: hdrs["Content-Type"] = ctype
    r = urllib.request.Request("http://svc-billing:%d%s" % (PORT, path),
                               data=data, method=method, headers=hdrs)
    opener = urllib.request.build_opener(NoRedirect)
    try:
        resp = opener.open(r, timeout=5)
        return {"method": method, "path": path, "status": resp.status,
                "allow": resp.headers.get("Allow"), "server": resp.headers.get("Server"),
                "ct": resp.headers.get("Content-Type"),
                "body400": resp.read(400).decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        return {"method": method, "path": path, "status": e.code,
                "allow": e.headers.get("Allow"), "server": e.headers.get("Server"),
                "ct": e.headers.get("Content-Type"),
                "body400": e.read(400).decode("utf-8", "replace")}
    except Exception as e:
        return {"method": method, "path": path, "error": "%s: %s" % (type(e).__name__, e)}

NX = "/zzz-r27-nx-baseline"
probes = [
    ("GET", NX, None, None),
    ("POST", NX, b"t=1", "application/x-www-form-urlencoded"),
    ("POST", NX, b'{"t":1}', "application/json"),
    ("OPTIONS", NX, None, None),
    ("OPTIONS", "/", None, None),
    ("OPTIONS", "/login", None, None),
    ("HEAD", "/", None, None),
    ("HEAD", "/admin", None, None),
]
out = []
for m, p, d, c in probes:
    out.append(req(m, p, d, c))
    time.sleep(0.2)
print(json.dumps(out, ensure_ascii=False, indent=1))
