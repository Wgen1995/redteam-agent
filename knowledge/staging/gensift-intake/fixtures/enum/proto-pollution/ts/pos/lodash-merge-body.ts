// 出处:人工构造(依据 CVE-2019-10744 lodash.merge 污染形态)
import * as _ from "lodash";
export function applyOverride(config: AppConfig) {
  return _.merge(config, req.body);
}
