# 出处:人工构造(硬负例:本地路径拼接)
target = (Path(base_dir) / user_name).resolve()
if not str(target).startswith(base_dir):
    raise PermissionError("traversal")
