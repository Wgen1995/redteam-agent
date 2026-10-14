# -*- coding: utf-8 -*-
"""v0.8 Task W：llmpool 战场接线——attach(goal_dir) 状态钉根 + emit 包装 timeline 单源写方。

红=现状：cli/ledger 无 llmpool_wire 模块。契约（docs/superpowers/plans/
2026-10-14-v09b-and-wiring.md Task W）：
- attach(goal_dir, env=None, now=None, rng=None) -> llmpool.Registry：
  state_path=<goal_dir>/llmpool_state.json；emit=包装 goal 账本 timeline
  单源写方（ledger.timeline.append_tl_locked——goal 锁内路径，勿绕开锁），
  事件行 kind=llm_failover（event/model/reason/lane/cooldown_s 进负载）。
- 测试四象限（计划 Task W 节）：①attach 后 report 硬熔错误→timeline 新增
  llm_failover 事件行+state 文件落盘；②同路径重建 Registry→冷却窗恢复
  （重启语义）；③emit 写失败不外抛（llmpool 已吞，接线层不新增炸点）；
  ④attach 幂等（选定语义：每次新等价实例+state 兼容，文档化于实现 docstring）。
- 附加两测（自选语义的对应钉）：⑤env 映射可整体改投 state 文件位置
  （TANYIN_LLMPOOL_STATE——llmpool.ENV_STATE 同名先例），timeline 不受影响；
  ⑥源码钉——接线只经 append_tl_locked 单源写方，不私铸链行。
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "cli"))
from ledger import core          # noqa: E402
from ledger import llmpool       # noqa: E402
from ledger import llmpool_wire  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "G-g1")


def half_rng():
    """固定 0.5 → 抖动因子恰为 1.0（test_v08a_llmpool 同款确定性基准）。"""
    return 0.5


class Clock(object):
    """可拨时钟：epoch 1000.0 起步（test_v08a_llmpool 同款）。"""

    def __init__(self, start=1000.0):
        self.t = float(start)

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += float(seconds)


class WireBase(unittest.TestCase):
    """夹具 G-g1 副本（timeline 8 行链有效）+ 注入时钟/随机源。"""

    def setUp(self):
        self.gd = tempfile.mkdtemp(prefix="v08w-wire-")
        for f in os.listdir(FIX):
            shutil.copy(os.path.join(FIX, f), self.gd)
        self.clock = Clock()

    def tearDown(self):
        shutil.rmtree(self.gd, ignore_errors=True)

    def attach(self, **kw):
        kw.setdefault("env", {})      # 隔离 os.environ 意外覆盖（TANYIN_LLMPOOL_STATE）
        kw.setdefault("now", self.clock)
        kw.setdefault("rng", half_rng)
        return llmpool_wire.attach(self.gd, **kw)

    def tl_rows(self):
        return core.read_tsv(os.path.join(self.gd, "timeline.tsv"), 8)

    def tl_bytes(self):
        with open(os.path.join(self.gd, "timeline.tsv"), "rb") as f:
            return f.read()

    def state_path(self):
        return os.path.join(self.gd, llmpool.STATE_FILENAME)

    def assert_chain_ok(self):
        ok, bad = core.Session(self.gd).verify_chain()
        self.assertTrue(ok, "timeline 链断于第 %d 行" % bad)


class TestAttachWritesTimeline(WireBase):
    """①attach 后 report 硬熔错误 → timeline 新增 llm_failover 事件行 + state 落盘。"""

    def test_hard_trip_appends_event_row_and_persists_state(self):
        p = self.attach()
        snap = p.report("a", 401)
        self.assertEqual(snap["state"], "tripped")
        rows = self.tl_rows()
        self.assertEqual(len(rows), 9)                      # 夹具 8 行 + 事件 1 行
        last = rows[-1]
        self.assertEqual(last[0], "1970-01-01T00:16:40Z")   # epoch 1000 → UTC ISO
        self.assertEqual(last[1], "llmpool")                 # actor
        self.assertEqual(last[2], "P-lifecycle")             # 跨阶段基础设施轨（wallclock 先例）
        self.assertEqual(
            last[3],
            "llm_failover event=trip model=a reason=http:401 lane=None cooldown_s=None")
        self.assertEqual(last[4], "")                        # revert 空
        self.assertEqual(last[7], "2")                       # schema_version
        self.assert_chain_ok()
        with open(self.state_path(), encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["models"]["a"]["hard"])        # state 钉根 goal 目录


class TestRestartSemantics(WireBase):
    """②同路径重建 Registry → 冷却窗/硬熔断恢复（重启语义）。"""

    def test_rebuild_same_goal_dir_restores_windows(self):
        p1 = self.attach()
        for _ in range(3):
            p1.report("a", 500)      # 软熔 3 连 → cooling 60s（rng=0.5 抖动因子 1.0）
        p1.report("b", 401)          # b 硬熔
        p2 = self.attach()            # 同 goal_dir 重建=重启
        self.assertEqual(p2.state_path, self.state_path())
        self.assertEqual(p2.snapshot("a"),
                         {"state": "cooling", "remaining_s": 60})
        self.assertEqual(p2.snapshot("b")["state"], "tripped")


class TestEmitFailureFailOpen(WireBase):
    """③emit 写失败不外抛——llmpool._fire 已吞异常，接线层不新增炸点。"""

    def test_timeline_corrupt_report_still_returns(self):
        # 真实失败注入（非 mock）：timeline.tsv 追加列数坏行 → 单源写方读表即炸
        with open(os.path.join(self.gd, "timeline.tsv"), "a", encoding="utf-8") as f:
            f.write("坏行\t两列" + chr(10))
        before = self.tl_bytes()
        p = self.attach()
        snap = p.report("a", 401)    # 不得外抛
        self.assertEqual(snap["state"], "tripped")
        with open(self.state_path(), encoding="utf-8") as f:
            data = json.load(f)      # state 照常落盘：记账 fail-open，判定优先
        self.assertTrue(data["models"]["a"]["hard"])
        self.assertEqual(self.tl_bytes(), before)   # 零半写：坏账本未被动过


class TestAttachIdempotent(WireBase):
    """④attach 幂等（选定语义，详见 llmpool_wire.attach docstring）：每次调用
    返回新建等价 Registry（无隐藏进程缓存），等价性由同一 state 文件承载。"""

    def test_second_attach_new_equivalent_instance_state_compatible(self):
        p1 = self.attach()
        for _ in range(3):
            p1.report("a", 500)      # a 熔 → timeline 1 行 + state 落盘
        p2 = self.attach()
        self.assertIsNot(p1, p2)      # 选定：等价新实例，非同实例缓存
        self.assertEqual(p2.state_path, p1.state_path)
        self.assertEqual(p2.snapshot("a")["state"], "cooling")  # state 兼容
        p2.report("b", 401)          # 二实例照常写同一 goal 账本
        rows = self.tl_rows()
        self.assertEqual(len(rows), 10)               # 夹具 8 + a 熔 + b 熔
        self.assertIn("model=a", rows[-2][3])
        self.assertIn("model=b", rows[-1][3])
        self.assert_chain_ok()


class TestEnvStateOverride(WireBase):
    """⑤env 映射可整体改投 state 文件位置（TANYIN_LLMPOOL_STATE）；
    timeline 事件仍进 goal 账本（战场主路径不动）。"""

    def test_env_override_redirects_state_only(self):
        custom = os.path.join(os.path.dirname(self.gd), "v08w-custom-state.json")
        self.addCleanup(lambda: os.path.exists(custom) and os.unlink(custom))
        p = self.attach(env={"TANYIN_LLMPOOL_STATE": custom})
        p.report("a", 401)
        self.assertTrue(os.path.exists(custom))               # state 改投 custom
        self.assertFalse(os.path.exists(self.state_path()))   # 钉根路径未被触碰
        self.assertIn("model=a", self.tl_rows()[-1][3])       # timeline 不受影响


class TestSingleSourceWriterPin(WireBase):
    """⑥源码钉（勿绕开锁）：接线只经 append_tl_locked 单源写方，不私铸链行。"""

    def test_wire_calls_locked_writer_no_local_minter(self):
        path = os.path.join(HERE, "..", "cli", "ledger", "llmpool_wire.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        self.assertIn("append_tl_locked", src)
        self.assertNotRegex(src, r"(?m)^def (chained_row|append_tl)\b")
        self.assertNotIn("row_hash(", src)


if __name__ == "__main__":
    unittest.main()
