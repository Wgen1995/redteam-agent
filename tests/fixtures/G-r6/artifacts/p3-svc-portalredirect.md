request:
GET /redirect?url=http://evil.example.com HTTP/1.1
Host: svc-portal:8000
User-Agent: tanyin-r6/1.0

response: status=302
headers: {"location": "/redirect?url=http://evil.example.com"}
body: <html>GTREDIR-01 synthetic redirect to %s</html>
