# selftest 阴性核对样本: os.environ 是配置读取不算入口——任何 source pattern 不应命中本文件
import os

DB_HOST = os.environ.get("DB_HOST", "localhost")
FEATURE_FLAG = os.environ["FEATURE_FLAG"]
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
