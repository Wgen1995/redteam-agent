# 出处:人工构造(依据 CWE-434 FastAPI 批量 UploadFile 列表)
from fastapi import File, UploadFile
from typing import List

@app.post('/gallery')
async def gallery(files: List[UploadFile] = File(...)):
    saved = []
    for f in files:
        dest = os.path.join(HTML_DIR, f.filename)
        with open(dest, 'wb') as out:
            out.write(await f.read())
        saved.append(dest)
    return {'saved': saved}
