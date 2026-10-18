// 出处:人工构造(依据 CWE-78 spawn shell:true 形态)
spawn(userCmd, userArgs, { shell: true, stdio: 'inherit' });
