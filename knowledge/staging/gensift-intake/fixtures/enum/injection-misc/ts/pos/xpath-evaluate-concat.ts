// 出处:人工构造(依据 CWE-643 XPathEvaluator 拼接)
const evaluator = new XPathEvaluator();
const res = evaluator.evaluate("//order[@id='" + orderId + "']", doc, null, XPathResult.FIRST_ORDERED_NODE_TYPE);
