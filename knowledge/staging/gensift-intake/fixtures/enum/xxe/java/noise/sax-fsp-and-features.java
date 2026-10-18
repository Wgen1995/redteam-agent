// 出处:人工构造(噪音:同 API 安全用法——FSP+双 external-entities 关,逐版本判值见类页 ⑤)
import javax.xml.XMLConstants;
import javax.xml.parsers.SAXParserFactory;

public final class SecureSax {
    public static void parse(java.io.InputStream in, org.xml.sax.helpers.DefaultHandler h) throws Exception {
        SAXParserFactory spf = SAXParserFactory.newInstance();
        spf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        spf.setFeature("http://xml.org/sax/features/external-general-entities", false);
        spf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        spf.newSAXParser().parse(in, h);
    }
}
