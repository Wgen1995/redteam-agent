request:
GET /search?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E HTTP/1.1
Host: svc-shop:8000
User-Agent: tanyin-r6/1.0

response: status=200
headers: {}
body: <html>search results %3Cscript%3Ealert(1)%3C/script%3E GTXSS-01 synthetic reflected xss</html>
