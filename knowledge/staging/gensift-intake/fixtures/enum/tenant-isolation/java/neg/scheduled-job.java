// 出处:人工构造(硬负例:定时任务)
@Scheduled(cron = "0 0 4 * * *")
public void archiveOldBatches() {
    batchRepository.deleteByCreatedBefore(Instant.now().minus(Duration.ofDays(365)));
}
