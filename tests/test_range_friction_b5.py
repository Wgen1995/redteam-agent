# -*- coding: utf-8 -*-
"""battle-5 T3a（P3 蓝军三项之落地两项）：防御摩擦种子回归。

①svc-api-gw 面级限流（30req/10s 滚动窗→429+Retry-After；per-route 之上）
②svc-shop 诱饵面（/wp-admin、/admin.php、/.git——拟真 200 噪声无 marker）。
端口异构+认证加权=GT v4 面改版项，本批不做（dict 勘误另记）。
种子以线程内 HTTPServer 实测（不依赖 docker）。"""
import importlib.util
import os
import threading
import time
import unittest
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = os.path.join(HERE, 'range', 'seed')


def _spawn(name, port_holder):
    spec = importlib.util.spec_from_file_location(
        name.replace('-', '_'), os.path.join(SEED, name, 'app.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    srv = mod.make_server('127.0.0.1', 0) if hasattr(mod, 'make_server') else None
    if srv is None:
        from http.server import HTTPServer
        srv = HTTPServer(('127.0.0.1', 0), mod.H)
    port_holder.append(srv.server_address[1])
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        r = urllib.request.urlopen(req, timeout=5)
        return r.status, r.read().decode('utf-8', 'replace'), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), dict(e.headers)


class TestGwGlobalThrottle(unittest.TestCase):
    def test_burst_throttled_with_retry_after(self):
        ph = []
        srv = _spawn('svc-api-gw', ph)
        base = 'http://127.0.0.1:%d/fetch' % ph[0]
        codes = [_get(base)[0] for _ in range(34)]     # 无退避连喷
        self.assertEqual(codes[-1], 429)
        self.assertEqual(codes[0], 200)
        # 退避后恢复（窗 10s 太长——直接验证 429 带 Retry-After 头）
        st, _b, hd = _get(base)
        self.assertEqual(st, 429)
        self.assertIn('Retry-After', hd)
        srv.shutdown()

    def test_slow_pace_unaffected(self):
        ph = []
        srv = _spawn('svc-api-gw', ph)
        base = 'http://127.0.0.1:%d/fetch' % ph[0]
        codes = []
        for _ in range(6):
            codes.append(_get(base)[0])
            time.sleep(0.35)                          # ~3req/s=正常探测节奏
        self.assertTrue(all(c == 200 for c in codes))
        srv.shutdown()


class TestShopDecoys(unittest.TestCase):
    def test_decoys_realistic_but_marker_free(self):
        ph = []
        srv = _spawn('svc-shop', ph)
        for path in ('/wp-admin/setup.php', '/admin.php', '/.git/config'):
            st, body, _h = _get('http://127.0.0.1:%d%s' % (ph[0], path))
            self.assertEqual(st, 200, path)
            self.assertNotIn('GT', body, '诱饵无 marker（噪声非靶）')
        # 正身路由不受影响
        st, body, _h = _get('http://127.0.0.1:%d/item?id=1' % ph[0])
        self.assertEqual(st, 200)
        self.assertIn('GTSQLI-01', body)
        srv.shutdown()


if __name__ == '__main__':
    unittest.main()
