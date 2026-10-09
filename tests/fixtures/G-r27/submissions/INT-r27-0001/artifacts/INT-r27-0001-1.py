#!/usr/bin/env python3
# INT-r27-0001-1: DNS resolution of 8 svc names (authorized range 172.28.0.0/24)
import socket, json

NAMES = ["svc-shop", "svc-api-gw", "svc-admin", "svc-login",
         "svc-billing", "svc-dashboard", "svc-portal", "svc-files"]

out = {}
for n in NAMES:
    try:
        infos = socket.getaddrinfo(n, None, socket.AF_INET, socket.SOCK_STREAM)
        ips = sorted({i[4][0] for i in infos})
        out[n] = {"ips": ips, "error": None}
    except Exception as e:
        out[n] = {"ips": [], "error": repr(e)}

result = {"script": "INT-r27-0001-1", "ts": "2026-10-23T15:30:00Z", "dns": out}
with open("/tmp/int-r27-dns.json", "w") as f:
    json.dump(result, f)
print(json.dumps(result, ensure_ascii=False, indent=1))
