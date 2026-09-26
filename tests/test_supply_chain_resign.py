# -*- coding: utf-8 -*-
"""批次 6 T9：tools.lock 全量 8 键+G-22 重签通道+G-32 refresh-cve（TDD 红→绿）。

断言面：
- 重签脚本闭环（roundtrip）：TEST 钥（tests/fixtures/keys/test-signing-key.pem，与
  engines/nuclei/release.pub 配对）重签临时锁副本 → load_lock 全键 verify_entry PASS
  ——信任锚=release.pub，私钥只进签名侧；
- 信任链未断声明：重签后手改任一键 sha256 → 该键 verify FAIL（fail-closed）；
- 锁全量化：8 键在册（openssl/nuclei/nuclei-templates + python/docker + 三自写引擎
  目录清单键）；
- G-32 refresh-cve：file:// 合法快照原子落盘（首行 snapshot-date=--timestamp 值、
  七列 lint 复用 rc==0、install-log.tsv 追加 refresh-cve 行）；六列坏快照 rc==1 且
  目标文件字节不变（先临时校验再原子替换的反向断言）。
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(REPO, "cli"))
from ledger import install_core, supply_chain  # noqa: E402

TS = "2026-09-24T00:00:00Z"
LOCK = os.path.join(REPO, "tools.lock")
PUBKEY = os.path.join(REPO, "engines", "nuclei", "release.pub")
TESTKEY = os.path.join(HERE, "fixtures", "keys", "test-signing-key.pem")
RESIGN = os.path.join(REPO, "install", "resign-tools-lock.py")
GOOD_SNAP = os.path.join(HERE, "fixtures", "cve", "snapshot-good.tsv")
KNOWLEDGE_CLI = os.path.join(REPO, "cli", "tanyin-knowledge")
ENV = {**os.environ, "PYTHONUTF8": "1"}

EIGHT_KEYS = {"python", "docker", "engines-web-blackbox", "engines-vuln-agent",
              "engines-session-viz", "openssl", "nuclei", "nuclei-templates"}


class TestResign(unittest.TestCase):
    def test_resign_roundtrip(self):
        """tempfile 拷 tools.lock+TEST 钥 → resign 脚本 subprocess → 全键 verify PASS。"""
        with tempfile.TemporaryDirectory() as d:
            tmplock = os.path.join(d, "tools.lock")
            with open(LOCK, encoding="utf-8") as f:
                content = f.read()
            with open(tmplock, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            r = subprocess.run([sys.executable, RESIGN, "--lock", tmplock,
                                "--key", TESTKEY],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=ENV, timeout=600)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            for e in supply_chain.load_lock(tmplock).values():
                ok, reason = supply_chain.verify_entry(e, PUBKEY)
                self.assertTrue(ok, "%s: %s" % (e["key"], reason))

    def test_resign_detects_tamper(self):
        """重签后手改一键 sha256 → verify FAIL（信任链未断声明成立）。"""
        with tempfile.TemporaryDirectory() as d:
            tmplock = os.path.join(d, "tools.lock")
            with open(LOCK, encoding="utf-8") as f:
                content = f.read()
            with open(tmplock, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            r = subprocess.run([sys.executable, RESIGN, "--lock", tmplock,
                                "--key", TESTKEY],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=ENV, timeout=600)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            with open(tmplock, encoding="utf-8") as f:
                tampered = f.read()
            first = supply_chain.load_lock(tmplock)["openssl"]
            self.assertIn(first["sha256"], tampered, "篡改探针须命中真实 sha256")
            tampered = tampered.replace(first["sha256"], "0" * 64, 1)
            with open(tmplock, "w", encoding="utf-8", newline="\n") as f:
                f.write(tampered)
            ok, _why = supply_chain.verify_entry(
                supply_chain.load_lock(tmplock)["openssl"], PUBKEY)
            self.assertFalse(ok, "被篡改键必须验签失败（fail-closed）")

    def test_lock_fullness(self):
        """tools.lock 8 键清单在册（键 3→8 全量化）。"""
        names = set(supply_chain.load_lock(LOCK))
        self.assertTrue(EIGHT_KEYS <= names,
                        "缺键: %s" % ", ".join(sorted(EIGHT_KEYS - names)))


def _runtime_kdir(d):
    """运行时知识库：种子库树拷贝（=安装 step5 init-home 形态；staging/ 载体在位），
    cve-snapshot.tsv 起始字节=仓库种子现值（原子性断言基线）。"""
    import shutil
    kd = os.path.join(d, "knowledge")
    shutil.copytree(os.path.join(REPO, "knowledge"), kd,
                    ignore=shutil.ignore_patterns("__pycache__"))
    dst = os.path.join(kd, "cve", "cve-snapshot.tsv")
    with open(dst, encoding="utf-8") as f:
        base = f.read()
    return kd, dst, base


class TestRefreshCve(unittest.TestCase):
    def test_refresh_from_file_atomic(self):
        """file:// 合法快照（14 行七列）→ refresh_cve 原子落盘三断言：
        首行 snapshot-date=--timestamp 值；tanyin-knowledge lint rc==0；
        install-log.tsv 追加 refresh-cve 行（sha256 记录在场）。"""
        with tempfile.TemporaryDirectory() as d:
            kd, dst, _base = _runtime_kdir(d)
            rc, msg = install_core.refresh_cve("file://" + GOOD_SNAP, kd, TS)
            self.assertEqual(rc, 0, msg)
            with open(dst, encoding="utf-8") as f:
                lines = f.read().splitlines()
            self.assertEqual(lines[0], "# snapshot-date: " + TS)
            self.assertIn("sha256=", msg)
            r = subprocess.run([sys.executable, KNOWLEDGE_CLI, "lint",
                                "--knowledge-dir", kd, "--timestamp", TS],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=ENV, timeout=300)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            with open(os.path.join(d, "install-log.tsv"), encoding="utf-8") as f:
                log = f.read()
            self.assertIn("refresh-cve", log)
            self.assertIn("sha256=", log)

    def test_refresh_rejects_bad_columns(self):
        """六列坏快照 → rc==1 且目标文件字节不变（先临时校验再原子替换）。"""
        with tempfile.TemporaryDirectory() as d:
            kd, dst, base = _runtime_kdir(d)
            bad = os.path.join(d, "snapshot-bad.tsv")
            with open(GOOD_SNAP, encoding="utf-8") as f:
                rows = f.read().splitlines()
            mangled = rows[1].split("\t")[:-1]           # 首数据行砍成六列
            self.assertEqual(len(mangled), 6)
            with open(bad, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join([rows[0]] + ["\t".join(mangled)] + rows[2:]) + "\n")
            rc, msg = install_core.refresh_cve("file://" + bad, kd, TS)
            self.assertEqual(rc, 1, msg)
            with open(dst, encoding="utf-8") as f:
                self.assertEqual(f.read(), base, "lint 不过=目标文件字节零变化")


if __name__ == "__main__":
    unittest.main()
