#!/usr/bin/env python3
# INT-r27-0006 s2: POST shape probing (urlencoded t=1 vs JSON {"t":1}), no cred guessing
# usage: python3 r27_0006_s2_post.py <port>
import sys, json, time, urllib.request, urllib.error

PORT = int(sys.argv[1])
PATHS = ["/login", "/register", "/token", "/upload", "/import", "/xml",
         "/fetch", "/search", "/comment"]
KEEP_HDR = ("server", "content-type", "location", "allow", "x-powered-by")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def post(path, ctype, data):
    url = "http://svc-billing:%d%s" % (PORT, path)
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"User-Agent": "Mozilla/5.0 (recon)",
                                          "Content-Type": ctype})
    opener = urllib.request.build_opener(NoRedirect)
    try:
        r = opener.open(req, timeout=5)
        return {"status": r.status,
                "headers": {k: v for k, v in r.headers.items() if k.lower() in KEEP_HDR},
                "body400": r.read(400).decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        return {"status": e.code,
                "headers": {k: v for k, v in e.headers.items() if k.lower() in KEEP_HDR},
                "body400": e.read(400).decode("utf-8", "replace")}
    except Exception as e:
        return {"status": None, "error": "%s: %s" % (type(e).__name__, e)}

results = []
for p in PATHS:
    ent = {"path": p}
    ent["post_form_t1"] = post(p, "application/x-www-form-urlencoded", b"t=1")
    time.sleep(0.2)
    ent["post_json_t1"] = post(p, "application/json", b'{"t":1}')
    time.sleep(0.2)
    # response diff summary
    a, b = ent["post_form_t1"], ent["post_json_t1"]
    ent["diff"] = {
        "status_differs": a.get("status") != b.get("status"),
        "body_differs": a.get("body400") != b.get("body400"),
        "ctype_differs": a.get("headers", {}).get("Content-Type", "") != b.get("headers", {}).get("Content-Type", ""),
    }
    results.append(ent)

print(json.dumps({"port": PORT, "count": len(results), "results": results},
                 ensure_ascii=False, indent=1))
