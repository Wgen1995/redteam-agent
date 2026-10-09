#!/usr/bin/env python3
# INT-r27-0017 GraphQL introspection via GET query param (GET-only target, POST unavailable)
# payloads: __schema types, __type(name:"Query") fields, {dummy} data-plane probe, no-param control
import http.client, time, json, urllib.parse

HOST, PORT = "svc-api-gw", 8002

QUERIES = [
    ("introspect_schema", '{__schema{types{name}}}'),
    ("introspect_type",   '{__type(name:"Query"){fields{name}}}'),
    ("data_probe_dummy",  '{dummy}'),
    ("control_noparam",   None),
]

def raw_request(path):
    return ("GET %s HTTP/1.1\r\nHost: %s:%d\r\nUser-Agent: w2-probe/1.0\r\n"
            "Accept: */*\r\nConnection: close\r\n\r\n" % (path, HOST, PORT))

def fetch(path):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=8)
    try:
        conn.request("GET", path, headers={"User-Agent": "w2-probe/1.0",
                                           "Accept": "*/*", "Connection": "close"})
        r = conn.getresponse()
        body = r.read(4096)
        return {"status": r.status, "reason": r.reason,
                "headers": {k.lower(): v for k, v in r.getheaders()},
                "body_excerpt": body.decode("utf-8", "replace")[:600]}
    finally:
        conn.close()

results = []
for name, q in QUERIES:
    path = "/graphql" if q is None else "/graphql?query=" + urllib.parse.quote(q, safe="")
    rec = {"probe": name, "query_literal": q, "path": path, "raw_request": raw_request(path)}
    try:
        resp = fetch(path)
        if resp["status"] == 429:
            time.sleep(3.0)
            resp = fetch(path)
            resp["note"] = "429-backoff-retry-3s"
    except Exception as e:
        resp = {"status": None, "error": repr(e)}
    rec["resp"] = resp
    body = resp.get("body_excerpt", "")
    rec["signals"] = {"has_types_array": '"types"' in body or "'types'" in body,
                      "has_fields": '"fields"' in body or "'fields'" in body,
                      "has_schema_kw": "__schema" in body or "schema" in body.lower(),
                      "has_errors_kw": "error" in body.lower(),
                      "has_data_kw": '"data"' in body}
    results.append(rec)
    print(json.dumps({"probe": name, "status": resp.get("status"),
                      "body": resp.get("body_excerpt", "")[:200]}, ensure_ascii=False))
    time.sleep(0.3)

out = {"script": "w2_gwc_graphql", "ts": "2026-10-23T16:00:00Z",
       "target": "%s:%d" % (HOST, PORT), "requests": len(results), "results": results}
with open("/tmp/w2_gwc_graphql.json", "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("DONE requests=%d" % len(results))
