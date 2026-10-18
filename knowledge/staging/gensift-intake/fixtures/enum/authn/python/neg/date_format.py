# 出处:人工构造(硬负例:日期格式化)
from datetime import datetime
def fmt_deadline(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")
