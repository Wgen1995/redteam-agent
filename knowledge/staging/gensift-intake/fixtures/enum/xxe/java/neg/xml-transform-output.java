// 出处:人工构造(硬负例:XML 输出方向——transform 写文件)
javax.xml.transform.Transformer t = javax.xml.transform.TransformerFactory.newInstance().newTransformer();
t.transform(new javax.xml.transform.dom.DOMSource(doc), new javax.xml.transform.stream.StreamResult(out));
