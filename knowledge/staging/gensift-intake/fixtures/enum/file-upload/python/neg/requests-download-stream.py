# 出处:人工构造(硬负例:外发拉取)
resp = requests.get(manifest_url, timeout=5)
etag = resp.headers.get('ETag')
