// 出处:人工构造(硬负例:审计日志写入非防护形态)
public class AuditLogger {
    public void record(String actor, String action) {
        LOGGER.info("actor={} action={}", actor, action);
        auditRepository.append(new AuditEntry(actor, action, Instant.now()));
    }
}
