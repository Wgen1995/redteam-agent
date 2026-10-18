# 出处:人工构造(依据 CWE-601 redirect_to 参数族标记——returnTo 家族)
class ShortLinkRedirect(tornado.web.RequestHandler):
    def initialize(self):
        self.redirect_to = self.get_argument("to", "/")
    def get(self):
        self.redirect(self.redirect_to)
