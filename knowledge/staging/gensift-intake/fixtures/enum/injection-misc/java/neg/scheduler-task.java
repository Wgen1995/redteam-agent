// 出处:人工构造(硬负例:定时任务)
@Scheduled(cron = "0 */5 * * * *")
public void reconcile() { service.reconcileBatches(); }
