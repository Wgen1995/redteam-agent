# 出处:人工构造(依据 CWE-434 Flask request.files 原名保存)
from flask import request

@app.route('/upload', methods=['POST'])
def upload_photo():
    photo = request.files['photo']
    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo.filename))
    return redirect(url_for('gallery'))
