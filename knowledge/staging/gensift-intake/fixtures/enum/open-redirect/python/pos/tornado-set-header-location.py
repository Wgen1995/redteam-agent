# 出处:人工构造(依据 CWE-601 tornado 响应头直写跳转)
class GoHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Location", self.get_query_argument("to"))
        self.set_status(302)
