# 出处:人工构造(依据 CWE-434 二阶——入库文件名回读再落盘/persisted_read)
import shutil

def replay(request):
    row = db.fetchone('SELECT stored_name FROM attachments WHERE id=%s', [request.GET['id']])
    src = tempfile.mkstemp()[1]
    with open(src, 'wb') as tmp:
        shutil.copyfileobj(request.FILES['replay'].file, tmp)
    shutil.copy(src, os.path.join(WEB_ROOT, row['stored_name']))
