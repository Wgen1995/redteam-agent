// 出处:人工构造(硬负例:异常映射)
@ExceptionHandler(BizException.class)
ResponseEntity<Error> handle(BizException e) { return ResponseEntity.badRequest().body(new Error(e.getCode())); }
