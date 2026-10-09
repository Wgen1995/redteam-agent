#!/usr/bin/env python3
"""Script 1: GET dictionary spray on svc-api-gw:8002. Rate-limit aware (30req/10s)."""
import json, time, urllib.request, urllib.error


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)
BASE = "http://svc-api-gw:8002"
INTERESTING_HDRS = ("server", "content-type", "location", "x-powered-by", "allow",
                    "www-authenticate", "retry-after", "access-control-allow-origin",
                    "set-cookie", "x-rateLimit-remaining", "x-ratelimit-remaining")

DICT = {
    "cred": "/login /signin /api/login /register /signup /api/register /forgot /reset /api/reset /password-reset /token /api/token /oauth/token /auth /logout /session /me",
    "info": "/debug/env /debug/vars /actuator/env /metrics /.env /info /graphql /health /status /version",
    "ssrf": "/fetch /preview /proxy /render /template",
    "handler": "/unserialize /deserialize /decode /import /upload /export /xml /api/xml",
    "resource": "/item /order /product /detail /invoice /user /account",
    "xss": "/search /echo /comment /reply /feedback /q /report",
    "file": "/download /file /read /static /files",
    "cors": "/cors /cors-debug /origin",
    "redirect": "/redirect /goto /jump /out /link",
    "admin": "/admin /manage /console /admin/config /admin/logs /admin/keys /admin/reports /admin/clients /admin/audit /admin/settings /admin/users",
    "ssti_cmdi": "/exec /run /eval /ping",
    "internal": "/api /api/v1 /api/v2 /internal /private",
}

results = []
interval = 0.4
saw_429 = False

for fam, paths in DICT.items():
    for p in paths.split():
        entry = {"family": fam, "path": p, "status": None, "headers": {}, "body": "", "notes": []}
        for attempt in range(3):
            try:
                req = urllib.request.Request(BASE + p, method="GET",
                                             headers={"User-Agent": "recon/1.0"})
                resp = OPENER.open(req, timeout=5)
                entry["status"] = resp.status
                entry["headers"] = {k.lower(): v for k, v in resp.headers.items() if k.lower() in INTERESTING_HDRS}
                entry["body"] = resp.read(400).decode("utf-8", "replace")
                break
            except urllib.error.HTTPError as e:
                entry["status"] = e.code
                entry["headers"] = {k.lower(): v for k, v in e.headers.items() if k.lower() in INTERESTING_HDRS}
                try:
                    entry["body"] = e.read(400).decode("utf-8", "replace")
                except Exception:
                    pass
                if e.code == 429:
                    saw_429 = True
                    entry["notes"].append(f"429@attempt{attempt+1} retry-after={e.headers.get('Retry-After')}")
                    time.sleep(3.5)
                    interval = min(interval * 1.5, 1.0)
                    continue
                break
            except Exception as e:
                entry["status"] = None
                entry["notes"].append(f"{type(e).__name__}:{e}")
                break
        results.append(entry)
        flag = "*" if (entry["status"] not in (404, None)) else " "
        print(f"[{flag}] {entry['status']:<4} {p:<20} fam={fam:<10} hdr={ {k:v for k,v in entry['headers'].items() if k!='server'} } body[:120]={entry['body'][:120]!r}")
        time.sleep(interval)

alive = [r for r in results if r["status"] not in (404, None)]
print(f"\n[SUMMARY] total={len(results)} non404={len(alive)} saw_429={saw_429}")
for r in alive:
    print(f"  HIT {r['status']} {r['path']} ({r['family']}) hdr={r['headers']} body[:200]={r['body'][:200]!r}")
with open("/tmp/p1-result.json", "w") as f:
    json.dump({"results": results, "saw_429": saw_429}, f, indent=1)
