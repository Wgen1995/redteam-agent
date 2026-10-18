// 出处:人工构造(硬负例:数组流式聚合无按键取对象)
const active = users.filter((u) => u.enabled).map((u) => u.primaryEmail);
