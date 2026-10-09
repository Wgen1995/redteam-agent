#!/usr/bin/env python3
# INT-r27-0007 脚本1：GET 字典喷洒 http://svc-dashboard:8006（只发现，不猜口令，不发攻击载荷）
import json, time, sys
import urllib.request, urllib.error

BASE = "http://svc-dashboard:8006"
DELAY = 0.22
TIMEOUT = 5

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

KEY_HEADERS = ["Server", "X-Powered-By", "Content-Type", "Location",
               "WWW-Authenticate", "Set-Cookie", "X-Frame-Options",
               "Access-Control-Allow-Origin", "Allow", "Content-Length", "X-Request-Id"]

FAMILIES = {
 "cred": ["/login","/signin","/api/login","/register","/signup","/api/register",
          "/forgot","/reset","/api/reset","/password-reset","/token","/api/token",
          "/oauth/token","/auth","/logout","/session","/me"],
 "info": ["/debug/env","/debug/vars","/actuator/env","/metrics","/.env","/info",
          "/graphql","/health","/status","/version","/stats","/api/stats",
          "/dashboard","/panel"],
 "ssrf": ["/fetch","/preview","/proxy","/render","/template","/widget","/widgets"],
 "handler": ["/unserialize","/deserialize","/decode","/import","/upload","/export","/xml"],
 "resource": ["/item","/order","/product","/detail","/invoice","/user","/account","/users"],
 "xss": ["/search","/echo","/comment","/reply","/feedback","/q","/report"],
 "file": ["/download","/file","/read","/static","/files","/assets"],
 "cors": ["/cors","/cors-debug","/origin"],
 "redirect": ["/redirect","/goto","/jump","/out","/link"],
 "admin": ["/admin","/manage","/console","/admin/config","/admin/logs","/admin/keys",
           "/admin/reports","/admin/clients","/admin/audit","/admin/settings","/admin/users"],
 "cmdi": ["/exec","/run","/eval","/ping"],
 "internal": ["/api","/api/v1","/api/v2","/internal","/private"],
}

def get(path):
    url = BASE + path
    rec = {"path": path}
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
    out = {"ts": "2026-10-23T15:30:00Z", "base": BASE, "results": []}
    n = 0
    for fam, paths in FAMILIES.items():
        for p in paths:
            rec = get(p)
            rec["family"] = fam
            out["results"].append(rec)
            n += 1
            time.sleep(DELAY)
    out["count"] = n
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
