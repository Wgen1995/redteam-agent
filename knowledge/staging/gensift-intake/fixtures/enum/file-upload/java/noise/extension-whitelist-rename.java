// 出处:人工构造(噪音:同 API 安全用法——三层校验+服务端生成名;允许命中由五步判别)
import org.springframework.web.multipart.MultipartFile;
import java.util.Set;
import java.util.UUID;

public class ValidatedUploadService {
    private static final Set<String> ALLOWED = Set.of("jpg", "png", "webp");
    public String store(MultipartFile file) throws Exception {
        String ext = file.getOriginalFilename().replaceAll("(?i)^.*\\.", "").toLowerCase();
        if (!ALLOWED.contains(ext)) throw new IllegalArgumentException("ext");
        if (!file.getContentType().startsWith("image/")) throw new IllegalArgumentException("mime");
        String name = UUID.randomUUID() + "." + ext;
        file.transferTo(new java.io.File(STORE_DIR, name));
        return name;
    }
}
