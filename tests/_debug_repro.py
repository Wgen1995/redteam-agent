# -*- coding: utf-8 -*-
import io, os, sys, tempfile
from contextlib import redirect_stdout, redirect_stderr
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cli"))
from ledger import write_cmds

td = tempfile.mkdtemp()
gd = os.path.join(td, "G-g2")
os.makedirs(gd)
print("before:", sorted(os.listdir(gd)))
buf_o, buf_e = io.StringIO(), io.StringIO()
args = ["--target=t.example", "--objective=o", "--auth-doc=a.pdf", "--auth-sha256=" + "a" * 64,
        "--signer=", "--valid-from=2026-09-01", "--valid-until=2026-09-30",
        "--budget=2M;50000;40", "--model-tier=strong", "--guard-tier=T3", "--timestamp=T"]
with redirect_stdout(buf_o), redirect_stderr(buf_e):
    code = write_cmds.HANDLERS["add-goal"](gd, args)
print("code", code, "| out:", buf_o.getvalue().strip(), "| err:", buf_e.getvalue().strip())
print("after:", sorted(os.listdir(gd)))
