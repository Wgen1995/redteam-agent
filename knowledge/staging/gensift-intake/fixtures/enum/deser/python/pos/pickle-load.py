# 出处:人工构造(依据 CWE-502 pickle.load 文件流形态)
with open(session_path, "rb") as f:
    state = pickle.load(f)
