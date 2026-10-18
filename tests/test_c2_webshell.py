# -*- coding: utf-8 -*-
"""WebShell 受控档测试——会话=账本行族 open→exec→close; 命令过 guard deny
(enforce 单源副作用黑名单)+revert 义务(副作用必登记回滚,义务未清不得关档);
回环集成=真 socket 127.0.0.1 临时口全链(队列→拉取→HTTP 回传→回显证据化)。
禁碰口 8900/3000/8787/8443 只作被拒 URL 口号出现,从不 bind。"""
import hashlib
import http.client
import socket
import threading
import unittest

from test_c2_common import T0, boot_beacon, boot_c2, ts

from cli.c2 import echo, queue, webshell
from cli.c2.store import C2Error, C2Store
from cli.c2.tables import PORT_DENYLIST, cols


class TestWebshell(unittest.TestCase):
    """WebShell 受控档: open 过 URL 门(禁碰口+bounds 域),exec 过 guard deny。"""

    def setUp(self):
        self.d, self.gd, self.iid = boot_c2()
        self.addCleanup(self.d.cleanup)

    def _open(self, url="http://127.0.0.1/cmd.php", ts_=ts(1)):
        return webshell.open_session(self.gd, ts_, url, self.iid)

    def test_open_session_ok(self):
        sid, row = self._open()
        self.assertTrue(sid.startswith("WSH-"))
        ci = {k: i for i, k in enumerate(cols("webshells.tsv"))}
        self.assertEqual(row[ci["kind"]], "open")
        self.assertTrue(row[ci["deny_check"]].startswith("pass:"),
                        "开档即记 guard 判定")

    def test_open_banned_ports_rejected(self):
        for port in PORT_DENYLIST:
            with self.assertRaises(C2Error):
                self._open("http://127.0.0.1:%d/cmd.php" % port)
        self.assertEqual(C2Store(self.gd).read("webshells.tsv"), [], "禁碰口零行落账")

    def test_open_bad_url_rejected(self):
        with self.assertRaises(C2Error):
            self._open("ftp://127.0.0.1/cmd.php")
        with self.assertRaises(C2Error):
            self._open("http:///cmd.php")

    def test_open_unknown_intent_rejected(self):
        with self.assertRaises(C2Error):
            webshell.open_session(self.gd, ts(1), "http://127.0.0.1/c.php", "INT-c2t-9999")

    def test_open_out_of_bounds_host_stops(self):
        with self.assertRaises(C2Error):
            self._open("http://10.0.0.5/cmd.php")

    def test_exec_pass_records_row(self):
        sid, _ = self._open()
        r = webshell.exec_cmd(self.gd, sid, "whoami", ts(2))
        self.assertEqual(r["deny_check"], "pass")
        s = [x for x in webshell.sessions(self.gd) if x["id"] == sid][0]
        self.assertEqual((s["state"], s["execs"], s["denies"]), ("open", 1, 0))

    def test_exec_denied_command_rejected_and_audited(self):
        sid, _ = self._open()
        with self.assertRaises(C2Error):
            webshell.exec_cmd(self.gd, sid, "rm -rf /", ts(2))
        s = [x for x in webshell.sessions(self.gd) if x["id"] == sid][0]
        self.assertEqual(s["denies"], 1, "拒执行也入账(每次执行仍入账)")
        self.assertEqual(s["execs"], 0)

    def test_exec_shell_wrapper_escape_denied(self):
        sid, _ = self._open()
        with self.assertRaises(C2Error):
            webshell.exec_cmd(self.gd, sid, ["sh", "-c", "rm -r -f /"], ts(2))

    def test_exec_unknown_or_closed_session_rejected(self):
        with self.assertRaises(C2Error):
            webshell.exec_cmd(self.gd, "WSH-c2t-9999", "id", ts(1))
        sid, _ = self._open()
        webshell.exec_cmd(self.gd, sid, "id", ts(2), side_effect="写 /tmp/x",
                          revert_cmd="rm /tmp/x")
        webshell.settle_revert(self.gd, webshell.obligations(self.gd, sid)[0]["id"], ts(3))
        webshell.close_session(self.gd, sid, ts(4))
        with self.assertRaises(C2Error):
            webshell.exec_cmd(self.gd, sid, "id", ts(5))

    def test_exec_side_effect_requires_revert_cmd(self):
        sid, _ = self._open()
        with self.assertRaises(C2Error):
            webshell.exec_cmd(self.gd, sid, "id", ts(2), side_effect="落地 webshell")
        self.assertEqual(webshell.obligations(self.gd, sid), [], "无 revert_cmd 不入义务")

    def test_exec_registers_revert_obligation(self):
        sid, _ = self._open()
        r = webshell.exec_cmd(self.gd, sid, "id", ts(2), side_effect="写 crontab 持久化",
                              revert_cmd="crontab -r")
        self.assertTrue(r["revert_id"].startswith("RVT-"))
        obs = webshell.obligations(self.gd, sid)
        self.assertEqual(len(obs), 1)
        self.assertEqual(obs[0]["status"], "pending")
        self.assertEqual(obs[0]["revert_cmd"], "crontab -r")

    def test_close_blocked_while_obligation_open(self):
        sid, _ = self._open()
        webshell.exec_cmd(self.gd, sid, "id", ts(2), side_effect="x", revert_cmd="y")
        with self.assertRaises(C2Error):
            webshell.close_session(self.gd, sid, ts(3))
        s = [x for x in webshell.sessions(self.gd) if x["id"] == sid][0]
        self.assertEqual(s["state"], "open", "义务未清关档失败")

    def test_settle_then_close(self):
        sid, _ = self._open()
        webshell.exec_cmd(self.gd, sid, "id", ts(2), side_effect="x", revert_cmd="y")
        rid = webshell.obligations(self.gd, sid)[0]["id"]
        webshell.settle_revert(self.gd, rid, ts(3))
        self.assertEqual(webshell.obligations(self.gd, sid), [], "履约后义务清")
        row = webshell.close_session(self.gd, sid, ts(4))
        self.assertEqual(row[1], "close")
        s = [x for x in webshell.sessions(self.gd) if x["id"] == sid][0]
        self.assertEqual(s["state"], "closed")

    def test_settle_unknown_revert_rejected(self):
        with self.assertRaises(C2Error):
            webshell.settle_revert(self.gd, "RVT-c2t-9999", ts(1))

    def test_close_unknown_session_rejected(self):
        with self.assertRaises(C2Error):
            webshell.close_session(self.gd, "WSH-c2t-9999", ts(1))


class TestLoopbackRoundtrip(unittest.TestCase):
    """本地回环全链: 指令队列→beacon 拉取→HTTP 回传(127.0.0.1 临时口)→
    回显证据化。socket 只 bind 127.0.0.1:0(内核临时口),禁碰口零接触。"""

    def test_queue_pull_http_echo_full_chain(self):
        d, gd, iid, bid = boot_beacon("G-loop")
        self.addCleanup(d.cleanup)
        ready = threading.Event()
        holder = {}

        def serve():
            srv = socket.socket()
            srv.bind(("127.0.0.1", 0))
            srv.listen(1)
            holder["port"] = srv.getsockname()[1]
            ready.set()
            conn, _ = srv.accept()
            holder["req"] = conn.recv(65536).decode("utf-8", "replace")
            body = b"uid=0(root) gid=0(root)\n"
            conn.sendall(b"HTTP/1.0 200 OK\r\nContent-Length: %d\r\n\r\n"
                         % len(body) + body)
            conn.close()
            srv.close()

        t = threading.Thread(target=serve)
        t.start()
        self.addCleanup(t.join, 5)
        ready.wait(5)
        port = holder["port"]
        self.assertNotIn(port, PORT_DENYLIST, "回环口=内核临时口,恒非禁碰口")

        sid, _ = webshell.open_session(gd, ts(1), "http://127.0.0.1:%d/cmd.php" % port, iid)
        cid, _ = queue.enqueue(gd, bid, "id", ts(2))
        cmds, _cursor = queue.pull(gd, bid, ts(3))
        self.assertEqual(cmds[0]["argv"], "id")

        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("POST", "/cmd.php", body="id",
                     headers={"X-Webshell-Session": sid})
        resp = conn.getresponse()
        data = resp.read()
        conn.close()

        self.assertIn("id", holder["req"], "回环面真收到了指令载荷")
        r = echo.submit(gd, cid, data, ts(4))
        self.assertEqual(r["digest"], hashlib.sha256(data).hexdigest(),
                         "回显锚 HTTP 回传字节")
        t.join(5)


if __name__ == "__main__":
    unittest.main()
