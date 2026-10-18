# 出处:人工构造(依据 CWE-79 显式关闭自动转义)
from jinja2 import Environment
env = Environment(autoescape=False)
return env.from_string(user_html).render()
