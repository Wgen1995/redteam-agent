// 出处:人工构造(依据 CWE-434 commons-fileupload FileItemIterator 流式形态)
import org.apache.commons.fileupload.servlet.ServletFileUpload;
import org.apache.commons.fileupload.FileItemIterator;

public class BatchImportServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        ServletFileUpload upload = new ServletFileUpload();
        FileItemIterator iter = upload.getItemIterator(req);
        while (iter.hasNext()) {
            org.apache.commons.fileupload.FileItemStream stream = iter.next();
            java.nio.file.Files.copy(stream.openStream(),
                java.nio.file.Path.of("/data/imports/" + stream.getName()));
        }
    }
}
