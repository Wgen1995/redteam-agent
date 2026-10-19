# -*- coding: utf-8 -*-
"""GraphLed 读面 FastAPI 入口(P0 T1 骨架)。

铁律对齐:引擎零改;读面进程只读账本+写走 engine_bridge;本文件只做装配。
启动(仓库根): python3 -m uvicorn server.readface.main:app --port 8901
"""
from pathlib import Path

from fastapi import FastAPI

from .routers import approvals, auth, chat, findings, overview, say, tasks

app = FastAPI(title="graphled-readface", version="0.1.0")

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(overview.router)
app.include_router(say.router)   # T6 说话开仗: say/confirm(写走 engine_bridge)
app.include_router(approvals.router)   # T8 内联审批: approve(写走 engine_bridge)
app.include_router(tasks.router)      # T11 任务列表+详情·会话签(纯读)
app.include_router(findings.router)   # T12 发现页: 列表过滤/详情/复验(桥)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "graphled-readface"}


# 静态托管:web/dist(vite build 产物)存在才挂;SPA 深链回退——
# 客户端路由(/chat 等)刷新不再 404:真文件直供,否则回 index.html;/api/* 不兜。
_WEB_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"
if _WEB_DIST.is_dir():
    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        cand = (_WEB_DIST / full_path).resolve()
        if full_path and cand.is_file() and str(cand).startswith(str(_WEB_DIST.resolve())):
            return FileResponse(str(cand))
        return FileResponse(str(_WEB_DIST / "index.html"))
