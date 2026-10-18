// 出处:CVE-2013-7285(XStream fromXML 已知可利用形态)
XStream xstream = new XStream();
Object o = xstream.fromXML(request.getParameter("xml"));
