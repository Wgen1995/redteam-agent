// 出处:人工构造(硬负例:DOM 构建方向——builder.newDocument() 非 newDocumentBuilder())
org.w3c.dom.Document fresh = builder.newDocument();
fresh.appendChild(fresh.createElement("rows"));
