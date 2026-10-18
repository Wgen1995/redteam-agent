// 出处:CVE-2017-18349(fastjson autoType 已知可利用形态)
Object o = JSON.parseObject(body, Feature.SupportAutoType);
