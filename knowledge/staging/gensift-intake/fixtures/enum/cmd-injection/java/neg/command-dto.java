// 出处:人工构造(硬负例:Command DTO/注解,无进程执行)
@CommandHandler
public void handle(RegisterOrderCommand cmd) {
    cmd.getAggregateId();
}
