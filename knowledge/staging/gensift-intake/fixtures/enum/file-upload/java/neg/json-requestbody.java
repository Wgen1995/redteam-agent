// 出处:人工构造(硬负例:JSON 体非 multipart)
public String create(@RequestBody OrderDto dto) { return svc.create(dto).getId(); }
