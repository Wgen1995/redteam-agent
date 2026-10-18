// 出处:人工构造(依据 CWE-434 MultipartFile[] 批量循环落盘)
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
public class BatchController {
    @PostMapping("/albums")
    public int album(@RequestParam("photos") MultipartFile[] photos) throws Exception {
        int n = 0;
        for (MultipartFile photo : photos) {
            photo.transferTo(new java.io.File("/srv/albums/" + photo.getOriginalFilename()));
            n++;
        }
        return n;
    }
}
