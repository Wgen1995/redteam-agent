// 出处:人工构造(噪音:同 API 安全用法——硬化 SAXSource 注入 unmarshal)
import javax.xml.bind.JAXBContext;
import javax.xml.bind.Unmarshaller;
import javax.xml.parsers.SAXParserFactory;
import javax.xml.transform.sax.SAXSource;

public final class SecureJaxb {
    public static Object to(java.io.InputStream in, Class<?> type) throws Exception {
        SAXParserFactory spf = SAXParserFactory.newInstance();
        spf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        SAXSource src = new SAXSource(spf.newSAXParser().getXMLReader(), new org.xml.sax.InputSource(in));
        Unmarshaller u = JAXBContext.newInstance(type).createUnmarshaller();
        return u.unmarshal(src);
    }
}
