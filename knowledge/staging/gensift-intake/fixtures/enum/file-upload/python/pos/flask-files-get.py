# 出处:人工构造(依据 CWE-434 request.files.get + 客户端名拼接)
def upload_doc():
    doc = request.files.get('doc')
    if doc and allowed(doc.filename):
        target = os.path.join(STATIC_DIR, doc.filename)
        doc.save(target)
    return 'ok'
