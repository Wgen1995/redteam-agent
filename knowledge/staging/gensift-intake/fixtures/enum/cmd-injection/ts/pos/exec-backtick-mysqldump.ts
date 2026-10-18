// 出处:人工构造(模板字符串拼接重定向)
exec(`mysqldump -u root ${dbName} > /tmp/${dbName}.sql`);
