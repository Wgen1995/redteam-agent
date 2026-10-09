#!/usr/bin/env python3
# INT-r27-0015 CORS origin-variant matrix: /cors-debug + /origin x 4 Origin variants (3 + no-Origin control)
# GET-only, no redirect follow, interval >= 0.25s, 429 backoff >= 3s
import http.client, time, json, urllib.parse

HOST, PORT = "svc-api-gw", 8002
PATHS = ["/cors-debug", "/origin"]
ORIGINS = [
    ("evil",      "https://evil.example"),
    ("null",      "null"),
    ("subdomain", "https://sub.example.com"),
    ("control",   None),  # no Origin header
]

def raw_request(path, origin):
    lines = ["GET %s HTTP/1.1" % path, "Host: %s:%d" % (HOST, PORT),
             "User-Agent: w2-probe/1.0", "Accept: */*", "Connection: close"]
    if origin is not None:
        lines.insert(2, "Origin: %s" % origin)
    return ("\r\n".join(lines) + "\r\n\r\n")

def fetch(path, origin):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=8)
    hdrs = {"User-Agent": "w2-probe/1.0", "Accept": "*/*", "Connection": "close"}
    if origin is not None:
        hdrs["Origin"] = origin
    try:
        conn.request("GET", path, headers=hdrs)
        r = conn.getresponse()
        body = r.read(2048)
        return {"status": r.status, "reason": r.reason,
                "headers": {k.lower(): v for k, v in r.getheaders()},
                "body_excerpt": body.decode("utf-8", "replace")[:400]}
    finally:
        conn.close()

results = []
for path in PATHS:
    for name, ov in ORIGINS:
        rr = raw_request(path, ov)
        rec = {"path": path, "origin_variant": name, "origin_value": ov,
               "raw_request": rr}
        try:
            resp = fetch(path, ov)
            if resp["status"] == 429:
                time.sleep(3.0)
                resp = fetch(path, ov)
                resp["note"] = "429-backoff-retry-3s"
        except Exception as e:
            resp = {"status": None, "error": repr(e)}
        cors_keys = ["access-control-allow-origin", "access-control-allow-credentials",
                     "access-control-allow-headers", "access-control-allow-methods",
                     "access-control-expose-headers", "access-control-max-age", "vary"]
        rec["resp"] = resp
        rec["cors_headers"] = {k: resp.get("headers", {}).get(k) for k in cors_keys
                               if resp.get("headers", {}).get(k) is not None}
        results.append(rec)
        print(json.dumps({"path": path, "variant": name, "status": resp.get("status"),
                          "cors": rec["cors_headers"]}, ensure_ascii=False))
        time.sleep(0.3)

out = {"script": "w2_gwc_cors", "ts": "2026-10-23T16:00:00Z",
       "target": "%s:%d" % (HOST, PORT), "requests": len(results), "results": results}
with open("/tmp/w2_gwc_cors.json", "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("DONE requests=%d" % len(results))
