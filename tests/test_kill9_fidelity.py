# -*- coding: utf-8 -*-
"""批次 3 T12：kill -9 保真度 eval。层 A=确定性撕裂三态（双平台）；层 B=随机断点（POSIX）。
机制根基=T4 原子写（tmp+os.replace）+T5 对账重建——本 eval 是证据链：
恢复协议跑完后 13 表字节指纹不变（保真度的定义）+ state-rebuild PASS。"""
import hashlib, os, random, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cli"))
from ledger import core

from tests.test_dryrun_p0p2 import dry_run_p0_p2, ledger, phases, fresh_drydir, TS
from tests.test_dryrun_p0p2 import STEPS

STEPS_N = len(STEPS)   # 12 步（T11 交付含 budget-check）——Ruling：计划 len(STEPS_N) 笔误

CHILD = os.path.join(HERE, "_kill9_child.py")


class TornBase(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.n = 0

    def fresh(self):
        gd = fresh_drydir(self.td.name, "G-k9-%d" % self.n)
        self.n += 1
        return gd

    def fingerprint(self, gd):
        """13 表字节指纹（恢复不得改变账本——保真度的定义）。"""
        h = hashlib.sha256()
        for t in sorted(core.TABLES):
            p = os.path.join(gd, t)
            h.update(t.encode())
            h.update(open(p, "rb").read() if os.path.exists(p) else b"-")
        return h.hexdigest()

    def drive_with_checkpoint(self, gd, upto=None):
        dry_run_p0_p2(gd, upto=upto)
        ledger(gd, "checkpoint", ["--session=s-k9", "--phase=P3",
                                  "--note=k9", "--timestamp=" + TS])

    def recover_and_assert(self, gd):
        """恢复协议三步（SKILL.md 第⑤节）+保真断言；返回 state-rebuild 输出。"""
        fp_before = self.fingerprint(gd)
        c1, out1, _ = ledger(gd, "verify-chain")
        self.assertEqual(c1, 0, out1)   # 链未断：kill -9 不碰已落盘行（原子追加纪律）
        c2, out2, _ = ledger(gd, "state-rebuild")
        if c2 != 0:
            c3, out3, _ = phases(gd, "rebuild-state", ["--timestamp=" + TS])
            self.assertEqual(c3, 0, out3)
            c2, out2, _ = ledger(gd, "state-rebuild")
        self.assertEqual(c2, 0, out2)
        c4, out4, _ = phases(gd, "resume-kit", ["--timestamp=" + TS])
        self.assertEqual(c4, 0, out4)
        self.assertTrue(os.path.isfile(os.path.join(gd, "resume-kit.md")))
        self.assertEqual(self.fingerprint(gd), fp_before)   # 13 表零变更
        return out2


class TestLayerA_TornStates(TornBase):
    def test_torn_tmp_leftover(self):   # 撕裂态 A：state.md.tmp 残留+state 完整
        gd = self.fresh()
        self.drive_with_checkpoint(gd)
        with open(os.path.join(gd, "state.md.tmp"), "w", encoding="utf-8") as f:
            f.write("torn half")
        c, out, _ = phases(gd, "rebuild-state", ["--timestamp=" + TS])   # rebuild 顺带清扫 tmp
        self.assertEqual(c, 0, out)
        self.assertFalse(os.path.exists(os.path.join(gd, "state.md.tmp")))
        out = self.recover_and_assert(gd)
        self.assertIn("PASS", out)

    def test_torn_state_stale(self):   # 撕裂态 B：timeline 领先 state（checkpoint 撕裂）
        gd = self.fresh()
        self.drive_with_checkpoint(gd)
        # Ruling：--phase 空值被 _req 拒收（T5 裁决⑤同型）→按 T5 同场景先例落 P3；
        # 并断言 late-write 真落账（否则撕裂态未构造、用例空转）。
        c, out, _ = ledger(gd, "append-timeline", ["--actor=CLI", "--phase=P3",
                                                  "--event=late-write", "--timestamp=" + TS])
        self.assertEqual(c, 0, out)
        out = self.recover_and_assert(gd)
        self.assertIn("PASS", out)

    def test_torn_state_missing(self):   # 撕裂态 C：state.md 缺失
        gd = self.fresh()
        self.drive_with_checkpoint(gd)
        os.remove(os.path.join(gd, "state.md"))
        out = self.recover_and_assert(gd)
        self.assertIn("PASS", out)

    def test_torn_resume_kit_missing(self):   # 工件缺失：重生成幂等
        gd = self.fresh()
        self.drive_with_checkpoint(gd)
        p = os.path.join(gd, "resume-kit.md")
        if os.path.exists(p):
            os.remove(p)
        with open(p + ".tmp", "w", encoding="utf-8") as f:
            f.write("torn")
        self.recover_and_assert(gd)   # write_resume_kit 的 tmp+replace 顺带覆盖残tmp
        self.assertFalse(os.path.exists(p + ".tmp"))


@unittest.skipIf(os.name != "posix", "SIGKILL 注入仅 POSIX（CI ubuntu 跑；windows 合法跳过）")
class TestLayerB_RandomKill(TornBase):
    def test_random_breakpoint_recovery(self):
        rng = random.Random(20260924)   # seed 固定：失败可复现
        for trial in range(5):
            gd = self.fresh()
            upto = rng.randint(3, STEPS_N + 1)   # 驱动 12 步+checkpoint（Ruling：len 笔误修正）
            proc = subprocess.Popen([sys.executable, CHILD, gd, str(upto)],
                                    cwd=ROOT)
            proc.wait(timeout=120)
            # Ruling：计划字面忽略子进程返回码——启动失败（exit 2）会让本例空转绿。
            # 断点截断=子进程主动 exit 0；非 0=未真跑，须红。upto≥3 ⇒ add-goal 必已落账。
            self.assertEqual(proc.returncode, 0, "子进程启动/运行失败（非断点截断）")
            self.assertTrue(os.path.isfile(os.path.join(gd, "goals.tsv")),
                            "upto≥3 必已执行 add-goal——子进程未真跑")
            # kill -9 半写模拟：已写的 state 摘除（丢弃半写窗口内容）
            sp = os.path.join(gd, "state.md")
            if os.path.isfile(sp) and rng.random() < 0.5:
                os.remove(sp)
            out = self.recover_and_assert(gd)
            self.assertIn("PASS", out, "trial=%d upto=%d" % (trial, upto))

    def test_exhaustive_breakpoint_discard_sweep(self):
        """Ruling 追加件：seed 20260924 的五枚硬币实测全 ≥0.5——计划字面的「state
        摘除」分支在该冻结 seed 下永不触发（计划原子进程无 checkpoint 时更是恒死码）。
        追加确定性穷举：断点 3..STEPS_N+1 × {保留, 摘除} 全组合——「任意断点+state
        丢弃后恢复协议闭环」不靠抽样运气证明。"""
        for upto in range(3, STEPS_N + 2):
            for discard in (False, True):
                gd = self.fresh()
                proc = subprocess.Popen([sys.executable, CHILD, gd, str(upto)],
                                        cwd=ROOT)
                proc.wait(timeout=120)
                self.assertEqual(proc.returncode, 0,
                                 "upto=%d 子进程启动/运行失败（非断点截断）" % upto)
                sp = os.path.join(gd, "state.md")
                self.assertTrue(os.path.isfile(sp),
                                "upto=%d checkpoint 未落 state.md（摘除臂将空转）" % upto)
                if discard:
                    os.remove(sp)   # kill -9 半写丢弃（确定性臂，不掷硬币）
                out = self.recover_and_assert(gd)
                self.assertIn("PASS", out, "upto=%d discard=%s" % (upto, discard))


if __name__ == "__main__":
    unittest.main()
