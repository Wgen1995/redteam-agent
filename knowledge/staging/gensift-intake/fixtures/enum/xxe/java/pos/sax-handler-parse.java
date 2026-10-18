// 出处:人工构造(依据 CWE-611 + OWASP XXE Cheatsheet SAX 形态)
import javax.xml.parsers.SAXParserFactory;
import org.xml.sax.helpers.DefaultHandler;

public class SaxImporter {
    public void importFeed(java.io.InputStream in) throws Exception {
        SAXParserFactory factory = SAXParserFactory.newInstance();
        factory.newSAXParser().parse(in, new DefaultHandler());
    }
}
