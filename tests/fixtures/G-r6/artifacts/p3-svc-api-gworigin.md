request:
GET /origin HTTP/1.1
Host: svc-api-gw:8000
User-Agent: tanyin-r6/1.0
Origin: http://evil.example.com

response: status=200
headers: {"access-control-allow-origin": "http://evil.example.com", "access-control-allow-credentials": "true"}
body: <html>origin GTCORS-02 reflected http://evil.example.com allow-credentials true</html>
