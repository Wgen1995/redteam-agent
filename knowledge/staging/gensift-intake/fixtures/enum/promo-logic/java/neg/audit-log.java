// 出处:人工构造(硬负例:审计写入,无促销语义)
public void record(String action, String actor) {
    auditLogger.write(action, actor, Instant.now());
}
