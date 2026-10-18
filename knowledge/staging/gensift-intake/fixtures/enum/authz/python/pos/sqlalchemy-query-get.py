# 出处:人工构造(依据 CWE-639 SQLAlchemy query.get 按 id 直查形态)
def view(user_id):
    user = session.query(User).get(user_id)
    return serialize(user)
