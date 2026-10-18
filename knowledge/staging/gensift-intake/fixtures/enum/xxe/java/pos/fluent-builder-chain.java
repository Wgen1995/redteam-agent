// 出处:人工构造(依据 CWE-611 单行 fluent 链——零配置直达读点)
import javax.xml.parsers.DocumentBuilderFactory;

public class Inline {
    org.w3c.dom.Document go(java.io.InputStream in) throws Exception {
        return DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(in);
    }
}
