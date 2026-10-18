// 出处:人工构造(噪音:固定 filter——允许命中)
await client.search(baseDn, { scope: "sub", filter: "(objectClass=person)" });
