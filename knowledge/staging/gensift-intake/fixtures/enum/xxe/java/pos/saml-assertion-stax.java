// 出处:人工构造(依据 CWE-611 SAML assertion 解析形态——IdP 来源不可信)
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamReader;
import java.io.ByteArrayInputStream;
import java.util.Base64;

public class SamlConsumer {
    void consume(String b64Response) throws Exception {
        byte[] raw = Base64.getDecoder().decode(b64Response);
        XMLInputFactory factory = XMLInputFactory.newInstance();
        XMLStreamReader r = factory.createXMLStreamReader(new ByteArrayInputStream(raw));
        while (r.hasNext()) r.next();
    }
}
