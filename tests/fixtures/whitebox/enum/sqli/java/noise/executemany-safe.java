// 出处:人工构造(噪音:executemany 参数化)
cur.executemany("INSERT INTO t VALUES (?)", rows);
