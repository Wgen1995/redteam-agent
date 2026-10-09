#!/usr/bin/env python3
# INT-r27-0001-3: HTTP GET / on every live (ip,port). No redirect follow, timeout 5s.
import json, urllib.request, urllib.error

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)
opener.addheaders = [("User-Agent", "tanyin-recon/1.0")]

live = json.load(open("/tmp/int-r27-live.json"))["live_pairs"]
probes = []
for ip, port in live:
    url = "http://%s:%d/" % (ip, port)
    rec = {"ip": ip, "port": port, "url": url}
    try:
        r = opener.open(url, timeout=5)
        body = r.read(300).decode("utf-8", "replace")
        rec.update({"status": r.status, "server": r.headers.get("Server"),
                    "location": r.headers.get("Location"),
                    "content_type": r.headers.get("Content-Type"),
                    "body_head": body, "error": None})
    except urllib.error.HTTPError as e:
        body = e.read(300).decode("utf-8", "replace")
        rec.update({"status": e.code, "server": e.headers.get("Server"),
                    "location": e.headers.get("Location"),
                    "content_type": e.headers.get("Content-Type"),
                    "body_head": body, "error": None})
    except Exception as e:
        rec.update({"status": None, "server": None, "location": None,
                    "content_type": None, "body_head": None, "error": repr(e)})
    probes.append(rec)

result = {"script": "INT-r27-0001-3", "ts": "2026-10-23T15:32:00Z", "http": probes}
with open("/tmp/int-r27-http.json", "w") as f:
    json.dump(result, f)
print(json.dumps(result, ensure_ascii=False, indent=1))
