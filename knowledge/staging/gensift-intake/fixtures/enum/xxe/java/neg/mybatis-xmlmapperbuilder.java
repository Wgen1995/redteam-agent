// 出处:人工构造(硬负例:MyBatis XMLMapperBuilder 大写 XML 前缀,非 Jackson XmlMapper)
org.apache.ibatis.builder.xml.XMLMapperBuilder mb = new org.apache.ibatis.builder.xml.XMLMapperBuilder(in, cfg, resource);
mb.parse();
