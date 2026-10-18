// 出处:人工构造(依据 CWE-611 JAXB 未硬化 unmarshal 形态)
import javax.xml.bind.JAXBContext;
import javax.xml.bind.Unmarshaller;

public class OrderApi {
    Object toOrder(java.io.InputStream body) throws Exception {
        JAXBContext ctx = JAXBContext.newInstance(Order.class);
        Unmarshaller u = ctx.createUnmarshaller();
        return u.unmarshal(body);
    }
}
