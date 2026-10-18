// 出处:人工构造(硬负例:审计日志只写不取)
public void record(String action, String actor) {
    auditLogger.write(action, actor, Instant.now());
}
