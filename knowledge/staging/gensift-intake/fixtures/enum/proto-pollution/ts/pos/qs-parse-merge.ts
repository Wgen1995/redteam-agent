// 出处:人工构造(依据 qs 展开 ?a[__proto__][b]=c 后 merge 形态)
import * as qs from "qs";
import * as _ from "lodash";
const parsed = qs.parse(req.query);
_.merge(options, parsed);
