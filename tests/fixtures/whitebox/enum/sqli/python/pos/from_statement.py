# 出处:人工构造(CWE-89 from_statement)
q = session.query(User).from_statement("SELECT * FROM u WHERE x = '" + x + "'")
