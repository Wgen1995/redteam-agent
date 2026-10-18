// 出处:人工构造(噪音:FP 卡形态——只解析服务端常量,需来源证据;命中登记)
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.StringReader;
import org.xml.sax.InputSource;

public final class InternalOnly {
    private static final String MAPPING_XML = "<mappings><rule id=\"1\"/></mappings>";
    public static org.w3c.dom.Document loadBuiltins() throws Exception {
        return DocumentBuilderFactory.newInstance().newDocumentBuilder()
                .parse(new InputSource(new StringReader(MAPPING_XML)));
    }
}
