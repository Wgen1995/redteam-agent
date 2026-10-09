#!/usr/bin/env python3
# INT-r27-0027 matrix-test: rate-limit missing sequence verification vs svc-login:8004
# Sequence A: POST /login x12, 0.5s interval (gentle pace, no high-frequency hammering)
# Sequence B: POST /api/login x3 (cross-face shared counter control)
import http.client, time, re, json

HOST, PORT = "svc-login", 8004
BODY = "user=rateprobe&pass=rateprobe"

def post(path):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=10)
    conn.request("POST", path, body=BODY, headers={
        "Host": "%s:%d" % (HOST, PORT),
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": str(len(BODY)),
    })
    r = conn.getresponse()
    status = r.status
    hdrs = {k.lower(): v for k, v in r.getheaders()}
    body = r.read().decode("utf-8", "replace")
    conn.close()
    return status, hdrs, body

def counter_of(body):
    m = re.search(r"after (\d+) attempts", body)
    return int(m.group(1)) if m else None

rows = []
print("=== SEQ A: POST /login x12 (interval 0.5s) ===")
for i in range(1, 13):
    status, hdrs, body = post("/login")
    rows.append({"seq": "A%d" % i, "route": "/login", "status": status,
                 "counter": counter_of(body), "retry_after": hdrs.get("retry-after"),
                 "body": body, "headers": hdrs})
    print("seq=A%d\troute=/login\tstatus=%d\tcounter=%s\tretry_after=%s\tbody=%s"
          % (i, status, counter_of(body), hdrs.get("retry-after"), body))
    if i < 12:
        time.sleep(0.5)

print("=== SEQ B: POST /api/login x3 (cross-face control, interval 0.5s) ===")
for i in range(1, 4):
    status, hdrs, body = post("/api/login")
    rows.append({"seq": "B%d" % i, "route": "/api/login", "status": status,
                 "counter": counter_of(body), "retry_after": hdrs.get("retry-after"),
                 "body": body, "headers": hdrs})
    print("seq=B%d\troute=/api/login\tstatus=%d\tcounter=%s\tretry_after=%s\tbody=%s"
          % (i, status, counter_of(body), hdrs.get("retry-after"), body))
    if i < 3:
        time.sleep(0.5)

# machine-readable block for evidence assembly
a = [r for r in rows if r["seq"].startswith("A")]
b = [r for r in rows if r["seq"].startswith("B")]
monotonic_a = all(a[i]["counter"] is not None and a[i+1]["counter"] is not None
                  and a[i+1]["counter"] > a[i]["counter"] for i in range(len(a)-1))
cross_face_cont = (a[-1]["counter"] is not None and b[0]["counter"] is not None
                   and b[0]["counter"] > a[-1]["counter"])
monotonic_b = all(b[i]["counter"] is not None and b[i+1]["counter"] is not None
                  and b[i+1]["counter"] > b[i]["counter"] for i in range(len(b)-1))
has_429 = any(r["status"] == 429 for r in rows)
has_retry_after = any(r["retry_after"] for r in rows)
has_no_rate_limit = all("no rate limit" in r["body"] for r in rows)
has_gtrate = all("GTRATE-01" in r["body"] for r in rows)
last = a[-1]

print("=== VERDICT INPUTS (json) ===")
print(json.dumps({
    "seq_a_status_set": sorted(set(r["status"] for r in a)),
    "seq_b_status_set": sorted(set(r["status"] for r in b)),
    "seq_a_counters": [r["counter"] for r in a],
    "seq_b_counters": [r["counter"] for r in b],
    "monotonic_a": monotonic_a,
    "monotonic_b": monotonic_b,
    "cross_face_continuation": cross_face_cont,
    "any_429": has_429,
    "any_retry_after": has_retry_after,
    "all_gtrate01": has_gtrate,
    "all_no_rate_limit_phrase": has_no_rate_limit,
    "body_len_bytes": len(last["body"].encode()),
    "last_a_headers": last["headers"],
    "last_a_body": last["body"],
    "content_length_sent": len(BODY),
}, ensure_ascii=False))
