# 出处:人工构造(Flask 上传保存形态)
dest = os.path.join(UPLOAD_FOLDER, request.files['upload'].filename)
request.files['upload'].save(dest)
