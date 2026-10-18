# 出处:人工构造(依据 CWE-22 shutil.copy join 传播形态)
shutil.copy(os.path.join(SRC_DIR, request.form['f']), BACKUP_DIR)
