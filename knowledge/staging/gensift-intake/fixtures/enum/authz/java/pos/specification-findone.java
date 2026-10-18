// 出处:人工构造(依据 CWE-639 Specification 构建器查询形态)
public Ticket ticket(Long ticketId) {
    Specification<Ticket> spec = (root, query, cb) -> cb.equal(root.get("ticketId"), ticketId);
    return ticketRepository.findOne(spec).orElseThrow();
}
