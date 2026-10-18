// 出处:人工构造(噪音:同 API 安全用法——disallow-doctype-decl 全禁,允许命中由五步判别)
import javax.xml.parsers.DocumentBuilderFactory;

public final class SecureDom {
    public static org.w3c.dom.Document parse(java.io.InputStream in) throws Exception {
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        return dbf.newDocumentBuilder().parse(in);
    }
}
