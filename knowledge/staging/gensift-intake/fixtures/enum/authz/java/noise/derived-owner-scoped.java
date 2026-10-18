// 出处:人工构造(噪音:派生查询属主列进查询条件)
public Invoice read(Long invoiceId, Long ownerId) {
    return invoiceRepository.findByIdAndOwnerId(invoiceId, ownerId).orElse(null);
}
