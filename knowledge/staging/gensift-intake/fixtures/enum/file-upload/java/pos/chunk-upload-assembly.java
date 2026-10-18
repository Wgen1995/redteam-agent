// 出处:人工构造(依据 CWE-434 分片上传拼装形态——目标名可预测即竞态面)
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
public class ChunkController {
    @PostMapping("/chunks/{index}")
    public void chunk(@PathVariable int index, @RequestParam("chunk") MultipartFile chunk,
                      @RequestParam("name") String name) throws Exception {
        storage.saveFile(chunk, "/srv/parts/" + name + ".part" + index);
    }
}
