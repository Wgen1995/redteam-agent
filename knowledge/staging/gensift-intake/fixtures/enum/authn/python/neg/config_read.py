# 出处:人工构造(硬负例:配置读取)
import os
BILLING_ENDPOINT = os.environ.get("BILLING_ENDPOINT", "https://billing.internal")
TIMEOUT = int(os.environ.get("BILLING_TIMEOUT", "5"))
