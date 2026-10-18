// 出处:人工构造(依据 CWE-611 + CVE-2020-10683 dom4j parseText/read 家族形态)
import org.dom4j.io.SAXReader;

public class ConfigLoader {
    org.dom4j.Document load(java.io.InputStream in) throws Exception {
        SAXReader reader = new SAXReader();
        return reader.read(in);
    }
}
