// 出处:人工构造(硬负例:定时清理)
@org.springframework.scheduling.annotation.Scheduled(cron = "0 0 3 * * *")
public void purge() throws Exception {
    java.nio.file.Files.list(java.nio.file.Path.of(CACHE)).filter(this::expired).forEach(this::deleteQuiet);
}
