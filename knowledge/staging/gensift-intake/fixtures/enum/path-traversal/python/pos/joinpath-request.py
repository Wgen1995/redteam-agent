# 出处:人工构造(依据 CWE-22 pathlib joinpath 形态)
rel = request.args.get('rel')
p = Path(CACHE_ROOT).joinpath(rel)
return p.read_bytes()
