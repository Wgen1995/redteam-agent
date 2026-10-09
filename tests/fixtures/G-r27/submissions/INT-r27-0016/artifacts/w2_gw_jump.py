#!/usr/bin/env python3
# INT-r27-0016 open-redirect matrix-test: /jump x params(url,to,next,goto,target,u) x value=http://evil.example
# raw socket -> byte-exact raw_request; capture 302 Location; interval>=0.25s; 429->sleep 3.5 retry once
import socket, json, time, urllib.parse

HOST, PORT = "svc-api-gw", 8002
TS = "2026-10-23T16:00:00Z"
FACE = "/jump"
PARAMS = ["url", "to", "next", "goto", "target", "u"]
VALUE = "http://evil.example"

def raw_req(qs, timeout=8.0):
    raw = "GET %s HTTP/1.1\r\nHost: %s:%d\r\n\r\n" % (qs, HOST, PORT)
    t0 = time.time()
    err = None
    buf = b""
    try:
        s = socket.create_connection((HOST, PORT), timeout=timeout)
        s.sendall(raw.encode("latin1"))
        s.settimeout(timeout)
        hdr_done, clen, te = False, None, None
        while len(buf) < 262144:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if not hdr_done and b"\r\n\r\n" in buf:
                hdr_done = True
                head = buf.split(b"\r\n\r\n", 1)[0].decode("latin1")
                for ln in head.split("\r\n")[1:]:
                    if ":" in ln:
                        k, v = ln.split(":", 1)
                        kl = k.strip().lower()
                        if kl == "content-length":
                            clen = int(v.strip())
                        elif kl == "transfer-encoding":
                            te = v.strip().lower()
                if te is None and clen is not None and len(buf) >= buf.find(b"\r\n\r\n") + 4 + clen:
                    break
        s.close()
    except Exception as e:
        err = repr(e)
    head, _, body = buf.partition(b"\r\n\r\n")
    status, headers = None, {}
    lines = head.decode("latin1").split("\r\n")
    if lines and lines[0].startswith("HTTP/"):
        parts = lines[0].split(" ", 2)
        if len(parts) >= 2:
            try:
                status = int(parts[1])
            except ValueError:
                pass
        for ln in lines[1:]:
            if ":" in ln:
                k, v = ln.split(":", 1)
                headers[k.strip().lower()] = v.strip()
    excerpt = body[:500].decode("latin1")
    printable = "".join(ch if 32 <= ord(ch) < 127 else "." for ch in excerpt)
    return {
        "raw_request": raw, "status": status, "resp_headers": headers,
        "body_len": len(body), "body_excerpt": printable,
        "elapsed_s": round(time.time() - t0, 3), "error": err,
    }

seq = [0]

def run_qs(tag, param, qs, value):
    seq[0] += 1
    rec = raw_req(qs)
    if rec["status"] == 429:
        time.sleep(3.5)
        rec = raw_req(qs)
        rec["retry_after_429"] = True
    rec.update({"seq": seq[0], "tag": tag, "ts": TS, "face": FACE, "param": param, "qs": qs, "value": value})
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    time.sleep(0.26)

# control: bare face
run_qs("ctrl-bare", None, FACE, None)
# controls: empty param per param name (同面参数并列全扫律)
for p in PARAMS:
    run_qs("ctrl-empty", p, "%s?%s=" % (FACE, p), "")
# matrix: external redirect value
for p in PARAMS:
    run_qs("matrix", p, "%s?%s=%s" % (FACE, p, urllib.parse.quote(VALUE, safe="")), VALUE)

print("[SUMMARY] total_requests=%d face=%s params=%d value=%s ts=%s" % (seq[0], FACE, len(PARAMS), VALUE, TS), flush=True)
