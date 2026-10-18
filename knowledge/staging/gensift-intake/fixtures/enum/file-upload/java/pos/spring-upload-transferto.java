// 出处:人工构造(依据 CWE-434 + OWASP File Upload Cheatsheet 原名直落盘形态)
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.File;

@RestController
public class AvatarController {
    @PostMapping("/avatar")
    public String upload(@RequestParam("file") MultipartFile file) throws Exception {
        File dest = new File("/var/app/webapp/uploads/" + file.getOriginalFilename());
        file.transferTo(dest);
        return dest.getName();
    }
}
