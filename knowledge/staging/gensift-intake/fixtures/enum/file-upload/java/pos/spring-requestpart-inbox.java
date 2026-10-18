// 出处:人工构造(依据 CWE-434 @RequestPart 声明式绑定 + 客户端名落盘)
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
public class InboxController {
    @PostMapping(value = "/inbox", consumes = "multipart/form-data")
    public String receive(@RequestPart("attachment") MultipartFile attachment) throws Exception {
        String stored = attachment.getOriginalFilename();
        java.nio.file.Files.write(java.nio.file.Path.of("/srv/store/" + stored), attachment.getBytes());
        return stored;
    }
}
