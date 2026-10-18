# 出处:人工构造(依据 CWE-639 服务层 get_by_id 直查形态)
def export(record_id):
    record = store.get_by_id(record_id)
    return record.blob if record else None
