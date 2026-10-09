#!/usr/bin/env python3
# INT-r27-0002 script0: DNS resolve svc-shop + port liveness 8001-8008 (HTTP GET /)
import json, socket, urllib.request, urllib.error, time

HOST = "svc-shop"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(NoRedirect)

result = {"host": HOST, "dns": None, "ports": []}

try:
    infos = socket.getaddrinfo(HOST, None)
    addrs = sorted(set(i[4][0] for i in infos))
    result["dns"] = {"addrs": addrs}
except Exception as e:
    result["dns"] = {"error": f"{type(e).__name__}: {e}"}

for port in range(8001, 8009):
    url = f"http://{HOST}:{port}/"
    entry = {"port": port, "url": url}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "r27-recon/1.0"})
        resp = opener.open(req, timeout=5)
        body = resp.read(2048)
        entry.update({
            "status": resp.status,
            "reason": getattr(resp, "reason", ""),
            "headers": {k: v for k, v in resp.headers.items()},
            "body_head": body.decode("utf-8", "replace")[:400],
        })
    except urllib.error.HTTPError as e:
        try:
            body = e.read(2048).decode("utf-8", "replace")[:400]
        except Exception:
            body = ""
        entry.update({
            "status": e.code,
            "reason": str(e.reason),
            "headers": {k: v for k, v in e.headers.items()},
            "body_head": body,
        })
    except Exception as e:
        entry.update({"error": f"{type(e).__name__}: {e}"})
    result["ports"].append(entry)
    time.sleep(0.2)

print(json.dumps(result, ensure_ascii=False, indent=1))
