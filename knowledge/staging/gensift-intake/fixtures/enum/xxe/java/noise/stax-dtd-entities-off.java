// 出处:人工构造(噪音:同 API 安全用法——SUPPORT_DTD 与外部实体双关)
import javax.xml.stream.XMLInputFactory;

public final class SecureStax {
    public static javax.xml.stream.XMLStreamReader read(java.io.InputStream in) throws Exception {
        XMLInputFactory xif = XMLInputFactory.newInstance();
        xif.setProperty(XMLInputFactory.SUPPORT_DTD, Boolean.FALSE);
        xif.setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, Boolean.FALSE);
        return xif.createXMLStreamReader(in);
    }
}
