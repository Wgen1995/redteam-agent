#!/usr/bin/env python3
# INT-r27-0004 script1: GET dictionary spray on svc-admin:8003 (discovery only, no payloads)
import urllib.request, urllib.error, time, json, re

BASE = "http://svc-admin:8003"
UA = "Mozilla/5.0 (compatible; recon/1.0)"

DICT = [
    ("cred", "/login"), ("cred", "/signin"), ("cred", "/api/login"), ("cred", "/register"),
    ("cred", "/signup"), ("cred", "/api/register"), ("cred", "/forgot"), ("cred", "/reset"),
    ("cred", "/api/reset"), ("cred", "/password-reset"), ("cred", "/token"), ("cred", "/api/token"),
    ("cred", "/oauth/token"), ("cred", "/auth"), ("cred", "/logout"), ("cred", "/session"), ("cred", "/me"),
    ("info", "/debug/env"), ("info", "/debug/vars"), ("info", "/actuator/env"), ("info", "/metrics"),
    ("info", "/.env"), ("info", "/info"), ("info", "/graphql"), ("info", "/health"), ("info", "/status"), ("info", "/version"),
    ("ssrf", "/fetch"), ("ssrf", "/preview"), ("ssrf", "/proxy"), ("ssrf", "/render"), ("ssrf", "/template"),
    ("processor", "/unserialize"), ("processor", "/deserialize"), ("processor", "/decode"), ("processor", "/import"),
    ("processor", "/upload"), ("processor", "/export"), ("processor", "/xml"), ("processor", "/api/xml"),
    ("resource", "/item"), ("resource", "/order"), ("resource", "/product"), ("resource", "/detail"),
    ("resource", "/invoice"), ("resource", "/user"), ("resource", "/account"), ("resource", "/users"), ("resource", "/admin/users"),
    ("xss", "/search"), ("xss", "/echo"), ("xss", "/comment"), ("xss", "/reply"),
    ("xss", "/feedback"), ("xss", "/q"), ("xss", "/report"),
    ("file", "/download"), ("file", "/file"), ("file", "/read"), ("file", "/static"), ("file", "/files"),
    ("cors", "/cors"), ("cors", "/cors-debug"), ("cors", "/origin"),
    ("redirect", "/redirect"), ("redirect", "/goto"), ("redirect", "/jump"), ("redirect", "/out"), ("redirect", "/link"),
    ("admin", "/admin"), ("admin", "/manage"), ("admin", "/console"), ("admin", "/admin/config"),
    ("admin", "/admin/logs"), ("admin", "/admin/keys"), ("admin", "/admin/reports"), ("admin", "/admin/clients"),
    ("admin", "/admin/audit"), ("admin", "/admin/settings"), ("admin", "/admin/users"), ("admin", "/admin/orders"), ("admin", "/admin/invoices"),
    ("cmdi", "/exec"), ("cmdi", "/run"), ("cmdi", "/eval"), ("cmdi", "/ping"),
    ("api", "/api"), ("api", "/api/v1"), ("api", "/api/v2"), ("internal", "/internal"), ("internal", "/private"),
]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)
KEEP = {"Server", "Content-Type", "Content-Length", "Location", "WWW-Authenticate", "Allow", "Set-Cookie", "Access-Control-Allow-Origin"}

def title_of(b):
    m = re.search(r"<title[^>]*>(.*?)</title>", b, re.I | re.S)
    return m.group(1).strip()[:80] if m else ""

for fam, path in DICT:
    rec = {"family": fam, "path": path}
    req = urllib.request.Request(BASE + path, method="GET", headers={"User-Agent": UA})
    try:
        r = opener.open(req, timeout=5)
        body = r.read(4096).decode("utf-8", "replace")
        rec["status"] = r.status
        rec["headers"] = {k: v for k, v in r.headers.items() if k in KEEP}
        rec["title"] = title_of(body)
        rec["body_head"] = body[:400]
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(4096).decode("utf-8", "replace")
        except Exception:
            pass
        rec["status"] = e.code
        rec["headers"] = {k: v for k, v in e.headers.items() if k in KEEP} if e.headers else {}
        rec["title"] = title_of(body)
        rec["body_head"] = body[:400]
    except Exception as e:
        rec["status"] = None
        rec["error"] = repr(e)
    print(json.dumps(rec, ensure_ascii=False))
    time.sleep(0.25)
print("DONE")
