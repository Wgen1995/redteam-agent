# 出处:人工构造(依据 CWE-1321 类似形态——递归合并不滤键)
def deep_merge(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if isinstance(value, dict):
            base[key] = deep_merge(base.get(key, {}), value)
        else:
            base[key] = value
    return base

config = deep_merge(defaults, request.json)
