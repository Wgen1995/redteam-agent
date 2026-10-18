// 出处:人工构造(依据 CWE-611 SOAP 附件流再解析形态)
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.soap.SOAPMessage;
import javax.xml.soap.AttachmentPart;

public class AttachmentRouter {
    org.w3c.dom.Document extract(SOAPMessage msg) throws Exception {
        AttachmentPart part = (AttachmentPart) msg.getAttachments().iterator().next();
        DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
        return dbf.newDocumentBuilder().parse(part.getDataHandler().getInputStream());
    }
}
