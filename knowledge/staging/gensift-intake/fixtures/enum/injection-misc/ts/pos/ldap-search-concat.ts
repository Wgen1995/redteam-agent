// 出处:人工构造(依据 CWE-90 ldapjs client.search 拼接 filter)
const { search } = await client.search(baseDn, { scope: "sub", filter: `(&(uid=${uid})(objectClass=person))` });
