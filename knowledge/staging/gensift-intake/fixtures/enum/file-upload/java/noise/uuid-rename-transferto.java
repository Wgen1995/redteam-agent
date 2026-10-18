// 出处:人工构造(噪音:FP 卡形态——UUID 重命名+非 web 目录,originalFilename 只进元数据;允许命中)
import org.springframework.web.multipart.MultipartFile;
import java.util.UUID;

@RestController
public class SafeAvatarController {
    @Value("${app.storage.dir}") private String storageDir;
    @PostMapping("/avatar")
    public String upload(@RequestParam("file") MultipartFile file) throws Exception {
        String stored = UUID.randomUUID() + ".bin";
        file.transferTo(new java.io.File(storageDir, stored));
        metaRepo.save(new UploadMeta(file.getOriginalFilename(), stored));
        return stored;
    }
}
