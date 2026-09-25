#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""远程模式：桌面版 GUI 接入 NAS API 服务（server/app.py）。

本地/远程双模式：桌面版既能操作本地文件，也可连接 NAS 服务
浏览目录 → 解析预览 → 一键重命名（自动备份）。
仅使用标准库（urllib），不引入额外依赖。
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QDialog, QGroupBox, QHBoxLayout, QHeaderView,
                             QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)


# ============ API 客户端 ============
class RemoteApiError(Exception):
    """远程 API 调用错误（HTTP 状态码 + 服务端 detail）。"""

    def __init__(self, status: Optional[int], message: str):
        self.status = status
        super().__init__(message)


class RemoteApiClient:
    """NAS 服务客户端（health/scan/rename-preview/rename）。"""

    def __init__(self, base_url: str, token: str, timeout: int = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token.strip()
        self.timeout = timeout

    def _request(self, method: str, path: str,
                 params: Optional[Dict[str, Any]] = None,
                 body: Optional[Dict[str, Any]] = None) -> Any:
        url = self.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {"Authorization": f"Bearer {self.token}"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.loads(e.read().decode("utf-8")).get("detail", "")
            except Exception:
                pass
            raise RemoteApiError(e.code, detail or f"HTTP {e.code}") from e
        except urllib.error.URLError as e:
            raise RemoteApiError(None, f"无法连接服务器: {e.reason}") from e

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/api/health")

    def scan(self, path: str, recursive: bool = True) -> Dict[str, Any]:
        return self._request("GET", "/api/scan",
                             {"path": path, "recursive": str(recursive).lower()})

    def rename_preview(self, path: str, filenames: List[str]) -> Dict[str, Any]:
        return self._request("POST", "/api/rename-preview",
                             body={"path": path, "filenames": filenames})

    def rename(self, path: str, renames: List[Dict[str, str]], dry_run: bool = True) -> Dict[str, Any]:
        return self._request("POST", "/api/rename",
                             body={"path": path, "renames": renames, "dry_run": dry_run})


# ============ 后台线程（避免网络请求阻塞 UI） ============
class RemoteWorker(QThread):
    finished_ok = pyqtSignal(object)      # 成功：返回结果
    finished_err = pyqtSignal(str)        # 失败：错误消息

    def __init__(self, fn, *args, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._fn = fn
        self._args = args

    def run(self) -> None:
        try:
            self.finished_ok.emit(self._fn(*self._args))
        except Exception as e:
            self.finished_err.emit(str(e))


# ============ 远程模式对话框 ============
class RemoteModeDialog(QDialog):
    """远程模式：连接 NAS 服务进行扫描与重命名。"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("连接 NAS 服务（远程模式）")
        self.resize(960, 640)
        self.setMinimumSize(720, 480)

        self._client: Optional[RemoteApiClient] = None
        self._worker: Optional[RemoteWorker] = None
        self._items: List[Dict[str, Any]] = []   # scan 结果（含 name/suggested_name/analysis）
        self._connected = False

        self._build_ui()
        self._apply_style()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # 连接区
        conn_box = QGroupBox("🔌 服务连接")
        conn_layout = QHBoxLayout()
        self.url_edit = QLineEdit("http://127.0.0.1:8123")
        self.url_edit.setPlaceholderText("NAS 服务地址，如 http://192.168.1.100:8123")
        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText("API Token")
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.connect_btn = QPushButton("连接")
        self.conn_status = QLabel("未连接")
        self.conn_status.setStyleSheet("color: #95a5a6;")
        conn_layout.addWidget(QLabel("地址:"))
        conn_layout.addWidget(self.url_edit, 3)
        conn_layout.addWidget(QLabel("Token:"))
        conn_layout.addWidget(self.token_edit, 2)
        conn_layout.addWidget(self.connect_btn)
        conn_layout.addWidget(self.conn_status)
        conn_box.setLayout(conn_layout)
        layout.addWidget(conn_box)

        # 目录区
        path_box = QGroupBox("📁 媒体目录")
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit("/media")
        self.path_edit.setPlaceholderText("NAS 上的媒体目录，如 /media/视频")
        self.scan_btn = QPushButton("扫描")
        self.scan_btn.setEnabled(False)
        path_layout.addWidget(self.path_edit, 1)
        path_layout.addWidget(self.scan_btn)
        path_box.setLayout(path_layout)
        layout.addWidget(path_box)

        # 文件表
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["重命名", "文件名", "建议名", "类型"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self._on_cell_clicked)
        layout.addWidget(self.table, 1)

        # 状态行
        self.table_status = QLabel("尚未扫描")
        self.table_status.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.table_status)

        # 操作区
        op_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.clear_btn = QPushButton("清空")
        self.filter_btn = QPushButton("仅需改名")
        self.filter_btn.setCheckable(True)
        self.preview_btn = QPushButton("预览重命名")
        self.apply_btn = QPushButton("✅ 执行重命名")
        self.apply_btn.setEnabled(False)
        for b in (self.select_all_btn, self.clear_btn, self.filter_btn, self.preview_btn, self.apply_btn):
            b.setEnabled(False)
        op_layout.addWidget(self.select_all_btn)
        op_layout.addWidget(self.clear_btn)
        op_layout.addWidget(self.filter_btn)
        op_layout.addStretch()
        op_layout.addWidget(self.preview_btn)
        op_layout.addWidget(self.apply_btn)
        layout.addLayout(op_layout)

        self.setLayout(layout)

        # 信号连接
        self.connect_btn.clicked.connect(self._connect)
        self.scan_btn.clicked.connect(self._scan)
        self.select_all_btn.clicked.connect(lambda: self._set_all_checked(True))
        self.clear_btn.clicked.connect(lambda: self._set_all_checked(False))
        self.filter_btn.toggled.connect(lambda _: self._refresh_table())
        self.preview_btn.clicked.connect(self._preview)
        self.apply_btn.clicked.connect(self._apply)
        self.token_edit.returnPressed.connect(self._connect)

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QGroupBox { font-weight: bold; border: 1px solid #d5d8dc; border-radius: 8px;
                        margin-top: 10px; padding-top: 12px; background-color: white; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #2c3e50; }
            QPushButton { padding: 7px 14px; border-radius: 6px; background-color: #ecf0f1; }
            QPushButton:hover { background-color: #d5dbdb; }
            QPushButton:disabled { color: #bdc3c7; background-color: #f4f6f7; }
            QLineEdit { padding: 6px 8px; border: 1px solid #d5d8dc; border-radius: 6px; }
            QLineEdit:focus { border-color: #3498db; }
            QTableWidget { border: 1px solid #d5d8dc; border-radius: 8px; background-color: white; }
            QHeaderView::section { background-color: #ecf0f1; padding: 6px; border: none;
                                   border-bottom: 1px solid #d5d8dc; font-weight: bold; }
        """)
        for btn, color in ((self.connect_btn, "#3498db"), (self.scan_btn, "#2ecc71"),
                           (self.apply_btn, "#e74c3c")):
            btn.setStyleSheet(f"QPushButton {{ background-color: {color}; color: white; }}"
                              f"QPushButton:hover {{ background-color: {color}; opacity: 0.9; }}"
                              f"QPushButton:disabled {{ background-color: #bdc3c7; color: white; }}")

    # ---------- 通用 ----------
    def _set_busy(self, busy: bool, msg: str = "") -> None:
        self.setCursor(Qt.WaitCursor if busy else Qt.ArrowCursor)
        for b in (self.connect_btn, self.scan_btn, self.select_all_btn, self.clear_btn,
                  self.filter_btn, self.preview_btn, self.apply_btn):
            b.setEnabled(not busy)
        if msg:
            self.table_status.setText(msg)

    def _on_error(self, msg: str) -> None:
        self._set_busy(False)
        QMessageBox.warning(self, "操作失败", msg)

    # ---------- 连接 ----------
    def _connect(self) -> None:
        url = self.url_edit.text().strip()
        token = self.token_edit.text().strip()
        if not url or not token:
            self.conn_status.setText("请填写地址与 Token")
            return
        client = RemoteApiClient(url, token)
        self._set_busy(True, "正在连接服务…")
        self._worker = RemoteWorker(client.health, parent=self)
        self._worker.finished_ok.connect(lambda h: self._on_connected(client, h))
        self._worker.finished_err.connect(self._on_connect_error)
        self._worker.start()

    def _on_connected(self, client: RemoteApiClient, health: Dict[str, Any]) -> None:
        self._client = client
        self._connected = True
        ver = health.get("version", "")
        self.conn_status.setText(f"✅ 已连接 v{ver}")
        self.conn_status.setStyleSheet("color: #27ae60;")
        self._set_busy(False)
        self.scan_btn.setEnabled(True)

    def _on_connect_error(self, msg: str) -> None:
        self._set_busy(False)
        self.conn_status.setText("连接失败")
        self.conn_status.setStyleSheet("color: #e74c3c;")
        QMessageBox.warning(self, "连接失败", msg)

    # ---------- 扫描 ----------
    def _scan(self) -> None:
        if not self._client:
            return
        path = self.path_edit.text().strip()
        if not path:
            self.table_status.setText("请输入媒体目录")
            return
        self._set_busy(True, "正在扫描…")
        self._worker = RemoteWorker(self._client.scan, path, parent=self)
        self._worker.finished_ok.connect(self._on_scanned)
        self._worker.finished_err.connect(self._on_error)
        self._worker.start()

    def _on_scanned(self, data: Dict[str, Any]) -> None:
        self._items = data.get("files", [])
        self._refresh_table()
        need = sum(1 for f in self._items if f.get("name") != f.get("suggested_name"))
        self.table_status.setText(f"共 {data.get('total', len(self._items))} 个文件，其中 {need} 项建议改名")
        for b in (self.select_all_btn, self.clear_btn, self.filter_btn, self.preview_btn):
            b.setEnabled(True)
        self._set_busy(False)

    # ---------- 表格 ----------
    def _refresh_table(self) -> None:
        self.table.setRowCount(0)
        filter_on = self.filter_btn.isChecked()
        for f in self._items:
            name = f.get("name", "")
            suggested = f.get("suggested_name", "")
            if filter_on and name == suggested:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            check = QTableWidgetItem()
            check.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, check)
            name_item = QTableWidgetItem(name)
            name_item.setToolTip(name)
            self.table.setItem(row, 1, name_item)
            sug_item = QTableWidgetItem(suggested if suggested else "—")
            if name != suggested:
                sug_item.setForeground(QColor("#e67e22"))
            self.table.setItem(row, 2, sug_item)
            media_type = (f.get("analysis") or {}).get("type", "unknown")
            self.table.setItem(row, 3, QTableWidgetItem(media_type))
        self._update_apply_state()

    def _on_cell_clicked(self, row: int, col: int) -> None:
        if col == 0:
            item = self.table.item(row, 0)
            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)
        self._update_apply_state()

    def _set_all_checked(self, checked: bool) -> None:
        state = Qt.Checked if checked else Qt.Unchecked
        for row in range(self.table.rowCount()):
            self.table.item(row, 0).setCheckState(state)
        self._update_apply_state()

    def _selected(self) -> List[Dict[str, Any]]:
        sel = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                sel.append(self._items[row])
        return sel

    def _update_apply_state(self) -> None:
        n = len(self._selected())
        self.apply_btn.setText(f"✅ 执行重命名（{n}）")
        self.apply_btn.setEnabled(n > 0 and self._connected)

    # ---------- 重命名 ----------
    def _preview(self) -> None:
        if not self._client:
            return
        sel = self._selected()
        if not sel:
            return
        path = self.path_edit.text().strip()
        self._set_busy(True, "生成预览…")
        self._worker = RemoteWorker(self._client.rename_preview, path,
                                    [f.get("rel_path") or f.get("name") for f in sel],
                                    parent=self)
        self._worker.finished_ok.connect(self._on_previewed)
        self._worker.finished_err.connect(self._on_error)
        self._worker.start()

    def _on_previewed(self, data: Dict[str, Any]) -> None:
        previews = data.get("previews", [])
        lines = []
        for p in previews:
            old = p.get("old_name", "")
            new = p.get("new_name", "")
            ok = p.get("ok")
            tag = "" if ok else ("  ⚠️ 冲突" if p.get("conflict") else "  ❌ 失败")
            lines.append(f"{old}\n   → {new}{tag}")
        QMessageBox.information(self, "重命名预览",
                                "\n".join(lines) if lines else "无可重命名的文件")
        self._set_busy(False)

    def _apply(self) -> None:
        if not self._client:
            return
        sel = self._selected()
        if not sel:
            return
        path = self.path_edit.text().strip()
        renames = [{"old": f.get("rel_path") or f.get("name"),
                    "new": f.get("suggested_name")} for f in sel]
        confirm = QMessageBox.question(
            self, "确认执行",
            f"将重命名 {len(sel)} 个文件（原文件自动备份到服务器 .tv_renamer_backup/）。\n继续？",
            QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        self._set_busy(True, "正在执行重命名…")
        self._worker = RemoteWorker(self._client.rename, path, renames, False, parent=self)
        self._worker.finished_ok.connect(self._on_applied)
        self._worker.finished_err.connect(self._on_error)
        self._worker.start()

    def _on_applied(self, data: Dict[str, Any]) -> None:
        results = data.get("results", [])
        ok = sum(1 for r in results if r.get("ok"))
        backup = data.get("backup_dir") or ""
        msg = f"执行完成：{ok}/{len(results)} 成功"
        if backup:
            msg += f"\n备份目录：{backup}"
        QMessageBox.information(self, "执行结果", msg)
        self._set_busy(False)
        self._scan()  # 刷新列表

    def _on_error(self, msg: str) -> None:
        self._set_busy(False)
        QMessageBox.warning(self, "操作失败", msg)
