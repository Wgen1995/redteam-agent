# 出处:人工构造(噪音:TOTP 窗口+限次)
import pyotp
def verify_mfa(secret, code, phone):
    if attempts.exceeded(phone):
        raise TooManyAttempts
    return pyotp.TOTP(secret).verify(code, valid_window=1)
