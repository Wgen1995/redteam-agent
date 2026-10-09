#!/usr/bin/env python3
"""INT-r27-0009 script 0: DNS resolve svc-files + HTTP GET / on ports 8001-8008.
No redirect following, timeout 5s, >=0.2s interval. Discovery only."""
import socket, json, time, urllib.request, urllib.error

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)
result = {"dns": {}, "ports": []}

try:
    infos = socket.getaddrinfo("svc-files", None)
    addrs = sorted({i[4][0] for i in infos})
    result["dns"] = {"svc-files": addrs}
except Exception as e:
    result["dns"] = {"svc-files": {"error": repr(e)}}

for port in range(8001, 8009):
    url = f"http://svc-files:{port}/"
    entry = {"port": port, "url": url}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "recon-int-r27/1.0"})
        resp = opener.open(req, timeout=5)
        body = resp.read(600)
        entry.update({
            "status": resp.status,
            "headers": {k.lower(): v for k, v in resp.headers.items()
                        if k.lower() in ("content-type", "content-length", "location",
                                          "server", "x-powered-by", "www-authenticate",
                                          "allow", "set-cookie")},
            "body_head": body[:400].decode("utf-8", "replace"),
        })
    except urllib.error.HTTPError as e:
        body = e.read(600)
        entry.update({
            "status": e.code,
            "headers": {k.lower(): v for k, v in e.headers.items()
                        if k.lower() in ("content-type", "content-length", "location",
                                          "server", "x-powered-by", "www-authenticate",
                                          "allow", "set-cookie")},
            "body_head": body[:400].decode("utf-8", "replace"),
        })
    except Exception as e:
        entry["error"] = repr(e)
    result["ports"].append(entry)
    time.sleep(0.25)

print(json.dumps(result, ensure_ascii=False, indent=1))
