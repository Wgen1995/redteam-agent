# 出处:人工构造(噪音:常量目标)
@app.get("/login")
def login_page():
    return RedirectResponse(url="/login")
