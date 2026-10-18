// 出处:人工构造(依据 CWE-434 jakarta 命名空间 Part 形态)
import jakarta.servlet.http.Part;

public class ModernUploadServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        for (Part part : req.getParts()) {
            String name = part.getSubmittedFileName();
            part.write(System.getProperty("webroot") + "/assets/" + name);
        }
    }
}
