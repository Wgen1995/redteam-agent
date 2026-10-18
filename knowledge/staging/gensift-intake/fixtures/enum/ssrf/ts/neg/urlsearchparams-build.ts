// 出处:人工构造(硬负例:仅构造查询串)
const qs = new URLSearchParams({ q: term, page: String(pageNo) }).toString();
return `/search?${qs}`;
