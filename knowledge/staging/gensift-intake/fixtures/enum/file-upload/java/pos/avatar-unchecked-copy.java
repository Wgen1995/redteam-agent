// 出处:人工构造(依据 CWE-434 nio copy + 客户端名拼接形态)
import org.springframework.web.multipart.MultipartFile;

public class ProfileService {
    public void store(MultipartFile avatar, String baseDir) throws Exception {
        java.nio.file.Path dest = java.nio.file.Path.of(baseDir, avatar.getOriginalFilename());
        java.nio.file.Files.copy(avatar.getInputStream(), dest, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
    }
}
