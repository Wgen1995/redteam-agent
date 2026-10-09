#!/usr/bin/env python3
# INT-r27-0007 脚本2b：方法差分补充——OPTIONS（看 Allow）+ 空 body POST（区分 400 归因：body解析 vs 缺字段）
import json, time
import urllib.request, urllib.error

BASE = "http://svc-dashboard:8006"
DELAY = 0.22
TIMEOUT = 5

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)
KEY_HEADERS = ["Allow", "Content-Type", "Content-Length", "Set-Cookie", "Location", "WWW-Authenticate"]

PATHS = ["/login", "/register", "/token", "/upload", "/fetch", "/search",
         "/render", "/report", "/ping", "/admin/config"]

def req_raw(path, method, data=None, ctype=None):
    url = BASE + path
    rec = {"path": path, "method": method, "data": "empty" if data == b"" else (data or None)}
    h = {"User-Agent": "recon/0.1"}
    if ctype:
        h["Content-Type"] = ctype
    try:
        r = urllib.request.Request(url, data=data, method=method, headers=h)
        resp = opener.open(r, timeout=TIMEOUT)
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
        out["results"].append(req_raw(p, "OPTIONS"))
        time.sleep(DELAY)
    for p in ["/login", "/render", "/ping"]:
        out["results"].append(req_raw(p, "POST", b"", "application/x-www-form-urlencoded"))
        time.sleep(DELAY)
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
