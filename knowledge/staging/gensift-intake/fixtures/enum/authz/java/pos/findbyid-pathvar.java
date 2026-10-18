// 出处:人工构造(依据 CWE-639 Spring Data 按 id 直查无属主过滤形态)
@GetMapping("/invoices/{id}")
public Invoice read(@PathVariable Long id) {
    return invoiceRepository.findById(id).orElseThrow(() -> new ResponseStatusException(NOT_FOUND));
}
