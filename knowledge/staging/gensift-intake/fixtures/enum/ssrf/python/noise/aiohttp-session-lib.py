# 出处:人工构造(噪音:aiohttp_session 服务端会话库用法——旧 pattern 误中形态)
from aiohttp_session import get_session, setup
session = await get_session(request)
