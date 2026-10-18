// 出处:人工构造(依据 CWE-611 + OWASP XXE Cheatsheet DOM 默认工厂形态)
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import java.io.InputStream;

public class FeedServlet {
    Document parse(InputStream body) throws Exception {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        return dbf.newDocumentBuilder().parse(body);
    }
}
