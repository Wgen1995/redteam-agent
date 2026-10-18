// 出处:人工构造(噪音:同 API 安全用法——Part.write 服务端生成名;允许命中)
import javax.servlet.http.Part;
import java.util.UUID;

public class SafePartServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        Part part = req.getPart("doc");
        String serverName = UUID.randomUUID() + ".part";
        part.write("/srv/nonweb/" + serverName);
        audit.log(part.getSubmittedFileName(), serverName);
    }
}
