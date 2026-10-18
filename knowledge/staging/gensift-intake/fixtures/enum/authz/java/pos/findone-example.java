// 出处:人工构造(依据 CWE-639 Example 探针查询形态)
public Invoice view(String invoiceNumber) {
    Invoice probe = new Invoice();
    probe.setNumber(invoiceNumber);
    return invoiceRepository.findOne(Example.of(probe)).orElse(null);
}
