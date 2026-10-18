// 出处:人工构造(硬负例:已解析 doc 的导航,非解析点)
org.w3c.dom.NodeList items = doc.getElementsByTagName("item");
String first = items.item(0).getTextContent();
