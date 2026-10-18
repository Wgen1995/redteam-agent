// 出处:人工构造(硬负例:固定类型 JAXB 解析)
Shipment s = jaxbContext.createUnmarshaller().unmarshal(new StreamSource(xml), Shipment.class).getValue();
