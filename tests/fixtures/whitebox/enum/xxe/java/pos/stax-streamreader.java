// 出处:人工构造(依据 CWE-611 + OWASP XXE Cheatsheet StAX 形态)
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamReader;

public class StreamParser {
    void consume(java.io.InputStream body) throws Exception {
        XMLInputFactory xif = XMLInputFactory.newInstance();
        XMLStreamReader reader = xif.createXMLStreamReader(body);
        while (reader.hasNext()) reader.next();
    }
}
