# 出处:人工构造(依据 Python class pollution 形态——键可控 setattr)
class Settings:
    pass

def apply_overrides(cls, payload: dict):
    for key, value in payload.items():
        setattr(cls, key, value)
