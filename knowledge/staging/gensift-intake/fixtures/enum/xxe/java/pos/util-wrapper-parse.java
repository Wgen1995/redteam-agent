// 出处:人工构造(依据 CWE-611 工具类封装形态——读点离入口三层)
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.StringReader;
import org.xml.sax.InputSource;

public final class XmlUtils {
    public static org.w3c.dom.Document parse(String raw) throws Exception {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        return dbf.newDocumentBuilder().parse(new InputSource(new StringReader(raw)));
    }
}
