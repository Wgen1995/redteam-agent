// 出处:人工构造(硬负例:ProcessHandle 进程查询非执行)
long pid = ProcessHandle.current().pid();
boolean alive = ProcessHandle.of(pid).map(ProcessHandle::isAlive).orElse(false);
