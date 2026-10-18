// 出处:人工构造(依据 lodash _.set path 可控沿链写原型)
_.set(userProfile, req.body.path, req.body.value);
cache.set(uid, userProfile);
