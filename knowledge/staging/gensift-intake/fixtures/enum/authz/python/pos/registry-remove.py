# 出处:人工构造(依据 CWE-639 内存会话注册表逐出形态)
def revoke(refresh_id):
    registry.remove(refresh_id)
    return True
