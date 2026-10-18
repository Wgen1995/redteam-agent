// 出处:人工构造(依据 CWE-1321 constructor["prototype"] 双跳绕过键黑名单)
const obj: any = {};
obj["constructor"]["prototype"]["role"] = "admin";
obj["constructor"]["prototype"]["trusted"] = true;
