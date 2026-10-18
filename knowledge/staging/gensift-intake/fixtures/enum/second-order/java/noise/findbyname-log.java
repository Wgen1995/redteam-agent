// 出处:人工构造(噪音:findByX 回读拼接进日志——弱锚命中是设计属性,C4 判别)
logger.info("profile of " + userRepository.findByName(name).getNickname() + " exported");
