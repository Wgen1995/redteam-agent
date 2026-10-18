// 出处:人工构造(依据 CWE-611 二阶——XML 字段入库回读再解析/persisted_read)
import javax.xml.parsers.DocumentBuilderFactory;
import java.sql.ResultSet;

public class NightlyXmlJob {
    org.w3c.dom.Document rebuild(java.sql.Connection c) throws Exception {
        ResultSet rs = c.createStatement().executeQuery("SELECT payload FROM audit_xml");
        rs.next();
        String stored = rs.getString(1);
        return DocumentBuilderFactory.newInstance().newDocumentBuilder()
                .parse(new org.xml.sax.InputSource(new java.io.StringReader(stored)));
    }
}
