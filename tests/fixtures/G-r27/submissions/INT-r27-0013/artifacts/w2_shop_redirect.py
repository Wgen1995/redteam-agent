#!/usr/bin/env python3
# INT-r27-0013: svc-shop /logout 开放重定向验证
# 参数族 ?next/?to/?url/?goto/?redirect/?continue 各发外域值 http://evil.example
# http.client 不跟随重定向，捕 302 读 Location；判据=Location 含外域载荷串
import http.client, json, time, urllib.parse

HOST, PORT = "svc-shop", 8001
PARAMS = ["next", "to", "url", "goto", "redirect", "continue"]
VALUES = [
    ("abs-http", "http://evil.example"),
    ("proto-rel", "//evil.example"),
    ("abs-https-path", "https://evil.example/r?x=1"),
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
time.sleep(0.25)
try:
    s, h, b = send("/logout")
    results.append({"path": "/logout", "query": None, "param": "(bare)", "payload_tag": "bare", "payload": None,
                    "raw_request": "GET /logout HTTP/1.1\r\nHost: svc-shop:8001\r\n\r\n",
                    "status": s, "headers": h, "body": b})
except Exception as e:
    results.append({"path": "/logout", "param": "(bare)", "payload_tag": "bare", "error": repr(e)})

for prm in PARAMS:
    for tag, val in VALUES:
        q = prm + "=" + urllib.parse.quote(val, safe="")
        tgt = "/logout?" + q
        time.sleep(0.25)
        try:
            s, h, b = send(tgt)
            results.append({"path": "/logout", "query": q, "param": prm, "payload_tag": tag, "payload": val,
                            "raw_request": "GET %s HTTP/1.1\r\nHost: svc-shop:8001\r\n\r\n" % tgt,
                            "status": s, "headers": h, "body": b})
        except Exception as e:
            results.append({"path": "/logout", "query": q, "param": prm, "payload_tag": tag, "payload": val, "error": repr(e)})

print(json.dumps({"intent": "INT-r27-0013", "target": "http://svc-shop:8001",
                  "count": len(results), "results": results}, ensure_ascii=False))
