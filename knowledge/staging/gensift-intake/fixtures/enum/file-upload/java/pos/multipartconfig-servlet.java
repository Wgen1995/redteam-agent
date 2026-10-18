// 出处:人工构造(依据 CWE-434 @MultipartConfig 声明式入口——无层校验)
import javax.servlet.annotation.MultipartConfig;
import javax.servlet.annotation.WebServlet;

@WebServlet("/upload/font")
@MultipartConfig
public class FontUploadServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        javax.servlet.http.Part font = req.getPart("font");
        font.write("/usr/share/fonts/" + font.getSubmittedFileName());
    }
}
