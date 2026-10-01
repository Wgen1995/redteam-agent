control request:
POST /login HTTP/1.1
Host: svc-login:8000
User-Agent: tanyin-r6/1.0
Content-Type: application/x-www-form-urlencoded
Content-Length: 17

username=zz&pw=zz

response: status=403
body: <html>denied</html>
