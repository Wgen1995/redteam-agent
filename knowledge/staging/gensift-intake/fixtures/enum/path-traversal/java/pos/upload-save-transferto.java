// 出处:人工构造(Spring MultipartFile 注解声明式上传保存形态)
@PostMapping("/upload")
public String handle(@RequestParam("file") MultipartFile upload) {
    String original = upload.getOriginalFilename();
    upload.transferTo(new File(storageDir + "/" + original));
    File dest = new File(storageDir + "/" + original);
    upload.transferTo(dest);
    return "ok";
}
