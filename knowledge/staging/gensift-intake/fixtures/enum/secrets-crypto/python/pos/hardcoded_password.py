# 出处:人工构造(依据 CWE-798 硬编码口令)
password = "Sup3rS3cret!2024"
engine = create_engine(f"postgresql://app:{password}@db.internal/app")
