// 出处:人工构造(依据 CWE-611 JDOM SAXBuilder 默认形态)
import org.jdom2.input.SAXBuilder;

public class RuleLoader {
    org.jdom2.Document build(java.io.InputStream in) throws Exception {
        SAXBuilder sb = new SAXBuilder();
        return sb.build(in);
    }
}
