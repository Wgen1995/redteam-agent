// 出处:人工构造(硬负例:路由声明,非网络调用)
router.get('/users/:id', getUserHandler);
router.post('/users', createUserHandler);
