#!/usr/bin/env python3
# INT-r27-0006 s1: GET dictionary spray (discovery only, no payloads, no cred guessing)
# usage: python3 r27_0006_s1_spray.py <port>
import sys, json, time, re, urllib.request, urllib.error

PORT = int(sys.argv[1])
KEEP_HDR = ("server", "content-type", "location", "www-authenticate",
            "allow", "x-powered-by", "access-control-allow-origin")

PATHS = [
    # 凭据族
    "/login", "/signin", "/api/login", "/register", "/signup", "/api/register",
    "/forgot", "/reset", "/api/reset", "/password-reset", "/token", "/api/token",
    "/oauth/token", "/auth", "/logout", "/session", "/me",
    # 信息族
    "/debug/env", "/debug/vars", "/actuator/env", "/metrics", "/.env", "/info",
    "/graphql", "/health", "/status", "/version",
    # SSRF 族
    "/fetch", "/preview", "/proxy", "/render", "/template",
    # 处理器族
    "/unserialize", "/deserialize", "/decode", "/import", "/upload", "/export", "/xml",
    # 资源参数族（账务）
    "/item", "/order", "/product", "/detail", "/invoice", "/invoices", "/user",
    "/account", "/billing", "/payment", "/payments", "/subscription",
    # XSS 族
    "/search", "/echo", "/comment", "/reply", "/feedback", "/q", "/report",
    # 文件族
    "/download", "/file", "/read", "/static", "/files",
    # CORS 族
    "/cors", "/cors-debug", "/origin",
    # 重定向族
    "/redirect", "/goto", "/jump", "/out", "/link",
    # 管理族
    "/admin", "/manage", "/console", "/admin/config", "/admin/logs", "/admin/keys",
    "/admin/reports", "/admin/clients", "/admin/audit", "/admin/settings",
    "/admin/users", "/admin/invoices",
    # 版本/内部族
    "/api", "/api/v1", "/api/v2", "/internal", "/private",
]

SIGNALS = ["error", "exception", "traceback", "stack", "token", "jwt", "secret",
           "password", "debug", "sql", "swagger", "openapi", "api-docs", "version",
           "unauthor", "forbidden", "not found", "404", "500", "login", "admin",
           "flag{", "key", "config", "env"]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def distinctive(body):
    hits = []
    low = body.lower()
    for s in SIGNALS:
        if s in low and s not in hits:
            hits.append(s)
    m = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    title = m.group(1).strip()[:80] if m else None
    return {"signals": hits[:8], "title": title}

def get(path):
    url = "http://svc-billing:%d%s" % (PORT, path)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (recon)"})
    opener = urllib.request.build_opener(NoRedirect)
    rec = {"path": path}
    try:
        r = opener.open(req, timeout=5)
        body = r.read(400).decode("utf-8", "replace")
        rec.update({"status": r.status,
                    "headers": {k: v for k, v in r.headers.items() if k.lower() in KEEP_HDR},
                    "len_first": len(body),
                    "body400": body, "distinctive": distinctive(body)})
    except urllib.error.HTTPError as e:
        body = e.read(400).decode("utf-8", "replace")
        rec.update({"status": e.code,
                    "headers": {k: v for k, v in e.headers.items() if k.lower() in KEEP_HDR},
                    "len_first": len(body),
                    "body400": body, "distinctive": distinctive(body)})
    except Exception as e:
        rec.update({"status": None, "error": "%s: %s" % (type(e).__name__, e)})
    return rec

results = []
for p in PATHS:
    results.append(get(p))
    time.sleep(0.2)

print(json.dumps({"port": PORT, "count": len(results), "results": results},
                 ensure_ascii=False, indent=1))
