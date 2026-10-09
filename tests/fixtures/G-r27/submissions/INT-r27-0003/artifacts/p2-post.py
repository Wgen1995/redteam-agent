#!/usr/bin/env python3
"""Script 2: POST form probing on svc-api-gw:8002. urlencoded t=1 + JSON {"t":1}, no creds."""
import json, time, urllib.request, urllib.error


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)
BASE = "http://svc-api-gw:8002"
PATHS = ["/login", "/register", "/token", "/upload", "/import", "/xml", "/fetch", "/search", "/comment"]
HDRS = ("server", "content-type", "location", "allow", "retry-after", "access-control-allow-origin", "set-cookie")

results = []
interval = 0.4
saw_429 = False

for p in PATHS:
    for mode in ("form", "json"):
        if mode == "form":
            data = b"t=1"
            ct = "application/x-www-form-urlencoded"
        else:
            data = json.dumps({"t": 1}).encode()
            ct = "application/json"
        entry = {"path": p, "mode": mode, "status": None, "headers": {}, "body": "", "notes": []}
        for attempt in range(3):
            try:
                req = urllib.request.Request(BASE + p, method="POST", data=data,
                                             headers={"User-Agent": "recon/1.0", "Content-Type": ct})
                resp = OPENER.open(req, timeout=5)
                entry["status"] = resp.status
                entry["headers"] = {k.lower(): v for k, v in resp.headers.items() if k.lower() in HDRS}
                entry["body"] = resp.read(400).decode("utf-8", "replace")
                break
            except urllib.error.HTTPError as e:
                entry["status"] = e.code
                entry["headers"] = {k.lower(): v for k, v in e.headers.items() if k.lower() in HDRS}
                try:
                    entry["body"] = e.read(400).decode("utf-8", "replace")
                except Exception:
                    pass
                if e.code == 429:
                    saw_429 = True
                    entry["notes"].append(f"429@attempt{attempt+1} retry-after={e.headers.get('Retry-After')}")
                    time.sleep(3.5)
                    continue
                break
            except Exception as e:
                entry["status"] = None
                entry["notes"].append(f"{type(e).__name__}:{e}")
                break
        results.append(entry)
        print(f"[{mode:>4}] {entry['status']}  POST {p:<10} ct={ct.split('/')[-1]:<16} hdr={entry['headers']} body[:150]={entry['body'][:150]!r}")
        time.sleep(interval)

diff = []
for i in range(0, len(results), 2):
    f, j = results[i], results[i + 1]
    if f["status"] != j["status"] or f["body"] != j["body"]:
        diff.append(f["path"])
print(f"\n[SUMMARY] posts={len(results)} form_vs_json_diff={diff} saw_429={saw_429}")
with open("/tmp/p2-result.json", "w") as f2:
    json.dump({"results": results, "diff": diff, "saw_429": saw_429}, f2, indent=1)
