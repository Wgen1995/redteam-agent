// 出处:人工构造(硬负例:.get 同形但键非对象 id——会话令牌缓存)
Object cached = tokenCache.get(sessionToken);
boolean warm = cached != null;
