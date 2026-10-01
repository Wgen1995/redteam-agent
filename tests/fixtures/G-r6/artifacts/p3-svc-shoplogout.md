request:
GET /logout?next=http://evil.example.com HTTP/1.1
Host: svc-shop:8000
User-Agent: tanyin-r6/1.0

response: status=302
headers: {"location": "http://evil.example.com"}
body: <html>GTREDIR-02 synthetic redirect to %s</html>
