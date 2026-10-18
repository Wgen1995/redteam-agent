// 出处:人工构造(依据 CWE-639 内存缓存按 id 取形态)
public String preview(String reportId) {
    byte[] cached = previewCache.get(reportId);
    return cached == null ? "" : new String(cached, StandardCharsets.UTF_8);
}
