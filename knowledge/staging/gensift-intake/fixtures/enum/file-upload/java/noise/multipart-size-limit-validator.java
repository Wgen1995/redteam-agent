// 出处:人工构造(噪音:同 API 安全用法——大小/类型配额校验后丢弃;允许命中)
import org.springframework.web.multipart.MultipartFile;

public class UploadLimits {
    public void check(MultipartFile file) {
        if (file.getSize() > 1_048_576L) throw new IllegalStateException("too large");
        if (!file.getContentType().equals("image/png")) throw new IllegalStateException("type");
    }
}
