# 出处:人工构造(依据 CWE-601 web.py Redirect 异常携带用户目标)
class JumpPage:
    def GET(self):
        target = web.input(url="/")["url"]
        raise Redirect(target)
