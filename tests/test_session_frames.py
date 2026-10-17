# -*- coding: utf-8 -*-
"""W2·C:G2 runner 事件帧化+call_id——修 session_view.py:15 解析脆弱点。

来源：docs/reviews/2026-10-18-realign/C-zhulong-multica-全件对齐.md G2
「runner.tsv 帧化：kind 枚举化+call_id 列+schema_version 锚；opencode TUI 文本
捕获无 tool_use/result id（session_view.py:15），格式漂移即解析崩」——
帧化自家契约（NDJSON，schema_version=1）：tool_use/tool_result 按 call_id 精确
配对（不再按行首标记猜）；opencode TUI 无 id 的旧路径原样保留（帧文件缺席/
无战士帧 → 回落标记法，兼容律）。

跑法：python3 -m unittest tests.test_session_frames -v
"""
import json, os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "..", "cli")
sys.path.insert(0, CLI)

from ledger import frames as fr          # noqa: E402
from ledger import session_view as sv    # noqa: E402


def _mk_battle(root, n, log_text=None, frames_lines=(), tsv_text=""):
    home = os.path.join(root, "battle-%d" % n)
    os.makedirs(home, exist_ok=True)
    if log_text is not None:
        with open(os.path.join(home, sv.TRANSCRIPT_NAME), "w", encoding="utf-8") as f:
            f.write(log_text)
    if frames_lines:
        with open(os.path.join(home, sv.FRAMES_NAME), "w", encoding="utf-8") as f:
            f.write("".join(l + "\n" for l in frames_lines))
    if tsv_text:
        with open(os.path.join(home, sv.RUNNER_TSV_NAME), "w", encoding="utf-8") as f:
            f.write(tsv_text)
    return home


class TestFramesContract(unittest.TestCase):
    """帧契约：schema_version 锚+kind 枚举+call_id 配对（写入→读回→投影）。"""

    def test_dump_parse_roundtrip_schema_anchored(self):
        f = fr.dump_frame("2026-10-20T08:00:00", "tool_use",
                          call_id="call-1", tool="Read", title="Read a.txt")
        self.assertEqual(f["schema_version"], fr.FRAMES_SCHEMA_VERSION)
        parsed = fr.parse_frames(json.dumps(f))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["kind"], "tool_use")
        self.assertEqual(parsed[0]["call_id"], "call-1")

    def test_parse_skips_blank_and_bad_lines(self):
        text = "\n".join(["", "not json", json.dumps(fr.dump_frame("t", "text", text="hi")), ""])
        self.assertEqual(len(fr.parse_frames(text)), 1)

    def test_append_frame_assigns_seq_in_order(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "x.frames.ndjson")
        fr.append_frame(p, "t1", "LAUNCH", detail="pid=1")
        fr.append_frame(p, "t2", "RESTART", detail="pid=2")
        got = fr.parse_frames(open(p, encoding="utf-8").read())
        self.assertEqual([f["seq"] for f in got], [1, 2])
        self.assertEqual([f["kind"] for f in got], ["LAUNCH", "RESTART"])

    def test_pair_merges_by_call_id_out_of_order(self):
        """配对按 id 不按位置：use A/use B → result B(error)/result A(ok) 乱序回。"""
        frames = [
            fr.dump_frame("t1", "round", title="> build"),
            fr.dump_frame("t2", "tool_use", call_id="A", tool="Read", title="Read a"),
            fr.dump_frame("t3", "tool_use", call_id="B", tool="Bash", title="$ ls"),
            fr.dump_frame("t4", "tool_result", call_id="B", state="error",
                          output=["Error: boom"]),
            fr.dump_frame("t5", "tool_result", call_id="A", state="ok", output=["ok-a"]),
        ]
        rounds = fr.frames_to_rounds(frames)
        self.assertEqual(len(rounds), 1)
        cards = [e for e in rounds[0]["entries"] if e["kind"] == "tool"]
        by_id = {c["call_id"]: c for c in cards}
        self.assertTrue(by_id["A"]["paired"])
        self.assertEqual(by_id["A"]["state"], "ok")
        self.assertEqual(by_id["A"]["output"], ["ok-a"])
        self.assertEqual(by_id["A"]["tool"], "Read")
        self.assertTrue(by_id["B"]["paired"])
        self.assertEqual(by_id["B"]["state"], "error")
        self.assertEqual(by_id["B"]["output"], ["Error: boom"])

    def test_unpaired_use_is_open_not_fabricated(self):
        frames = [fr.dump_frame("t1", "tool_use", call_id="C", tool="Grep", title="Grep x")]
        cards = [e for e in fr.frames_to_rounds(frames)[0]["entries"]
                 if e["kind"] == "tool"]
        self.assertFalse(cards[0]["paired"])
        self.assertEqual(cards[0]["state"], "open")   # 未回结果=开卡，不伪造 ok
        self.assertEqual(cards[0]["output"], [])

    def test_orphan_result_kept_with_flag(self):
        frames = [fr.dump_frame("t1", "tool_result", call_id="Z", state="ok", output=["z"])]
        cards = [e for e in fr.frames_to_rounds(frames)[0]["entries"]
                 if e["kind"] == "tool"]
        self.assertTrue(cards[0]["orphan"])
        self.assertEqual(cards[0]["call_id"], "Z")

    def test_round_and_text_frames_project(self):
        frames = [
            fr.dump_frame("t1", "round", title="> round one"),
            fr.dump_frame("t2", "text", text="第一段\n\n第二段"),
            fr.dump_frame("t3", "round", title="> round two"),
            fr.dump_frame("t4", "text", text="尾轮"),
        ]
        rounds = fr.frames_to_rounds(frames)
        self.assertEqual([r["head"] for r in rounds], ["> round one", "> round two"])
        self.assertEqual(rounds[0]["entries"][0]["kind"], "text")
        self.assertEqual(rounds[0]["entries"][0]["lines"], ["第一段", "", "第二段"])

    def test_lifecycle_frames_not_round_entries(self):
        """runner 生命周期帧不入会话条目（session_view 另从 runner.tsv 穿插，
        双计防御）。"""
        frames = [fr.dump_frame("t1", "BOOT", detail="cwd=x"),
                  fr.dump_frame("t2", "text", text="hi")]
        rounds = fr.frames_to_rounds(frames)
        kinds = [e["kind"] for r in rounds for e in r["entries"]]
        self.assertEqual(kinds, ["text"])


LEGACY_LOG = "".join([
    "> build · glm-5.3\n",
    "开场白。\n",
    "$ echo hi\n",
    "hi\n",
    "→ Read mission.txt\n",
    "读完了。\n",
])


class TestSessionViewFramesFirst(unittest.TestCase):
    """session_view 帧优先：有战士帧用帧（call_id 配对），否则回落标记法。"""

    def setUp(self):
        self.root = tempfile.mkdtemp()

    def test_frames_present_wins_over_markers(self):
        frames_lines = [
            json.dumps(fr.dump_frame("t1", "round", title="> build")),
            json.dumps(fr.dump_frame("t2", "tool_use", call_id="c1",
                                     tool="Read", title="Read mission.txt")),
            json.dumps(fr.dump_frame("t3", "tool_result", call_id="c1",
                                     state="ok", output=["line1"])),
        ]
        home = _mk_battle(self.root, 1, log_text=LEGACY_LOG, frames_lines=frames_lines)
        doc = sv.session_view(home)
        entries = doc["rounds"][0]["entries"]
        tools = [e for e in entries if e["kind"] == "tool"]
        self.assertTrue(tools, "帧路径应产出工具卡")
        self.assertEqual(tools[0]["call_id"], "c1")
        self.assertTrue(tools[0]["paired"])
        self.assertEqual(tools[0]["state"], "ok")
        # 标记法特征（bash 命令卡）不得在场——证明走了帧路径而非猜路径
        self.assertFalse(any(e.get("state") == "bash" for e in entries))

    def test_frames_without_warrior_frames_falls_back(self):
        """帧文件只有 runner 生命周期帧（无战士帧）→ 回落标记法（兼容律：
        帧文件在场但无战士面数据时不得清空会话页）。"""
        frames_lines = [json.dumps(fr.dump_frame("t1", "BOOT", detail="cwd=x"))]
        home = _mk_battle(self.root, 2, log_text=LEGACY_LOG, frames_lines=frames_lines)
        doc = sv.session_view(home)
        entries = doc["rounds"][0]["entries"]
        self.assertTrue(any(e.get("state") == "bash" for e in entries))   # 标记法特征
        self.assertEqual(doc["stats"]["bash"], 1)

    def test_legacy_no_frames_uses_markers_unchanged(self):
        home = _mk_battle(self.root, 3, log_text=LEGACY_LOG)
        doc = sv.session_view(home)
        expected = sv.parse_transcript(LEGACY_LOG)
        self.assertEqual(doc["rounds"], expected)          # 逐字节同构（兼容钉）
        self.assertEqual(doc["stats"]["bash"], 1)
        self.assertEqual(doc["stats"]["tools"], 2)


class TestRunnerDualWrite(unittest.TestCase):
    """runner log_event 双写：runner.tsv 行 + frames 帧（先写帧后杀的审计底座）。"""

    def _load_runner(self):
        import importlib.util
        path = os.path.join(CLI, "tanyin-runner")
        loader = importlib.machinery.SourceFileLoader("tanyin_runner_mod", path)
        spec = importlib.util.spec_from_loader("tanyin_runner_mod", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod

    def test_log_event_writes_tsv_and_frame(self):
        mod = self._load_runner()
        d = tempfile.mkdtemp()
        runner_log = os.path.join(d, "opencode-run.log.runner.tsv")
        mod.log_event(runner_log, "BOOT", "cwd=/x max_restarts=5")
        self.assertTrue(os.path.isfile(runner_log))
        frames_path = os.path.join(d, sv.FRAMES_NAME)
        self.assertTrue(os.path.isfile(frames_path),
                        "帧文件应与 runner.tsv 同基名（.frames.ndjson）")
        got = fr.parse_frames(open(frames_path, encoding="utf-8").read())
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["kind"], "BOOT")
        self.assertEqual(got[0]["schema_version"], fr.FRAMES_SCHEMA_VERSION)
        self.assertIn("cwd=/x", got[0]["detail"])


if __name__ == "__main__":
    unittest.main()
