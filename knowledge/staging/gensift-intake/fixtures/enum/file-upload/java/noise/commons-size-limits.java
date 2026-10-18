// 出处:人工构造(噪音:同 API 安全用法——commons 配额 + 服务端名;允许命中)
import org.apache.commons.fileupload.servlet.ServletFileUpload;
import org.apache.commons.fileupload.disk.DiskFileItemFactory;

public class SafeCommonsServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        DiskFileItemFactory factory = new DiskFileItemFactory();
        ServletFileUpload upload = new ServletFileUpload(factory);
        upload.setSizeMax(2_097_152L);
        upload.setFileSizeMax(1_048_576L);
        for (org.apache.commons.fileupload.FileItem item : upload.parseRequest(req)) {
            item.write(new java.io.File(TMP, java.util.UUID.randomUUID() + ".dat"));
        }
    }
}
