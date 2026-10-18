# 出处:人工构造(依据 CWE-287 验证码无次数上限+弱熵源)
import random
def send_code(phone):
    code = random.randint(100000, 999999)
    cache.set(f"code:{phone}", code, timeout=None)
def verify_code(phone, code):
    return cache.get(f"code:{phone}") == code
