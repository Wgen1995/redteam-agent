// 出处:人工构造(硬负例:异常映射)
@ExceptionHandler(IllegalArgumentException.class)
ResponseEntity<Error> bad(IllegalArgumentException e) { return ResponseEntity.badRequest().body(Error.of(e.getMessage())); }
