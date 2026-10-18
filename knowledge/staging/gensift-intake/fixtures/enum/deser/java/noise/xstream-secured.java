// 出处:人工构造(噪音:XStream security framework 配置后仍用同一 API——允许命中)
XStream xstream = new XStream();
XStream.setupDefaultSecurity(xstream);
xstream.allowTypes(new Class[] { SessionState.class });
Object o = xstream.fromXML(savedXml);
