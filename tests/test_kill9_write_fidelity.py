# -*- coding: utf-8 -*-
"""批次 7 T3：真实 SIGKILL 保真（SRE 复现协议：200k 行 timeline kill 8 次）+restart 三段写孤儿对账。
红=专家 8/8 静默丢史（200008 行→8KB、verify-chain 假绿 PASS、revision 回滚）。
POSIX-only（SIGKILL 语义）；Windows skip——CI 该文件 skip 不算红（test_kill9 层 B 同款门槛）。

R-T3-1（断点协议裁决）：计划片段的 rng.uniform(0.002, 0.05)s 断点落在子进程 import/读表
期（200k 行读表数百 ms 起），写窗内命中率≈0——红测会假绿（反例不复现）。改用**武装哨兵
协议**：子进程完成读表、即将进入写路径前触哨兵文件，父进程等哨兵后再 sleep
rng.uniform(0.002, 0.05) 发 SIGKILL——断点确定落在 200k 行写窗（>50ms）内，反例必现。
R-T3-2（tmp 残留裁决）：kill -9 无法执行 except 清扫，写窗内被杀必留 <table>.tmp——该残留
非撕裂态 A（账本本体以 os.replace 保证要么旧版要么新版），且同路径 tmp 在下一次写入时
被截断复用（收尾例钉死）；故 SIGKILL 循环内不断言 tmp 零残留，改断言「账本本体可解析+
链完整+行数不回滚」，并以收尾例断言残留被复用回收。计划内「tmp 零残留」断言由 T1
异常路径清扫例（test_atomic_write_b7）与收尾复用例共同承载。
R-T3-3（孤儿对账夹具裁决）：孤儿例夹具=tests/fixtures/G-g1 拷贝（test_managed_restart
同款）——计划片段的 fresh_drydir 空目无 goals/budget 行，_make_orphan 的 budget-log/
append-timeline 将 Tier0 REJECT（用法性假红）；反例需要合法账本上的孤儿事件竞速。"""
import os, random, shutil, subprocess, sys, tempfile, time, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
sys.path.insert(0, ROOT)
from ledger import core
from tests.test_dryrun_p0p2 import ledger, phases

FIX = os.path.join(HERE, "fixtures", "G-g1")
NCOLS = len(core.TABLES["timeline.tsv"])

def build_big_timeline(gd, n=200008):
    """测试夹具专用：直写大 timeline（链哈希逐行真实，不经 CLI）。"""
    rows, prev = [], core.GENESIS
    for i in range(n):
        ts = "2026-09-27T%02d:%02d:%02dZ" % (i % 24, (i // 24) % 60, i % 60)
        ev = "kill9-fidelity seq=%d" % i
        h = core.row_hash(prev, [ts, "CLI", "P1", ev, "", prev, core.SCHEMA_VERSION])
        rows.append([ts, "CLI", "P1", ev, "", prev, h, core.SCHEMA_VERSION])
        prev = h
    core.write_tsv(os.path.join(gd, "timeline.tsv"), rows)

CHILD = """
import os, sys
sys.path.insert(0, {root})
from ledger import core
gd = sys.argv[1]
p = os.path.join(gd, "timeline.tsv")
rows = core.read_tsv(p, len(core.TABLES["timeline.tsv"]))
ts, prev = "2026-09-27T23:59:59Z", rows[-1][6]
wo = [ts, "CLI", "P1", "kill9-append final", "", prev, core.SCHEMA_VERSION]
h = core.row_hash(prev, wo)
rows.append([ts, "CLI", "P1", "kill9-append final", "", prev, h, core.SCHEMA_VERSION])
# 武装哨兵（R-T3-1）：读表完毕、即将进入写路径——此后任意时刻被杀都落在写窗内
open(os.path.join(gd, ".armed"), "w").close()
core.write_tsv(p, rows)
os.unlink(os.path.join(gd, ".armed"))
""".format(root=repr(os.path.join(ROOT, "cli")))

class TestSigkillFidelity(unittest.TestCase):
    @unittest.skipUnless(os.name != "nt", "SIGKILL 语义 POSIX-only")
    def test_200k_rows_survive_eight_sigkills(self):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        gd = os.path.join(td.name, "G-k9b"); os.makedirs(gd)
        build_big_timeline(gd)
        n0 = len(core.read_tsv(os.path.join(gd, "timeline.tsv"), NCOLS))
        self.assertEqual(n0, 200008)
        rng = random.Random(20270927)   # seed 固定（T12 随机断点先例）
        armed = os.path.join(gd, ".armed")
        for k in range(8):
            if os.path.exists(armed):
                os.unlink(armed)
            p = subprocess.Popen([sys.executable, "-c", CHILD, gd])
            for _ in range(600):            # 等武装哨兵（读表毕，写窗将至）；30s 超时兜底
                if os.path.exists(armed):
                    break
                if p.poll() is not None:
                    break
                time.sleep(0.05)
            time.sleep(rng.uniform(0.002, 0.05))   # 写途中随机断点（R-T3-1：确定在写窗内）
            p.kill(); p.wait()
            ok, bad = core.Session(gd).verify_chain()
            self.assertTrue(ok, "第 %d 次 kill 后链断于行 %d（专家反例）" % (k + 1, bad))
            rows = core.read_tsv(os.path.join(gd, "timeline.tsv"), NCOLS)
            self.assertGreaterEqual(len(rows), n0,
                "第 %d 次 kill 后行数回滚（专家反例：200008→8KB、revision 回滚）" % (k + 1))
        # 收尾例（R-T3-2）：残留 tmp 被下一次写入同路径复用回收——零残留可恢复
        r = subprocess.run([sys.executable, "-c", CHILD, gd], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(os.path.join(gd, "timeline.tsv.tmp")),
                         "收尾成功写入后 tmp 必须零残留")
        rows = core.read_tsv(os.path.join(gd, "timeline.tsv"), NCOLS)
        self.assertEqual(len(rows), n0 + 1, "收尾追加恰好一行（链式推进不断不丢）")

class TestRestartOrphanReconcile(unittest.TestCase):
    """SRE High：checkpoint 前注入 kill→孤儿 restart+rate-limit 卡 10min。
    红=孤儿态下再 restart 被 RESTART_RATE_MINUTES=10 拒；绿=孤儿对账放行+补记对账事件。"""
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.addCleanup(self.td.cleanup)

    def _gdir(self, name):
        return shutil.copytree(FIX, os.path.join(self.td.name, name))

    def _make_orphan(self, gd):
        # 复刻 run_restart ④⑤（budget-log+managed-restart 事件），跳过 ⑥ checkpoint——
        # 事件词带 session=r-orphan（T3 升级格式），state.md session 保持旧值=孤儿判据
        from ledger import registry
        rc = registry.lookup("budget-log")(gd, ["--token-delta=2000", "--requests-delta=0",
            "--hours-delta=0", "--dollars-delta=0", "--scope=goal",
            "--note=managed-restart spawn=auto", "--timestamp=2026-09-27T01:00:00Z"])
        assert rc == 0, "夹具 budget-log 失败（R-T3-3 夹具有效性）"
        from ledger.phases_engine import _append_event
        _append_event(gd, "P1", "managed-restart spawn=auto session=r-orphan", "2026-09-27T01:00:00Z")

    def test_orphan_reconciles_not_rate_blocked(self):
        gd = self._gdir("G-orphan")
        rc, out, err = ledger(gd, "checkpoint", ["--session=s-old", "--phase=P1", "--note=old",
                                  "--timestamp=2026-09-27T00:30:00Z"])
        self.assertEqual(rc, 0, out + err + "（夹具 checkpoint 失败=R-T3-3 夹具无效）")
        self._make_orphan(gd)
        rc, out, err = phases(gd, "restart", ["--spawn=manual", "--usage=0.90", "--round=1",   # T12 必填契约
                                              "--timestamp=2026-09-27T01:05:00Z"])
        self.assertEqual(rc, 0, "孤儿对账后放行（红现状：rate-limit REJECT 卡 10min）: " + out)
        with open(os.path.join(gd, "timeline.tsv"), encoding="utf-8") as f:
            tl = f.read()
        self.assertIn("managed-restart-orphan prior-session=r-orphan", tl, "对账事件必须留痕")

    def test_non_orphan_still_rate_limited(self):
        gd = self._gdir("G-rate")
        rc, out, err = ledger(gd, "checkpoint", ["--session=s-a", "--phase=P1", "--note=a",
                                  "--timestamp=2026-09-27T00:30:00Z"])
        self.assertEqual(rc, 0, out + err)
        rc, out, err = phases(gd, "restart", ["--spawn=manual", "--usage=0.90", "--round=1",   # T12 必填契约
                                              "--timestamp=2026-09-27T00:40:00Z"])
        self.assertEqual(rc, 0, out + err)
        rc, out, err = phases(gd, "restart", ["--spawn=manual", "--usage=0.90", "--round=1",   # T12 必填契约
                                              "--timestamp=2026-09-27T00:45:00Z"])
        self.assertEqual(rc, 1, "真重启（checkpoint 已落地）仍受速率窗——孤儿豁免不得扩大化")
        self.assertIn("restart-rate-limit", out)