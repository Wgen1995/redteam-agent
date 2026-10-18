// 出处:人工构造(噪音:同 API 安全用法——dom4j SAXReader 关 doctype)
import org.dom4j.io.SAXReader;

public final class SecureDom4j {
    public static org.dom4j.Document read(java.io.InputStream in) throws Exception {
        SAXReader reader = new SAXReader();
        reader.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        return reader.read(in);
    }
}
