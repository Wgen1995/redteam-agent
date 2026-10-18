# 出处:人工构造(硬负例:env 取值)
password = os.environ["DB_PASSWORD"]
engine = create_engine(url, connect_args={"password": password})
