// 出处:人工构造(硬负例:异常到响应映射)
@ExceptionHandler(IllegalArgumentException.class)
public ResponseEntity<String> handle(IllegalArgumentException error) {
    return ResponseEntity.badRequest().body("rejected");
}
