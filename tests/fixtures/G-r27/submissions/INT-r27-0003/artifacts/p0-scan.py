#!/usr/bin/env python3
"""Script 0: DNS resolve svc-api-gw + port discovery 8001-8008 (HTTP GET /)."""
import socket, time, json, urllib.request, urllib.error


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


HOST = "svc-api-gw"
result = {"dns": None, "ports": []}

try:
    ip = socket.gethostbyname(HOST)
    result["dns"] = ip
    print(f"[DNS] {HOST} -> {ip}")
except Exception as e:
    result["dns"] = f"ERR:{e}"
    print(f"[DNS] FAILED: {e}")
    print(json.dumps(result))
    raise SystemExit(1)

for port in range(8001, 8009):
    url = f"http://{HOST}:{port}/"
    entry = {"port": port, "status": None, "reason": None, "headers": {}, "body_head": ""}
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "recon/1.0"})
        opener = urllib.request.build_opener(NoRedirect)
        resp = opener.open(req, timeout=5)
        entry["status"] = resp.status
        entry["headers"] = {k.lower(): v for k, v in resp.headers.items() if k.lower() in
                            ("server", "content-type", "location", "x-powered-by", "content-length", "allow", "www-authenticate")}
        entry["body_head"] = resp.read(400).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        entry["status"] = e.code
        entry["headers"] = {k.lower(): v for k, v in e.headers.items() if k.lower() in
                            ("server", "content-type", "location", "x-powered-by", "content-length", "allow", "www-authenticate")}
        try:
            entry["body_head"] = e.read(400).decode("utf-8", "replace")
        except Exception:
            pass
    except Exception as e:
        entry["reason"] = f"{type(e).__name__}:{e}"
    tag = "ALIVE" if entry["status"] is not None else "dead"
    print(f"[PORT] {port} -> {tag} status={entry['status']} reason={entry['reason']}")
    if entry["status"] is not None:
        print(f"       headers={entry['headers']}")
        print(f"       body[:200]={entry['body_head'][:200]!r}")
    result["ports"].append(entry)
    time.sleep(0.25)

alive = [p["port"] for p in result["ports"] if p["status"] is not None]
print(f"[SUMMARY] alive_ports={alive}")
with open("/tmp/p0-result.json", "w") as f:
    json.dump(result, f, indent=1)
