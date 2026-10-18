// 出处:人工构造(硬负例:调度任务)
@Scheduled(cron = "0 0 3 * * *")
public void reconcileLedger() {
    ledgerRepository.findUnbalanced().forEach(ledgerService::rebalance);
}
