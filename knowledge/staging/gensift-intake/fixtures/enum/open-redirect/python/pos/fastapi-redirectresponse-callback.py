# 出处:人工构造(依据 CWE-601 OAuth 回调 relay 目标可控)
@app.get("/oauth/callback")
def callback(state: str):
    relay = oauth.decode_relay(state)
    return RedirectResponse(url=relay)
