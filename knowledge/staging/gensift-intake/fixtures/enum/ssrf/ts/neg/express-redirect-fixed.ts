// 出处:人工构造(硬负例:业务 302 到固定内部路径)
if (!req.user) { res.redirect('/login'); return; }
res.redirect('/profile');
