# -*- coding: utf-8 -*-
"""W2·01P0-1+02P0：timeline O(1) 尾追加+epoch 撕裂读封口（TDD 红测试先行）。

前科（docs/reviews/2026-10-15-direction-review/05-engineering-debt.md ②/建议1、
2026-10-17-exceed-review/02-工程开发专家.md 骂1/骂2——F2 排队三评审周期）：
- O(N²)：append_tl_locked 每事件「Session 全量载 13 表→write_tsv 整表重写」，
  N 事件=O(N²) 字节写+解析，万行级账本单事件持续劣化（实测 18µs/行线性劣化在案）；
- epoch 撕裂：读侧无一致性校验——追加窗口内读者可见半行/新旧混读（撕裂快照），
  v1.0b 多战士并发写+webui 常驻读=撕裂从理论变日常。

红→绿判据：
① 万行级（默认 10k 行，TL_PERF_N 可缩）追加全程 < 60s、尾窗 200 事件 < 2.0s、
   尾窗/首窗均值比 < 6——O(1) ⇒ 近常数；O(N²) 形态在该量级必炸（比≈N/200=50）；
② 字节级兼容：同一事件序列经 append_tl_locked 与「全量读+write_tsv 整表重写」
   （修前旧算法的测试内参考实现）产物逐字节相等——金样/fingerprint/链哈希零漂移之根；
③ 撕裂读封口：read_rows 读前后双验 .timeline.epoch——窗内有追加=整体重读后成功；
   持续变更=TornTimelineError 拒绝返回（fail-closed 不吐撕裂视图）；持久损坏半行
   =read_tsv 原语义直抛；并发写×读（真实线程，非 mock）全窗口每个返回视图链完整；
④ 末行损坏 fail-closed：列数坏行/无 LF 收尾=拒追加且零半写（wallclock 反例同源；
   旧路径对无 LF 末行会静默"修复"入链——新路径 fail-closed，修复走人工）；
⑤ epoch 工件卫生：.timeline.epoch 为 dot 工件不进 13 表（.lock 同律），
   Session/validate 零干扰；追加路径与整表重写路径（Ctx.commit 形态）交错接链互通。
"""
import itertools
import os, shutil, sys, tempfile, threading, time, unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, os.path.join(ROOT, 'cli'))
from ledger import core
from ledger import timeline as TL

FIX = os.path.join(HERE, 'fixtures', 'G-g1')
NCOL = len(core.TABLES['timeline.tsv'])
EPOCH_NAME = '.timeline.epoch'


def chain_ok(rows):
    """链完整性复算（core.Session.verify_chain 同判据，脱离 Session 便于并发窗口内调用）。"""
    prev = core.GENESIS
    for r in rows:
        if r[5] != prev or core.row_hash(prev, r[:6] + [r[7]]) != r[6]:
            return False
        prev = r[6]
    return True


def _ts(i):
    return '2026-10-18T%02d:%02d:%02dZ' % (i // 3600 % 24, i // 60 % 60, i % 60)


class WireBase(unittest.TestCase):
    """夹具 G-g1 副本（timeline 8 行链有效）——wallclock WireBase 同款。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.gd = shutil.copytree(FIX, os.path.join(self._tmp.name, 'G-g1'))

    def tl_bytes(self, gd=None):
        with open(os.path.join(gd or self.gd, 'timeline.tsv'), 'rb') as f:
            return f.read()


# ---------------------------------------------------------------- ① O(1) 性能阈值

class TestO1AppendPerf(WireBase):
    def test_10k_rows_constant_tail_latency(self):
        n = int(os.environ.get('TL_PERF_N', '10000'))
        win = 200
        total_cap = float(os.environ.get('TL_PERF_TOTAL', '60.0'))
        tail_cap = float(os.environ.get('TL_PERF_TAIL', '2.0'))
        durs = []
        t_all = time.perf_counter()
        for i in range(n):
            t0 = time.perf_counter()
            TL.append_tl_locked(
                self.gd, _ts(i),
                'perf-%05d op=probe latency sample detail=0123456789abcdef' % i,
                'bench', 'P3')
            durs.append(time.perf_counter() - t0)
        t_all = time.perf_counter() - t_all
        first_win, last_win = sum(durs[:win]), sum(durs[-win:])
        ratio = (last_win / win) / (first_win / win)
        rows = core.read_tsv(os.path.join(self.gd, 'timeline.tsv'), NCOL)
        print('perf: n=%d total=%.2fs first200=%.3fs last200=%.3fs ratio=%.2f'
              % (n, t_all, first_win, last_win, ratio))
        self.assertEqual(len(rows), 8 + n, '万行级账本必须真实长成')
        self.assertTrue(chain_ok(rows), '万行级链完整性')
        self.assertLess(t_all, total_cap,
                        '全程 %.1fs 超阈 %.0fs——O(N²) 整表重写形态' % (t_all, total_cap))
        self.assertLess(last_win, tail_cap,
                        '尾窗 200 事件 %.3fs 超阈 %.1fs——尾部单事件劣化' % (last_win, tail_cap))
        self.assertLess(ratio, 6.0,
                        '尾/首窗均值比 %.1f ≥6——每事件成本随行数增长（O(N²) 特征）' % ratio)


# ---------------------------------------------------------------- ② 字节级兼容

class TestByteCompat(WireBase):
    def _events(self):
        evs = [('2026-10-18T01:00:%02dZ' % i, '总控', 'P3', '事件-%04d 常规' % i, '')
               for i in range(300)]
        evs += [  # 转义律四特殊字符全覆盖（契约 01 §1：BS/tab/CR/LF/分号）
            ('2026-10-18T02:00:00Z', '兼容性\t制表', 'P4', '事件\t内嵌制表', ''),
            ('2026-10-18T02:00:01Z', '总控', 'P4', '多\n行事件\r回车', 'revert-cmd\t2'),
            ('2026-10-18T02:00:02Z', '分号;演员', 'P5', '分号;事件;三连', 'x;1'),
            ('2026-10-18T02:00:03Z', '反斜\\杆', 'P5', '反斜\\杆\\t事件', '\\n'),
        ]
        return evs

    def test_append_bytes_equal_legacy_whole_rewrite(self):
        gd2 = shutil.copytree(FIX, os.path.join(self._tmp.name, 'G-legacy'))
        p2 = os.path.join(gd2, 'timeline.tsv')
        for ts, actor, phase, event, revert in self._events():
            TL.append_tl_locked(self.gd, ts, event, actor, phase, revert)
            # 修前旧算法参考实现（测试内自持）：全量读→算链→整表重写
            rows = core.read_tsv(p2, NCOL)
            row, _ = TL.chained_row(rows, ts, actor, phase, event, revert)
            rows.append(row)
            core.write_tsv(p2, rows)
        self.assertEqual(self.tl_bytes(), self.tl_bytes(gd2),
                         '追加路径与整表重写路径字节级不同——金样/指纹零漂移之根被破')
        self.assertEqual(core.Session(self.gd).validate(), [], 'Session 读面互通零错')

    def test_interleaves_with_whole_rewrite_path(self):
        """追加路径与 Ctx.commit 整表重写形态交错——接链互通（两类写方共存契约）。"""
        p = os.path.join(self.gd, 'timeline.tsv')
        TL.append_tl_locked(self.gd, '2026-10-18T03:00:00Z', '追加-1', 'bench', 'P3')
        rows = core.read_tsv(p, NCOL)
        row, _ = TL.chained_row(rows, '2026-10-18T03:00:01Z', 'CLI', 'P4', '整表重写-1', '')
        rows.append(row)
        core.write_tsv(p, rows)
        TL.append_tl_locked(self.gd, '2026-10-18T03:00:02Z', '追加-2', 'bench', 'P3')
        rows = core.read_tsv(p, NCOL)
        self.assertTrue(chain_ok(rows), '交错接链断')
        self.assertEqual([r[3] for r in rows[-2:]], ['整表重写-1', '追加-2'])


# ---------------------------------------------------------------- ③ 撕裂读封口

class TestReadRowsEpochSeal(WireBase):
    def _seed(self, n=5):
        for i in range(n):
            TL.append_tl_locked(self.gd, _ts(i), '种子-%02d' % i, 'bench', 'P3')

    def test_read_rows_projection_equals_file_and_chain(self):
        self._seed(50)
        rows = TL.read_rows(self.gd)
        self.assertEqual(rows, core.read_tsv(os.path.join(self.gd, 'timeline.tsv'), NCOL),
                         '读路径投影必须等于 timeline.tsv 全量行')
        self.assertEqual(len(rows), 58)
        self.assertTrue(chain_ok(rows))

    def test_transient_epoch_change_retries_then_succeeds(self):
        self._seed()
        calls = {'n': 0}

        def flip_once(gd):
            calls['n'] += 1
            return 1 if calls['n'] == 1 else 42   # 首验=旧世代，其后稳定新世代

        with mock.patch.object(TL, '_read_epoch', side_effect=flip_once):
            rows = TL.read_rows(self.gd)
        self.assertGreater(calls['n'], 2, '窗内变更加必须触发整体重读')
        self.assertTrue(chain_ok(rows))

    def test_persistent_epoch_change_rejects_torn_view(self):
        self._seed()
        counter = itertools.count()
        with mock.patch.object(TL, '_read_epoch', side_effect=lambda gd: next(counter)):
            with self.assertRaises(TL.TornTimelineError):
                TL.read_rows(self.gd)   # 无法证明一致的视图=拒绝返回（fail-closed）

    def test_persistent_torn_tail_fail_closed(self):
        self._seed()
        with open(os.path.join(self.gd, 'timeline.tsv'), 'ab') as f:
            f.write(b'2026-10-18T0')    # 撕裂半行：无 LF 收尾+列数坏
        with self.assertRaises((ValueError, TL.TornTimelineError)):
            TL.read_rows(self.gd)       # 绝不返回含半行的视图


class TestConcurrentAppendReadSeal(WireBase):
    def test_reader_never_sees_torn_view_during_appends(self):
        n = 800
        errors, stop = [], threading.Event()
        views = []

        def writer():
            try:
                for i in range(n):
                    TL.append_tl_locked(self.gd, _ts(i), '并发写-%05d' % i, 'bench', 'P3')
            except Exception as e:      # pragma: no cover - 失败即测试失败
                errors.append(e)
            finally:
                stop.set()

        th = threading.Thread(target=writer)
        th.start()
        try:
            while not stop.is_set():
                rows = TL.read_rows(self.gd)
                views.append(len(rows))
                self.assertTrue(chain_ok(rows),
                                '撕裂视图泄漏：行数=%d' % len(rows))
        finally:
            th.join()
        self.assertEqual(errors, [])
        self.assertEqual(views, sorted(views), '追加只增——视图行数必须单调不减')
        final = TL.read_rows(self.gd)
        self.assertEqual(len(final), 8 + n)
        self.assertTrue(chain_ok(final))


# ---------------------------------------------------------------- ④ 末行损坏 fail-closed

class TestAppendFailClosed(WireBase):
    def test_corrupt_tail_bad_columns_rejected_zero_halfwrite(self):
        TL.append_tl_locked(self.gd, '2026-10-18T04:00:00Z', '正常-1', 'bench', 'P3')
        with open(os.path.join(self.gd, 'timeline.tsv'), 'ab') as f:
            f.write('坏行\t两列'.encode('utf-8') + b'\n')
        before = self.tl_bytes()
        with self.assertRaises(ValueError):
            TL.append_tl_locked(self.gd, '2026-10-18T04:00:01Z', '必然被拒', 'bench', 'P3')
        self.assertEqual(self.tl_bytes(), before, '零半写：拒追加不得动账本一字节')

    def test_torn_tail_missing_lf_rejected_zero_halfwrite(self):
        TL.append_tl_locked(self.gd, '2026-10-18T04:10:00Z', '正常-1', 'bench', 'P3')
        p = os.path.join(self.gd, 'timeline.tsv')
        with open(p, 'r+b') as f:       # 截掉末行 LF=撕裂尾（追加窗中途被杀形态）
            f.seek(-1, os.SEEK_END)
            f.truncate()
        before = self.tl_bytes()
        with self.assertRaises(TL.TornTimelineError):
            TL.append_tl_locked(self.gd, '2026-10-18T04:10:01Z', '必然被拒', 'bench', 'P3')
        self.assertEqual(self.tl_bytes(), before, '零半写：撕裂尾上拒追加')

    def test_ts_required_unchanged(self):
        with self.assertRaises(TypeError):
            TL.append_tl_locked(self.gd)   # EPOCH/墙钟缺省退役律（批次 10 P2#9）不回退


# ---------------------------------------------------------------- ⑤ epoch 工件卫生

class TestEpochHygiene(WireBase):
    def test_epoch_increments_and_stays_out_of_tables(self):
        self.assertEqual(TL._read_epoch(self.gd), 0, '存量 goal 无戳=0 世（引导态）')
        n = 25
        for i in range(n):
            TL.append_tl_locked(self.gd, _ts(i), '卫生-%02d' % i, 'bench', 'P3')
        self.assertEqual(TL._read_epoch(self.gd), n, '每次成功追加恰递增一世')
        self.assertNotIn(EPOCH_NAME, core.TABLES, 'dot 工件不进 13 表（.lock 同律）')
        s = core.Session(self.gd)
        self.assertEqual(s.validate(), [], '读面零干扰')
        self.assertTrue(s.verify_chain()[0])
        self.assertFalse(os.path.exists(os.path.join(self.gd, EPOCH_NAME + '.tmp')),
                         'epoch tmp 残留必须被复用/清扫')


# ------------------------------------------------- ⑥ 尾读边界补齐（接盘 TDD 补齐）

class TestTailEdgeCases(WireBase):
    """O(1) 尾读自身的边界分支——窗口回退/空行文件/冷账本/宽容 epoch/多字节撕裂。

    ⑥-1 单行超窗（> _TAIL_WINDOW）：_tail_bytes 逐窗回退必须取到完整长行——取半行
        = prev_hash 接错 = 链断（O(1) 优化自毁事实源，红线中的红线）；
    ⑥-2 仅空行文件：非 write_tsv 产物——拒追加零半写（与全空判据同源）；
    ⑥-3 冷账本（timeline.tsv 缺失）：GENESIS 起链，Session 读面互通；
    ⑥-4 read_rows 对缺失 timeline.tsv=[]（读投影不虚构文件）；
    ⑥-5 epoch 工件损坏：宽容降 0 世不炸读，追加后正常递增（戳非事实源）；
    ⑥-6 多字节字符半截尾：UTF-8 撕裂=拒追加零半写（fail-closed 同律）。
    """

    def test_row_longer_than_tail_window_backs_off(self):
        long_event = '长行-' + 'x' * (TL._TAIL_WINDOW + 8192)   # ~16KiB，esc 后仍单行
        TL.append_tl_locked(self.gd, '2026-10-18T05:00:00Z', long_event, 'bench', 'P3')
        TL.append_tl_locked(self.gd, '2026-10-18T05:00:01Z', '回退后续行', 'bench', 'P3')
        rows = core.read_tsv(os.path.join(self.gd, 'timeline.tsv'), NCOL)
        self.assertEqual(len(rows), 10)
        self.assertTrue(chain_ok(rows), '长行窗口回退取半行=接链断（prev 取错）')
        self.assertEqual(rows[-1][5], rows[-2][6], '续行 prev_hash 必须接长行 hash')

    def test_blank_only_file_append_fail_closed_zero_halfwrite(self):
        with open(os.path.join(self.gd, 'timeline.tsv'), 'wb') as f:
            f.write(b'\n\n\n')
        before = self.tl_bytes()
        with self.assertRaises(TL.TornTimelineError):
            TL.append_tl_locked(self.gd, '2026-10-18T05:01:00Z', '必然被拒', 'bench', 'P3')
        self.assertEqual(self.tl_bytes(), before, '零半写：空行文件拒追加')

    def test_cold_goal_without_timeline_starts_genesis(self):
        os.unlink(os.path.join(self.gd, 'timeline.tsv'))
        row = TL.append_tl_locked(self.gd, '2026-10-18T05:02:00Z', '冷启动-1', 'bench', 'P3')
        self.assertEqual(row[5], core.GENESIS, '冷账本首行必须接 GENESIS')
        rows = core.read_tsv(os.path.join(self.gd, 'timeline.tsv'), NCOL)
        self.assertEqual(len(rows), 1)
        self.assertTrue(chain_ok(rows))
        self.assertEqual(core.Session(self.gd).validate(), [], 'Session 读面互通零错')
        self.assertTrue(core.Session(self.gd).verify_chain()[0])

    def test_read_rows_missing_timeline_returns_empty(self):
        os.unlink(os.path.join(self.gd, 'timeline.tsv'))
        self.assertEqual(TL.read_rows(self.gd), [], '读投影不得虚构文件')

    def test_epoch_garbage_lenient_zero_then_bumps(self):
        with open(os.path.join(self.gd, EPOCH_NAME), 'w', encoding='utf-8') as f:
            f.write('garbage')
        self.assertEqual(TL._read_epoch(self.gd), 0, '损坏戳宽容降 0 世')
        TL.append_tl_locked(self.gd, '2026-10-18T05:03:00Z', '宽容-1', 'bench', 'P3')
        self.assertEqual(TL._read_epoch(self.gd), 1, '损坏后追加正常递增一世')

    def test_torn_multibyte_tail_rejected_zero_halfwrite(self):
        TL.append_tl_locked(self.gd, '2026-10-18T05:04:00Z', '正常-1', 'bench', 'P3')
        with open(os.path.join(self.gd, 'timeline.tsv'), 'ab') as f:
            f.write('事件中文'.encode('utf-8')[:2])   # 多字节字符半截=追加窗撕裂形态
        before = self.tl_bytes()
        with self.assertRaises((TL.TornTimelineError, ValueError)):
            TL.append_tl_locked(self.gd, '2026-10-18T05:04:01Z', '必然被拒', 'bench', 'P3')
        self.assertEqual(self.tl_bytes(), before, '零半写：多字节撕裂尾拒追加')


if __name__ == '__main__':
    unittest.main()
