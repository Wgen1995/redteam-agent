# -*- coding: utf-8 -*-
"""C2-lite 测试共用夹具——goal 立项/意图/L3 预授权族放行(全本地回环,零外网零真靶)。

夹具律:
- 每例自建 tmp goal 目录,测毕即焚;时间戳全定值(零睡眠零墙钟);
- 13 表写路径原样复用 write_cmds(redirect_stdout 吞 _ok_line——测面只认账本);
- 审批族四放行(c2-beacon/c2-cmd/c2-echo/c2-webshell)对齐 FAMILIES 在册面。
"""
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
sys.path.insert(0, os.path.join(HERE, ".."))

from ledger import write_cmds          # noqa: E402

T0 = "2026-10-18T10:00:00Z"
VF = "2026-10-18T00:00:00Z"
VU = "2026-10-19T00:00:00Z"


def ts(minute, sec=0):
    """T0 起第 minute 分(可带秒)的 ISO8601 Z 时间戳——账本 ts 全定值。"""
    return "2026-10-18T%02d:%02d:%02dZ" % (10 + minute // 60, minute % 60, sec)


def _quiet(fn, *a, **kw):
    buf = io.StringIO()
    with redirect_stdout(buf):
        return fn(*a, **kw)


def boot_goal(name="G-c2t"):
    """tmp goal 目录+立项(场景靶场显式豁免授权书在场)。"""
    d = tempfile.TemporaryDirectory()
    gd = os.path.join(d.name, name)
    os.makedirs(gd, exist_ok=True)
    _quiet(write_cmds._add_goal, gd, [
        "--target=127.0.0.1", "--objective=C2-lite 受控档账本化测试(本地回环)",
        "--auth-doc=auth-range.md", "--auth-sha256=" + "a" * 64,
        "--signer=靶场管理员", "--valid-from=" + VF, "--valid-until=2026-12-31T00:00:00Z",
        "--budget=1000;100;10", "--model-tier=weak", "--guard-tier=T3",
        "--allow-missing-auth=1", "--timestamp=" + T0])
    return d, gd


def add_intent(gd, title="C2 通道意图(回环靶场)", ts_=T0):
    """登记来源意图,返回 INT id(beacon/webshell 引用闭合的锚)。"""
    _quiet(write_cmds._add_intent, gd, [
        "--title=" + title, "--engine=manual", "--kind=recon",
        "--origin=entity", "--budget-share=100;10;1", "--timestamp=" + ts_])
    from ledger.core import Session
    return Session(gd).rows("intents.tsv")[-1][0]


def grant_family(gd, family, bounds="hosts=127.0.0.1", vf=VF, vu=VU, ts_=T0):
    """放行一个 L3 预授权族(gates-speed 预授权档: bounds+expire)。"""
    from cli.c2 import families
    return _quiet(families.grant, gd, family, bounds, "operator", vf, vu, ts_)[0]


def boot_c2(name="G-c2t", families=("c2-beacon", "c2-cmd", "c2-echo", "c2-webshell")):
    """goal+意图+指定族放行(默认四族)——多数用例的完整夹具。"""
    d, gd = boot_goal(name)
    iid = add_intent(gd)
    for f in families:
        grant_family(gd, f)
    return d, gd, iid


def boot_beacon(name="G-c2t"):
    """goal+意图+四族+登记一个 beacon。返回 (tmp, gd, iid, beacon_id)。"""
    d, gd, iid = boot_c2(name)
    from cli.c2 import beacon
    bid, _row = beacon.register(gd, T0, iid)
    return d, gd, iid, bid
