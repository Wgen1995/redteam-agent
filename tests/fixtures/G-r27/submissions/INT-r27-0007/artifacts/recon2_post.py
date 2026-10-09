#!/usr/bin/env python3
# INT-r27-0007 脚本2：POST 形探测（urlencoded t=1 与 JSON {"t":1} 各一发，不带凭据猜测，不发攻击载荷）
import json, time
import urllib.request, urllib.error

BASE = "http://svc-dashboard:8006"
DELAY = 0.22
TIMEOUT = 5

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

KEY_HEADERS = ["Server", "Content-Type", "Location", "WWW-Authenticate",
               "Set-Cookie", "Allow", "Content-Length", "Access-Control-Allow-Origin"]

# 委派单指定的 9 条 + 已发现 4 面的行为差异
PATHS = ["/login", "/register", "/token", "/upload", "/import", "/xml",
         "/fetch", "/search", "/comment",
         "/render", "/report", "/ping", "/admin/config"]

def post(path, mode):
    url = BASE + path
    if mode == "form":
        data = b"t=1"
        ctype = "application/x-www-form-urlencoded"
    else:
        data = json.dumps({"t": 1}).encode()
        ctype = "application/json"
    rec = {"path": path, "mode": mode}
    try:
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={"User-Agent": "recon/0.1",
                                              "Content-Type": ctype})
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
    out = {"ts": "2026-10-23T15:30:00Z", "base": BASE, "results": []}
    for p in PATHS:
        for mode in ("form", "json"):
            out["results"].append(post(p, mode))
            time.sleep(DELAY)
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
