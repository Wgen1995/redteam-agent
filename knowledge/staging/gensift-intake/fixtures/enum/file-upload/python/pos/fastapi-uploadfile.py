# 出处:人工构造(依据 CWE-434 FastAPI UploadFile 原名直写)
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.post('/certs')
async def upload_cert(file: UploadFile = File(...)):
    data = await file.read()
    path = os.path.join('/srv/htdocs/certs', file.filename)
    with open(path, 'wb') as out:
        out.write(data)
    return {'size': len(data)}
