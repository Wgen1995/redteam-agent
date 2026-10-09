#!/usr/bin/env python3
# INT-r27-0012: svc-shop XSS 反射验证四面 (/search /comment /reply /feedback)
# 每面×参数族×三载荷形（tag/event/quote-break）全枚举；URL 编码后发；
# 判据=响应体未编码回显探针串 probe7x9/bold7x9 原形；编码回显=对照负
import http.client, json, time, urllib.parse

HOST, PORT = "svc-shop", 8001
PATHS = ["/search", "/comment", "/reply", "/feedback"]
PARAMS = ["q", "query", "s", "keyword", "k", "text", "msg", "name", "id", "content"]
PAYLOADS = [
    ("x1-tag", "<b>bold7x9</b>"),
    ("x2-event", "<img src=x onerror=probe7x9>"),
    ("x3-quotebreak", "\" onmouseover=probe7x9 \""),
]

def send(path_query):
    c = http.client.HTTPConnection(HOST, PORT, timeout=8)
    c.request("GET", path_query, headers={"Host": "svc-shop:8001", "Connection": "close"})
    r = c.getresponse()
    body = r.read().decode("utf-8", "replace")
    hdrs = dict(r.getheaders())
    st = r.status
    c.close()
    return st, hdrs, body

results = []
for p in PATHS:
    time.sleep(0.25)
    try:
        s, h, b = send(p)
        results.append({"path": p, "query": None, "param": "(bare)", "payload_tag": "bare", "payload": None,
                        "raw_request": "GET %s HTTP/1.1\r\nHost: svc-shop:8001\r\n\r\n" % p,
                        "status": s, "headers": h, "body": b})
    except Exception as e:
        results.append({"path": p, "param": "(bare)", "payload_tag": "bare", "error": repr(e)})

for p in PATHS:
    for prm in PARAMS:
        for tag, pl in PAYLOADS:
            q = prm + "=" + urllib.parse.quote(pl, safe="")
            tgt = p + "?" + q
            time.sleep(0.25)
            try:
                s, h, b = send(tgt)
                results.append({"path": p, "query": q, "param": prm, "payload_tag": tag, "payload": pl,
                                "raw_request": "GET %s HTTP/1.1\r\nHost: svc-shop:8001\r\n\r\n" % tgt,
                                "status": s, "headers": h, "body": b})
            except Exception as e:
                results.append({"path": p, "query": q, "param": prm, "payload_tag": tag, "payload": pl, "error": repr(e)})

print(json.dumps({"intent": "INT-r27-0012", "target": "http://svc-shop:8001",
                  "count": len(results), "results": results}, ensure_ascii=False))
