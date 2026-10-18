// 出处:人工构造(硬负例:属主校验属 authz 类,与本类形态无关)
@GetMapping("/invoices/{id}")
public Invoice read(@PathVariable Long id, Principal who) {
    Invoice inv = invoiceRepository.findById(id).orElseThrow();
    if (!inv.getOwner().equals(who.getName())) throw new ResponseStatusException(NOT_FOUND);
    return inv;
}
