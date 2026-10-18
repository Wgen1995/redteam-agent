// 出处:人工构造(硬负例:定时任务)
@Scheduled(fixedDelay = 5000)
public void sweep() { store.sweepExpired(); }
