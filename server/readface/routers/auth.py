# -*- coding: utf-8 -*-
"""操作员登录:密钥比对 + HttpOnly 会话 cookie(内存会话表,TTL 12 小时)。

铁律对齐:读面只做登录会话;写路径一律走 engine_bridge,本文件不碰账本。
"""
import hashlib
import hmac
import os
import secrets
import time
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth")

# 会话有效期:12 小时(与 cookie Max-Age 一致)
SESSION_TTL_SECONDS = 12 * 60 * 60
SESSION_COOKIE = "session"

# 内存会话表:token -> 到期时间戳。
# 单进程读面够用;进程重启即全员下线,属预期(骨架阶段)。
_sessions = {}


def _operator_key() -> str:
    """读操作员密钥环境变量(缺省空串)。"""
    return os.environ.get("TANYIN_OPERATOR_KEY", "")


def _allow_demo() -> bool:
    """空钥缺省时是否放行演示模式(配置化,默认开;关掉则一律验钥)。"""
    flag = os.environ.get("READFACE_ALLOW_DEMO", "1")
    return flag.strip().lower() not in ("0", "false", "no", "off")


def make_token(key: str, salt: str) -> str:
    """会话令牌 = sha256(密钥+盐)。"""
    return hashlib.sha256((key + salt).encode("utf-8")).hexdigest()


def create_session(key: str) -> str:
    """落一条会话(token=sha256(key+随机盐)),返回 token。"""
    salt = secrets.token_hex(16)
    token = make_token(key, salt)
    _sessions[token] = time.time() + SESSION_TTL_SECONDS
    return token


def session_valid(token: Optional[str]) -> bool:
    """token 是否有效;过期即从表中清除。"""
    if not token:
        return False
    expiry = _sessions.get(token)
    if expiry is None:
        return False
    if time.time() >= expiry:
        _sessions.pop(token, None)
        return False
    return True


class LoginBody(BaseModel):
    key: str


@router.post("/login")
def login(body: LoginBody) -> JSONResponse:
    expected = _operator_key()
    demo = expected == "" and _allow_demo()
    if not demo:
        same = hmac.compare_digest(
            body.key.encode("utf-8"), expected.encode("utf-8")
        )
        if not same:
            return JSONResponse(status_code=401, content={"error": "密钥不对"})
    token = create_session(body.key)
    resp = JSONResponse(content={"ok": True, "demo": demo})
    resp.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return resp
