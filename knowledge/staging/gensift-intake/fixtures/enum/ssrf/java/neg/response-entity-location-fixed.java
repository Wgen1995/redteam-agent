// 出处:人工构造(硬负例:业务 302,Location 为常量相对路径)
return ResponseEntity.status(HttpStatus.FOUND)
    .header(HttpHeaders.LOCATION, "/login?expired=1")
    .build();
