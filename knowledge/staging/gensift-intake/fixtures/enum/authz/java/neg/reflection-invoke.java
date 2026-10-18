// 出处:人工构造(硬负例:反射调度非数据访问)
Method handler = target.getClass().getMethod("onEvent", String.class);
Object outcome = handler.invoke(target, event);
