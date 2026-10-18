# 出处:人工构造(硬负例:正则校验)
import re
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
def valid_recipient(email: str) -> bool:
    return bool(EMAIL_RE.match(email))
