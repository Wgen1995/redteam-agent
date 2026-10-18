// 出处:人工构造(依据 CWE-611 Jackson XmlMapper/Woodstox 未配置形态)
import com.fasterxml.jackson.dataformat.xml.XmlMapper;

public class SoapLite {
    Object read(String xmlBody) throws Exception {
        XmlMapper mapper = new XmlMapper();
        return mapper.readValue(xmlBody, java.util.Map.class);
    }
}
