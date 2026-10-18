// 出处:人工构造(spawnSync + shell:true 拼接形态)
spawnSync('tar -czf ' + archive + ' ' + dir, { shell: true });
