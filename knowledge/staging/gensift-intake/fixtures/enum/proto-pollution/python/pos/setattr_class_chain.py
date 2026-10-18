# 出处:人工构造(依据 class pollution __class__ 链写)
def poke(obj, key, value):
    setattr(obj.__class__, key, value)
