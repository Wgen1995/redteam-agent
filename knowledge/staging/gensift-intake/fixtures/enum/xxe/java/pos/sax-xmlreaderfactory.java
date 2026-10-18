// 出处:人工构造(依据 CWE-611 SAX XMLReader 直构形态)
import org.xml.sax.XMLReader;
import org.xml.sax.helpers.XMLReaderFactory;

public class LegacySaxEndpoint {
    void handle(java.io.InputSource src) throws Exception {
        XMLReader xr = XMLReaderFactory.createXMLReader();
        xr.setContentHandler(new org.xml.sax.helpers.DefaultHandler());
        xr.parse(src);
    }
}
