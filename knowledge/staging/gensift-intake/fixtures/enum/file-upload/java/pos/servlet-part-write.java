// 出处:人工构造(依据 CWE-434 + OWASP File Upload Cheatsheet 原生 Part 形态)
import javax.servlet.http.Part;

public class LegacyUploadServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        Part part = req.getPart("doc");
        String clientName = part.getSubmittedFileName();
        part.write("/opt/web/htdocs/files/" + clientName);
    }
}
