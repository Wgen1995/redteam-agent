# 出处:人工构造(依据 CWE-434 + OWASP File Upload Cheatsheet Django 原名落盘)
from django.http import HttpRequest

def upload(request: HttpRequest):
    f = request.FILES['file']
    name = f.name
    with open('/var/www/media/' + name, 'wb') as out:
        for chunk in f.chunks():
            out.write(chunk)
    return name
