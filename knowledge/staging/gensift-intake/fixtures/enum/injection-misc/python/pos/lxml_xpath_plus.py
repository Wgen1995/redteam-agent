# 出处:人工构造(依据 CWE-643 lxml xpath 显式拼接)
nodes = tree.xpath("//order[@id='" + order_id + "']/total")
