// 出处:人工构造(硬负例:定时任务清理)
@Scheduled(cron = "0 0 3 * * *")
public void purgeExpiredTokens() {
    tokenRepository.deleteByExpiresBefore(Instant.now());
}
