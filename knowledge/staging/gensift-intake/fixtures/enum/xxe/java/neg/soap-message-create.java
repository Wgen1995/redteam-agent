// 出处:人工构造(硬负例:SOAP 消息构造方向)
javax.xml.soap.SOAPMessage msg = javax.xml.soap.MessageFactory.newInstance().createMessage();
msg.setProperty(javax.xml.soap.SOAPMessage.WRITE_XML_DECLARATION, Boolean.TRUE);
