#!/usr/bin/env python3
"""INT-r27-0009 script 2: POST shape probe on svc-files:8008.
Targets: /login /upload /import /xml /fetch /search /comment (+401 endpoint /admin/logs).
Two shapes each: urlencoded t=1 and JSON {"t":1}. No credential guessing, no payloads."""
import json, time, urllib.request, urllib.error

BASE = "http://svc-files:8008"
PATHS = ["/login", "/upload", "/import", "/xml", "/fetch", "/search", "/comment", "/admin/logs"]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

def post(path, data, ctype):
    req = urllib.request.Request(
        BASE + path, data=data, method="POST",
        headers={"User-Agent": "recon-int-r27/1.0", "Content-Type": ctype})
    try:
        resp = opener.open(req, timeout=5)
        body = resp.read(800)
        return {"status": resp.status,
                "headers": {k.lower(): v for k, v in resp.headers.items()
                            if k.lower() in ("content-type", "content-length", "location",
                                              "server", "allow", "www-authenticate")},
                "body_head": body[:400].decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        body = e.read(800)
        return {"status": e.code,
                "headers": {k.lower(): v for k, v in e.headers.items()
                            if k.lower() in ("content-type", "content-length", "location",
                                              "server", "allow", "www-authenticate")},
                "body_head": body[:400].decode("utf-8", "replace")}
    except Exception as e:
        return {"error": repr(e)}

results = []
for p in PATHS:
    entry = {
        "path": p,
        "form": post(p, b"t=1", "application/x-www-form-urlencoded"),
    }
    time.sleep(0.25)
    entry["json"] = post(p, json.dumps({"t": 1}).encode(), "application/json")
    results.append(entry)
    time.sleep(0.25)

print(json.dumps(results, ensure_ascii=False, indent=1))
