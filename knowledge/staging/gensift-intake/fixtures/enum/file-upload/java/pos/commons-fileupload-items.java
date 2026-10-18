// 出处:人工构造(依据 CWE-434 commons-fileupload parseRequest 形态)
import org.apache.commons.fileupload.servlet.ServletFileUpload;
import org.apache.commons.fileupload.disk.DiskFileItemFactory;
import java.util.List;

public class GalleryServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        ServletFileUpload upload = new ServletFileUpload(new DiskFileItemFactory());
        List<org.apache.commons.fileupload.FileItem> items = upload.parseRequest(req);
        for (org.apache.commons.fileupload.FileItem item : items) {
            if (!item.isFormField()) {
                item.write(new java.io.File("/var/www/gallery/" + item.getName()));
            }
        }
    }
}
