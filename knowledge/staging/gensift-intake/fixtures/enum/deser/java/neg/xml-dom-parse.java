// 出处:人工构造(硬负例:DOM 解析属 XXE 类非对象反序列化)
Document doc = builder.parse(new InputSource(new StringReader(xml)));
