# 出处:人工构造(硬负例:自动转义显式开启)
from jinja2 import Environment
env = Environment(autoescape=True)
