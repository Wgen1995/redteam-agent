# 出处:人工构造(依据 CWE-798 硬编码 AWS key)
AWS_ACCESS_KEY_ID = "AKIAJ4RP2V7KZQ3XW8MG"
session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID)
