# selftest 样本: Flask/FastAPI 装饰器入口（P-SRC01/P-SRC02/P-SRC03 预期命中）
@app.route("/orders", methods=["POST"])
def create_order():
    return repo.save()

@app.get("/items")
def list_items():
    return repo.all()

@app.post("/items")
def make_item():
    return repo.new()
