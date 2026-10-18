# 出处:人工构造(依据 Python class pollution __dict__ 直写)
def merge_profile(target, payload: dict):
    target.__dict__.update(payload)
    return target
