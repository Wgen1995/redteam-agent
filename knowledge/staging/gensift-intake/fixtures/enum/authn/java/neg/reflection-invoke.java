// 出处:人工构造(硬负例:反射调用注册表白名单方法)
public Object dispatch(String handlerName, Object[] args) throws Exception {
    Method m = HANDLERS.get(handlerName);
    if (m == null) throw new IllegalStateException("unknown handler");
    return m.invoke(target, args);
}
