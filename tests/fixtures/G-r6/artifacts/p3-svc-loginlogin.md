request:
POST /login HTTP/1.1
Host: svc-login:8000
User-Agent: tanyin-r6/1.0
Content-Type: application/x-www-form-urlencoded
Content-Length: 23

username=admin&pw=wrong

response: status=403
headers: {}
body: <html>denied GTRATE-01 synthetic no rate limit after 17 attempts</html>
