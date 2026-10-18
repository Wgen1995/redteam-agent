# 出处:人工构造(依据 CWE-639 filter_by 键形谓词无属主列形态)
def resolve(token):
    api_key = session.query(ApiKey).filter_by(token=token).one()
    return api_key
