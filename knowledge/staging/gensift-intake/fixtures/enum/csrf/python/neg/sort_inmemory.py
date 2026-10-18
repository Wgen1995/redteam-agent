# 出处:人工构造(硬负例:内存排序)
def rank_orders(orders: list[dict]) -> list[dict]:
    return sorted(orders, key=lambda o: o["total"], reverse=True)
