#!/usr/bin/env python3
# INT-r27-0005 script2: POST form-shape probing (dummy values only) on http://svc-login:8004
# 7 faces x 4 shapes (urlencoded x3 keyname-families + JSON x1), one shot each, interval 0.2s
import urllib.request, urllib.error, hashlib, time, json

BASE = "http://svc-login:8004"
UA = "Mozilla/5.0 (compatible; recon/1.0)"

FACES = ["/login", "/api/login", "/token", "/api/token", "/register", "/forgot", "/reset"]

SHAPES = [
    ("form:user-pass",       "application/x-www-form-urlencoded", b"user=probe&pass=probe"),
    ("form:username-password", "application/x-www-form-urlencoded", b"username=probe&password=probe"),
    ("form:email",           "application/x-www-form-urlencoded", b"email=probe@probe.local"),
    ("json:user-pass",       "application/json",                   b'{"user":"probe","pass":"probe"}'),
]

KEY_HEADERS = ["Content-Type", "Location", "Set-Cookie", "WWW-Authenticate", "X-Auth-Token",
               "Allow", "Server", "Content-Length", "X-Session", "Authorization"]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

results = []
for face in FACES:
    url = BASE + face
    for shape, ctype, body in SHAPES:
        rec = {"face": face, "shape": shape, "content_type": ctype, "body_sent": body.decode("utf-8")}
        req = urllib.request.Request(url, method="POST", data=body,
                                     headers={"User-Agent": UA, "Content-Type": ctype})
        try:
            r = opener.open(req, timeout=5)
            rb = r.read(8192)
            rec["status"] = r.status
            hdrs = {k: v for k, v in r.headers.items()}
            rec["headers"] = {k: hdrs[k] for k in KEY_HEADERS if k in hdrs}
            rec["body_sha256"] = hashlib.sha256(rb).hexdigest()[:16]
            rec["body_len"] = len(rb)
            rec["body_head"] = rb[:200].decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            rb = b""
            try:
                rb = e.read(8192)
            except Exception:
                pass
            rec["status"] = e.code
            hdrs = {k: v for k, v in e.headers.items()} if e.headers else {}
            rec["headers"] = {k: hdrs[k] for k in KEY_HEADERS if k in hdrs}
            rec["body_sha256"] = hashlib.sha256(rb).hexdigest()[:16]
            rec["body_len"] = len(rb)
            rec["body_head"] = rb[:200].decode("utf-8", "replace")
        except Exception as e:
            rec["error"] = "%s: %s" % (type(e).__name__, e)
        results.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)
        time.sleep(0.2)

# differentiation analysis: group by (status, body_sha256) signature
sigs = {}
for r in results:
    if "error" in r:
        sigs.setdefault(("error", r["error"]), []).append("%s|%s" % (r["face"], r["shape"]))
    else:
        sigs.setdefault((r["status"], r["body_sha256"], r["body_len"]), []).append("%s|%s" % (r["face"], r["shape"]))
print(json.dumps({"summary": "post-shape-done", "total": len(results),
                  "distinct_signatures": len(sigs),
                  "signature_groups": [{"sig": list(k), "members": v} for k, v in sigs.items()]},
                 ensure_ascii=False), flush=True)
