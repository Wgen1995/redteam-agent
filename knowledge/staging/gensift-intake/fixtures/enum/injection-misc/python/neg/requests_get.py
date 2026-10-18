# 出处:人工构造(硬负例:外呼)
resp = requests.get(f"{api_base}/items/{quote(sku)}", timeout=3)
