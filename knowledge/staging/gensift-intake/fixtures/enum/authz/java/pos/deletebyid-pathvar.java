// 出处:人工构造(依据 CWE-639 按 id 删除无属主校验形态)
@DeleteMapping("/orders/{id}")
public ResponseEntity<Void> cancel(@PathVariable Long id) {
    orderRepository.deleteById(id);
    return ResponseEntity.noContent().build();
}
