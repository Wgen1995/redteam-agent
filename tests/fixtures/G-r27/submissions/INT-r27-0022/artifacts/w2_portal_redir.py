# INT-r27-0022 open-redirect matrix-test: /redirect param family x http://evil.example
# GET-only, capture Location header, NO redirect following (http.client never follows)
import http.client, json, time, urllib.parse

HOST, PORT = "svc-portal", 8007
params = ["to", "url", "next", "goto", "target", "u"]
payload = "http://evil.example"
out = {"meta": {"intent": "INT-r27-0022", "kind": "open-redirect-matrix", "ts_literal": "2026-10-23T16:00:00Z"}, "cases": []}

def get_raw(path):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=6)
    raw_req = "GET %s HTTP/1.1\r\nHost: %s:%d\r\n\r\n" % (path, HOST, PORT)
    t0 = time.time()
    try:
        conn.request("GET", path)
        r = conn.getresponse()
        body = r.read(800).decode("utf-8", "replace")
        res = {
            "raw_request": raw_req,
            "resp_status": r.status,
            "resp_headers": {k: v for k, v in r.getheaders()},
            "location": r.getheader("Location"),
            "resp_body_excerpt": body[:300],
            "elapsed_ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:
        res = {"raw_request": raw_req, "error": repr(e)[:160]}
    finally:
        conn.close()
    return res

out["cases"].append({"case": "baseline", "param": None, "payload": None, "path": "/redirect", **get_raw("/redirect")})
time.sleep(0.3)
for p in params:
    q = "/redirect?%s=" % p
    out["cases"].append({"case": "empty-param-baseline", "param": p, "payload": None, "path": q, **get_raw(q)})
    time.sleep(0.3)
for p in params:
    q = "/redirect?%s=%s" % (p, urllib.parse.quote(payload, safe=":/"))
    out["cases"].append({"case": "payload", "param": p, "payload": payload, "path": q, **get_raw(q)})
    time.sleep(0.3)

print(json.dumps(out, ensure_ascii=False, indent=1))
