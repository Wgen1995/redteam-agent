# 出处:人工构造(噪音:键白名单后 setattr——允许命中)
for key in payload:
    if key in ALLOWED_FIELDS:
        setattr(profile, key, payload[key])
