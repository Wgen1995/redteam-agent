// 出处:人工构造(依据 CWE-434 二阶——入库文件名回读再落盘/persisted_read)
import javax.servlet.http.Part;
import java.sql.ResultSet;

public class ResubmitJob extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        ResultSet rs = db.query("SELECT stored_name FROM uploads WHERE id = ?", req.getParameter("id"));
        rs.next();
        Part incoming = req.getPart("replay");
        incoming.write("/var/web/queue/" + rs.getString("stored_name"));
    }
}
