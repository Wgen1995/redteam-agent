// 出处:人工构造(硬负例:定时任务指标上报)
@Scheduled(fixedDelay = 60000)
public void heartbeat() {
    metrics.gauge("worker.alive", 1);
}
