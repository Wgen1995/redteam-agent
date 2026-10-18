// 出处:人工构造(依据 CWE-434 服务层封装 saveFile 形态——校验责任分离丢失)
import org.springframework.web.multipart.MultipartFile;
import org.springframework.stereotype.Service;

@Service
public class StorageService {
    public String saveFile(MultipartFile file, String tenantDir) throws Exception {
        String target = tenantDir + "/" + file.getOriginalFilename();
        file.transferTo(new java.io.File(target));
        return target;
    }
}
