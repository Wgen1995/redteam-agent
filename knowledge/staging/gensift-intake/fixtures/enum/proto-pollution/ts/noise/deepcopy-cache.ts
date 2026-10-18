// 出处:人工构造(噪音:深拷贝作快照无用户键回写——允许命中)
const snapshot = deepCopy(cacheState);
auditTrail.push(snapshot);
