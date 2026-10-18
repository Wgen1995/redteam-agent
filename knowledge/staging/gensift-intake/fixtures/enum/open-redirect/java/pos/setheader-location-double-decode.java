// 出处:人工构造(依据 CWE-601 双重解码后直写 Location——约束与解码错位)
@GetMapping("/jump")
public void jump(@RequestParam String target, HttpServletResponse response) throws UnsupportedEncodingException {
    String decoded = URLDecoder.decode(URLDecoder.decode(target, "UTF-8"), "UTF-8");
    response.setHeader("Location", decoded);
}
