#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""远程 API 客户端单元测试（无需真实服务，mock urllib）。

覆盖：健康检查/鉴权头、扫描参数编码（中文路径）、POST JSON 体、
HTTP 错误 detail 透传、网络不可达错误。
"""

import io
import json
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, __file__.rsplit("/", 2)[0])

from ui.remote_mode import RemoteApiClient, RemoteApiError


class _FakeResp:
    """模拟 urlopen 成功响应。"""

    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestRemoteApiClient(unittest.TestCase):

    def test_health_success_and_auth_header(self):
        with mock.patch("urllib.request.urlopen",
                        return_value=_FakeResp({"app": "x", "version": "1.0", "status": "ok"})) as m:
            h = RemoteApiClient("http://nas:8123/", "tok").health()
        self.assertEqual(h["status"], "ok")
        req = m.call_args[0][0]
        self.assertEqual(req.full_url, "http://nas:8123/api/health")
        self.assertEqual(req.get_header("Authorization"), "Bearer tok")

    def test_scan_encodes_chinese_path(self):
        with mock.patch("urllib.request.urlopen",
                        return_value=_FakeResp({"total": 1, "files": []})) as m:
            RemoteApiClient("http://nas:8123", "t").scan("/媒体 目录", recursive=True)
        req = m.call_args[0][0]
        self.assertIn("path=%2F%E5%AA%92%E4%BD%93+%E7%9B%AE%E5%BD%95", req.full_url)
        self.assertIn("recursive=true", req.full_url)

    def test_rename_posts_json_body(self):
        with mock.patch("urllib.request.urlopen",
                        return_value=_FakeResp({"results": [{"ok": True}]})) as m:
            r = RemoteApiClient("http://nas:8123", "t").rename(
                "/d", [{"old": "a.mkv", "new": "b.mkv"}], dry_run=False)
        self.assertTrue(r["results"][0]["ok"])
        req = m.call_args[0][0]
        self.assertEqual(req.get_method(), "POST")
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["dry_run"], False)
        self.assertEqual(body["renames"][0]["old"], "a.mkv")
        self.assertIn("Content-type", [k for k, _ in req.header_items()])

    def test_http_error_passes_detail(self):
        fp = io.BytesIO(json.dumps({"detail": "未授权"}).encode("utf-8"))
        err = urllib.error.HTTPError("http://nas:8123/api/health", 401,
                                     "Unauthorized", {}, fp)
        with mock.patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(RemoteApiError) as ctx:
                RemoteApiClient("http://nas:8123", "bad").health()
        self.assertEqual(ctx.exception.status, 401)
        self.assertIn("未授权", str(ctx.exception))

    def test_unreachable_host(self):
        with mock.patch("urllib.request.urlopen",
                        side_effect=urllib.error.URLError("connect refused")):
            with self.assertRaises(RemoteApiError) as ctx:
                RemoteApiClient("http://nas:1", "t").health()
        self.assertIsNone(ctx.exception.status)
        self.assertIn("无法连接", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
