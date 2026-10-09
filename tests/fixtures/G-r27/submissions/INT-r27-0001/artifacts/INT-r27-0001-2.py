#!/usr/bin/env python3
# INT-r27-0001-2: TCP port probe. Focused 8000-8009 on DNS-resolved IPs,
# plus full 172.28.0.0/24 sweep on 8001-8008. timeout 0.3s, concurrency <= 16.
import socket, json, os
from concurrent.futures import ThreadPoolExecutor

def connect_scan(t):
    ip, port = t
    try:
        s = socket.create_connection((ip, port), timeout=0.3)
        s.close()
        return True
    except Exception:
        return False

dns = {}
if os.path.exists("/tmp/int-r27-dns.json"):
    dns = json.load(open("/tmp/int-r27-dns.json")).get("dns", {})

ip_to_names = {}
for n, rec in dns.items():
    for ip in rec.get("ips", []):
        ip_to_names.setdefault(ip, []).append(n)

tasks = []
for ip in ip_to_names:                      # focused: resolved IPs x 8000-8009
    for port in range(8000, 8010):
        tasks.append((ip, port))
for i in range(1, 255):                     # sweep: whole subnet x 8001-8008
    ip = "172.28.0.%d" % i
    for port in range(8001, 8009):
        tasks.append((ip, port))

live = []
with ThreadPoolExecutor(max_workers=16) as ex:
    for t, ok in zip(tasks, ex.map(connect_scan, tasks)):
        if ok:
            live.append(list(t))

focused_only = sorted([p for p in live if p[1] in (8000, 8009)])
result = {"script": "INT-r27-0001-2", "ts": "2026-10-23T15:31:00Z",
          "attempted_connections": len(tasks),
          "resolved_ip_names": ip_to_names,
          "live_pairs": sorted(live),
          "focused_edge_ports_open": focused_only}
with open("/tmp/int-r27-live.json", "w") as f:
    json.dump(result, f)
print(json.dumps(result, ensure_ascii=False, indent=1))
