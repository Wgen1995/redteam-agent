// 出处:人工构造(依据 CWE-643 xpath 包 evaluate 拼接)
import * as xpath from "xpath";
const result = xpath.evaluate("//order[@id='" + orderId + "']", doc, null, xpath.XPathResult.STRING_TYPE);
