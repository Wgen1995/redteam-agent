#!/usr/bin/env python3
# INT-r27-0004 script2: POST shape probing on svc-admin:8003 (no creds, no payloads, marker t=1 only)
import urllib.request, urllib.error, time, json

BASE = "http://svc-admin:8003"
UA = "Mozilla/5.0 (compatible; recon/1.0)"
PATHS = ["/login", "/register", "/token", "/upload", "/import", "/xml", "/fetch", "/search", "/comment", "/zzz-control-nonexistent"]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

def post(path, body, ctype):
    rec = {"path": path, "ctype": ctype}
    req = urllib.request.Request(BASE + path, data=body, method="POST",
                                 headers={"User-Agent": UA, "Content-Type": ctype})
    try:
        r = opener.open(req, timeout=5)
        b = r.read(4096).decode("utf-8", "replace")
        rec["status"] = r.status
        rec["headers"] = {k: v for k, v in r.headers.items()
                          if k in ("Content-Type", "Content-Length", "Location", "WWW-Authenticate", "Allow", "Set-Cookie")}
        rec["body_head"] = b[:400]
    except urllib.error.HTTPError as e:
        b = ""
        try:
            b = e.read(4096).decode("utf-8", "replace")
        except Exception:
            pass
        rec["status"] = e.code
        rec["headers"] = {k: v for k, v in e.headers.items()
                          if k in ("Content-Type", "Content-Length", "Location", "WWW-Authenticate", "Allow", "Set-Cookie")} if e.headers else {}
        rec["body_head"] = b[:400]
    except Exception as e:
        rec["status"] = None
        rec["error"] = repr(e)
    return rec

FORM = ("t=1", "application/x-www-form-urlencoded")
JS = (json.dumps({"t": 1}), "application/json")
for p in PATHS:
    for body, ct in (FORM, JS):
        rec = post(p, body.encode(), ct)
        print(json.dumps(rec, ensure_ascii=False))
        time.sleep(0.25)
print("DONE")
