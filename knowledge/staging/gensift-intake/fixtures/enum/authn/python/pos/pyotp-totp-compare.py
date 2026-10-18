# 出处:人工构造(依据 CWE-287 TOTP 自比对,无窗口与限次)
import pyotp
def verify_mfa(secret, code):
    return pyotp.TOTP(secret).now() == code
