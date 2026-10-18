# 出处:人工构造(依据 CWE-22 shutil.copy 拼接形态)
src_name = request.args.get('src')
shutil.copy(SHARED + '/' + src_name, BACKUP_DIR)
