// 出处:人工构造(硬负例:异常映射)
@ExceptionHandler(NotFound.class)
ResponseEntity<Error> notFound(NotFound e) { return ResponseEntity.status(404).body(Error.of(e.getId())); }
