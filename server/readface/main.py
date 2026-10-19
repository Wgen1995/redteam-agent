# -*- coding: utf-8 -*-
"""GraphLed 读面 FastAPI 入口(P0 T1 骨架)。

铁律对齐:引擎零改;读面进程只读账本+写走 engine_bridge;本文件只做装配。
启动(仓库根): python3 -m uvicorn server.readface.main:app --port 8901
"""
from pathlib import Path

from fastapi import FastAPI

from .routers import auth

app = FastAPI(title="graphled-readface", version="0.1.0")

app.include_router(auth.router)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "graphled-readface"}


# 静态托管占位:web/dist(vite build 产物)存在才挂;T14 收官启用。
# 挂在 "/" 尾部,不影响 /health 与 /api/* 显式路由。
_WEB_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"
if _WEB_DIST.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(_WEB_DIST), html=True), name="web")
