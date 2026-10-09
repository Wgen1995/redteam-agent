# INT-r27-0023 info-exposure: /debug/env direct GET (full key-name inventory + body digest)
# plus second-face sweep: /graphql /metrics /actuator/env (same-family third-face rule)
# GET-only, no redirect following, interval >= 0.3s
import http.client, json, time

HOST, PORT = "svc-portal", 8007
targets = ["/debug/env", "/debug", "/graphql", "/metrics", "/actuator/env"]
out = {"meta": {"intent": "INT-r27-0023", "kind": "info-exposure-env", "ts_literal": "2026-10-23T16:00:00Z"}, "cases": []}

def get_raw(path):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=6)
    raw_req = "GET %s HTTP/1.1\r\nHost: %s:%d\r\n\r\n" % (path, HOST, PORT)
    t0 = time.time()
    try:
        conn.request("GET", path)
        r = conn.getresponse()
        body = r.read(4000).decode("utf-8", "replace")
        res = {
            "raw_request": raw_req,
            "resp_status": r.status,
            "resp_headers": {k: v for k, v in r.getheaders()},
            "resp_body_excerpt": body[:400],
            "body_full": body if len(body) <= 3000 else body[:3000] + "...[trunc]",
            "elapsed_ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:
        res = {"raw_request": raw_req, "error": repr(e)[:160]}
    finally:
        conn.close()
    return res

for p in targets:
    out["cases"].append({"path": p, **get_raw(p)})
    time.sleep(0.3)

print(json.dumps(out, ensure_ascii=False, indent=1))
