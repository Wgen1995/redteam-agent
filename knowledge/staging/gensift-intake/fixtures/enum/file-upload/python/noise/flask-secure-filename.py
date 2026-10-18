# 出处:人工构造(噪音:同 API 安全用法——secure_filename 净化;允许命中)
from werkzeug.utils import secure_filename

@app.route('/upload', methods=['POST'])
def upload():
    f = request.files['doc']
    if f and f.filename:
        safe = secure_filename(f.filename)
        f.save(os.path.join(UPLOAD_DIR, safe))
    return 'ok'
