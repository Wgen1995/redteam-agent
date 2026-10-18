// 出处:人工构造(硬负例:DB execute 属 sqli 域)
await db.execute('SELECT * FROM t WHERE id = ?', [userId]);
