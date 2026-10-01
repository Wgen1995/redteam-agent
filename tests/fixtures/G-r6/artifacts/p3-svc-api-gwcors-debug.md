request:
GET /cors-debug HTTP/1.1
Host: svc-api-gw:8000
User-Agent: tanyin-r6/1.0
Origin: http://evil.example.com

response: status=200
headers: {"access-control-allow-origin": "*"}
body: <html>cors debug GTCORS-01 wildcard allow-origin</html>
