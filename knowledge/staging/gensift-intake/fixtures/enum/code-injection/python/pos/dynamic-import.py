# 出处:人工构造(依据 CWE-94 动态导入执行)
mod = __import__(request.args["module"])
mod.run()
