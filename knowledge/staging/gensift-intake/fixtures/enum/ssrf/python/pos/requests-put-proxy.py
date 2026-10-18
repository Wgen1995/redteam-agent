# 出处:人工构造(依据 CWE-918 requests put/etcd 代理形态)
def write_key(scheme, host, key, value):
    r = requests.put(f"{scheme}://{host}:2379/v2/keys/{key}", data=value.encode())
    return r.json()
