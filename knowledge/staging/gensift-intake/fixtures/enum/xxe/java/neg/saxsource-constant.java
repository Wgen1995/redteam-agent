// 出处:人工构造(硬负例:SAXSource 构造常量载荷,无 parse 调用)
javax.xml.transform.sax.SAXSource src = new javax.xml.transform.sax.SAXSource(new org.xml.sax.InputSource(new java.io.StringReader(FEED_TEMPLATE)));
