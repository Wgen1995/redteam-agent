# 出处:人工构造(硬负例:bind 认证而非 filter 检索)
from ldap3 import Server, Connection
server = Server("dir.example", use_ssl=True)
conn = Connection(server, user=f"uid={uid},ou=people,dc=example", password=password)
conn.bind()
