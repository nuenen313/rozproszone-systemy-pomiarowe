"""
Rozproszone Systemy Pomiarowe — Dashboard LabVIEW-style in PyQt6
REST client UI communicating with Flask backend.

Architecture: Three-layer separation
  - RestClient   → HTTP communication (requests)
  - DataParser   → JSON parsing and validation
  - Dashboard    → UI presentation only
"""

import sys
import json
from datetime import datetime

import numpy as np
import requests
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QObject, pyqtSlot
)
from PyQt6.QtGui import QFont, QColor, QPalette, QFontDatabase
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QCheckBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QFrame, QTextEdit, QStatusBar,
    QSizePolicy
)

# ─────────────────────────────────────────────
# PALETTE & STYLING
# ─────────────────────────────────────────────

DARK_BG      = "#0e1117"
PANEL_BG     = "#161b22"
BORDER       = "#30363d"
ACCENT_BLUE  = "#58a6ff"
ACCENT_GREEN = "#3fb950"
ACCENT_RED   = "#f85149"
ACCENT_AMBER = "#d29922"
TEXT_PRIMARY = "#e6edf3"
TEXT_MUTED   = "#8b949e"
INPUT_BG     = "#21262d"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_PRIMARY};
    font-family: "JetBrains Mono", "Consolas", "Courier New", monospace;
    font-size: 12px;
}}

QGroupBox {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 12px;
    padding: 8px;
    font-weight: bold;
    font-size: 11px;
    color: {TEXT_MUTED};
    letter-spacing: 1px;
    text-transform: uppercase;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 10px;
}}

QLabel {{
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QLabel#muted {{
    color: {TEXT_MUTED};
    font-size: 11px;
}}

QLineEdit, QSpinBox {{
    background-color: {INPUT_BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 5px 8px;
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_BLUE};
}}

QLineEdit:focus, QSpinBox:focus {{
    border-color: {ACCENT_BLUE};
}}

QComboBox {{
    background-color: {INPUT_BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 5px 8px;
    color: {TEXT_PRIMARY};
    min-width: 120px;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT_BLUE};
}}

QPushButton {{
    background-color: {INPUT_BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 14px;
    color: {TEXT_PRIMARY};
    font-weight: bold;
    letter-spacing: 0.5px;
}}

QPushButton:hover {{
    background-color: {BORDER};
    border-color: {ACCENT_BLUE};
}}

QPushButton:pressed {{
    background-color: {ACCENT_BLUE};
    color: {DARK_BG};
}}

QPushButton#primary {{
    background-color: {ACCENT_BLUE};
    color: #ffffff;
    border-color: {ACCENT_BLUE};
}}

QPushButton#primary:hover {{
    background-color: #79c0ff;
    color: #ffffff;
}}

QPushButton#danger {{
    border-color: {ACCENT_RED};
    color: {ACCENT_RED};
}}

QTableWidget {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    gridline-color: {BORDER};
    color: {TEXT_PRIMARY};
    selection-background-color: #1f3a5f;
}}

QTableWidget::item {{
    padding: 4px 8px;
    border: none;
}}

QHeaderView::section {{
    background-color: {INPUT_BG};
    color: {TEXT_MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 5px 8px;
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

QTextEdit {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 4px;
    color: {TEXT_MUTED};
    font-size: 11px;
    font-family: "JetBrains Mono", "Consolas", monospace;
}}

QCheckBox {{
    color: {TEXT_MUTED};
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    background-color: {INPUT_BG};
    border: 1px solid {BORDER};
    border-radius: 3px;
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_BLUE};
    border-color: {ACCENT_BLUE};
}}

QSplitter::handle {{
    background: {BORDER};
}}

QScrollBar:vertical {{
    background: {PANEL_BG};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 20px;
}}

QStatusBar {{
    background-color: {PANEL_BG};
    border-top: 1px solid {BORDER};
    color: {TEXT_MUTED};
    font-size: 11px;
}}
"""

# ─────────────────────────────────────────────
# LAYER 1: REST CLIENT
# ─────────────────────────────────────────────

class RestClient:
    """Pure HTTP communication. No UI coupling."""

    def __init__(self, base_url: str, timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str, params: dict = None) -> tuple[int, dict | list | None, str]:
        """
        Returns (status_code, parsed_body, error_message).
        On success: (200, data, "")
        On failure: (-1, None, reason)
        """
        url = f"{self.base_url}{path}"
        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            try:
                body = resp.json()
            except ValueError:
                body = None
            return resp.status_code, body, ""
        except requests.ConnectionError:
            return -1, None, f"Connection refused — is the backend running at {self.base_url}?"
        except requests.Timeout:
            return -1, None, f"Request timed out after {self.timeout}s"
        except Exception as exc:
            return -1, None, str(exc)

    def check_health(self) -> tuple[bool, str]:
        code, body, err = self.get("/health")
        if err:
            return False, err
        if code == 200:
            return True, f"HTTP {code} — {body}"
        return False, f"HTTP {code} — unexpected response"

    def get_devices(self) -> tuple[list, str]:
        code, body, err = self.get("/devices")
        if err:
            return [], err
        if code != 200 or not isinstance(body, list):
            return [], f"HTTP {code} — expected list of devices"
        return body, ""

    def get_latest(self) -> tuple[dict | None, str]:
        """
        GET /measurements/latest — returns the single globally most recent row.
        This endpoint accepts NO filter parameters (by design in the Flask app).
        """
        code, body, err = self.get("/measurements/latest")
        if err:
            return None, err
        if code == 404:
            return None, "No measurements in the database yet."
        if code != 200 or not isinstance(body, dict):
            return None, f"HTTP {code} — unexpected response"
        return body, ""

    def get_latest_filtered(self, device_id: str, sensor: str) -> tuple[dict | None, str]:
        """
        Simulates a filtered 'latest' by calling /measurements/history?limit=1.
        Used when the user has selected a specific device and/or sensor.
        """
        params: dict = {"limit": 1}
        if device_id:
            params["device_id"] = device_id
        if sensor:
            params["sensor"] = sensor
        code, body, err = self.get("/measurements/history", params)
        if err:
            return None, err
        if code != 200 or not isinstance(body, list):
            return None, f"HTTP {code} — unexpected response"
        if not body:
            return None, "No measurements found for the selected filters."
        return body[0], ""

    def get_history(self, device_id: str, sensor: str, limit: int) -> tuple[list, str]:
        params = {"device_id": device_id, "sensor": sensor, "limit": limit}
        code, body, err = self.get("/measurements/history", params)
        if err:
            return [], err
        if code != 200 or not isinstance(body, list):
            return [], f"HTTP {code} — expected list of measurements"
        return body, ""


# ─────────────────────────────────────────────
# LAYER 2: DATA PARSER
# ─────────────────────────────────────────────

class DataParser:
    """Validates and normalises JSON payloads from the REST layer."""

    # API uses "sensor_value" (not "value") — matches measurements table column name
    LATEST_FIELDS  = ("device_id", "sensor", "sensor_value", "unit", "ts_ms", "seq")
    HISTORY_FIELDS = ("ts_ms", "sensor_value", "unit", "sensor")

    @staticmethod
    def parse_devices(raw: list) -> tuple[list[str], list[dict]]:
        """
        Parses /devices response: [{device_id, group_id, is_online, updated_at}, ...]
        Returns (sorted device_id list, full device info list).
        """
        ids  = []
        info = []
        for item in raw:
            if isinstance(item, dict) and "device_id" in item:
                ids.append(str(item["device_id"]))
                info.append({
                    "device_id": item.get("device_id", ""),
                    "group_id":  item.get("group_id",  ""),
                    "is_online": item.get("is_online",  False),
                    "updated_at": item.get("updated_at", 0),
                })
        ids, info = zip(*sorted(zip(ids, info))) if ids else ([], [])
        return list(ids), list(info)

    @staticmethod
    def parse_latest(raw: dict) -> dict:
        """
        Normalises a single measurement row from the API.
        The API returns 'sensor_value' (matches the DB column name),
        NOT 'value' — we normalise to 'sensor_value' throughout.
        """
        return {
            "device_id":   raw.get("device_id",   "—"),
            "sensor":      raw.get("sensor",       "—"),
            "sensor_value": raw.get("sensor_value", "—"),
            "unit":        raw.get("unit",         "—"),
            "ts_ms":       raw.get("ts_ms",        "—"),
            "seq":         raw.get("seq",          "—"),
        }

    @staticmethod
    def parse_history(raw: list) -> list[dict]:
        """
        Normalises history records.
        API returns newest-first (ORDER BY id DESC); we reverse to ascending
        for chronological chart plotting.
        """
        records = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            records.append({
                "ts_ms":        item.get("ts_ms",        0),
                "sensor_value": item.get("sensor_value", None),
                "unit":         item.get("unit",         ""),
                "sensor":       item.get("sensor",       ""),
            })
        # Reverse: API gives DESC, chart needs ASC
        records.reverse()
        return records

    @staticmethod
    def format_timestamp(ts_ms: int | str) -> str:
        try:
            ts = int(ts_ms)
            return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, OSError):
            return str(ts_ms)


# ─────────────────────────────────────────────
# LAYER 3: WORKER THREAD (non-blocking HTTP)
# ─────────────────────────────────────────────

class WorkerSignals(QObject):
    finished   = pyqtSignal(str, object, str)   # (task, result, error)


class RestWorker(QThread):
    """Runs a single REST call off the UI thread."""

    def __init__(self, task: str, client: RestClient, **kwargs):
        super().__init__()
        self.task   = task
        self.client = client
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        result, err = None, ""
        try:
            if self.task == "health":
                ok, msg = self.client.check_health()
                result = ok
                err    = "" if ok else msg
            elif self.task == "devices":
                result, err = self.client.get_devices()
            elif self.task == "latest":
                result, err = self.client.get_latest()
            elif self.task == "latest_filtered":
                result, err = self.client.get_latest_filtered(
                    self.kwargs.get("device_id"),
                    self.kwargs.get("sensor"),
                )
            elif self.task == "history":
                result, err = self.client.get_history(
                    self.kwargs["device_id"],
                    self.kwargs["sensor"],
                    self.kwargs["limit"],
                )
        except Exception as exc:
            err = str(exc)
        self.signals.finished.emit(self.task, result, err)


# ─────────────────────────────────────────────
# MATPLOTLIB CHART WIDGET
# ─────────────────────────────────────────────

class TrendChart(FigureCanvas):
    """Embedded matplotlib figure styled to match the dark theme."""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 3), facecolor=PANEL_BG)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ax = self.fig.add_subplot(111)
        self._style_axes()
        self.fig.tight_layout(pad=1.5)

    def _style_axes(self):
        ax = self.ax
        ax.set_facecolor(DARK_BG)
        ax.tick_params(colors=TEXT_MUTED, labelsize=9)
        ax.xaxis.label.set_color(TEXT_MUTED)
        ax.yaxis.label.set_color(TEXT_MUTED)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)
        ax.grid(True, color=BORDER, linewidth=0.5, linestyle="--", alpha=0.5)
        ax.set_xlabel("Sample index", color=TEXT_MUTED, fontsize=9)
        ax.set_ylabel("Value", color=TEXT_MUTED, fontsize=9)
        ax.set_title("No data — fetch history to populate chart",
                     color=TEXT_MUTED, fontsize=9, style="italic")

    def plot(self, records: list[dict], sensor: str, unit: str):
        self.ax.clear()
        self._style_axes()

        if not records:
            self.ax.set_title("No data returned for the selected filters",
                              color=ACCENT_AMBER, fontsize=9, style="italic")
            self.draw()
            return

        values = [r["sensor_value"] for r in records if r["sensor_value"] is not None]
        indices = list(range(len(values)))

        self.ax.plot(indices, values,
                     color=ACCENT_BLUE, linewidth=1.5, marker="o",
                     markersize=3, markerfacecolor=ACCENT_BLUE,
                     markeredgewidth=0)
        self.ax.fill_between(indices, values, alpha=0.1, color=ACCENT_BLUE)

        title = f"{sensor}  [{unit}]  —  {len(values)} samples"
        self.ax.set_title(title, color=TEXT_PRIMARY, fontsize=10)
        self.ax.set_xlabel("Sample index", color=TEXT_MUTED, fontsize=9)
        self.ax.set_ylabel(f"Value [{unit}]", color=TEXT_MUTED, fontsize=9)
        self.fig.tight_layout(pad=1.5)
        self.draw()


# ─────────────────────────────────────────────
# STATUS BADGE LABEL
# ─────────────────────────────────────────────

class StatusBadge(QLabel):
    def set_ok(self, text="OK"):
        self.setText(f"● {text}")
        self.setStyleSheet(f"color: {ACCENT_GREEN}; font-weight: bold; background: transparent;")

    def set_error(self, text="ERROR"):
        self.setText(f"● {text}")
        self.setStyleSheet(f"color: {ACCENT_RED}; font-weight: bold; background: transparent;")

    def set_neutral(self, text="—"):
        self.setText(f"● {text}")
        self.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: bold; background: transparent;")

    def set_pending(self, text="..."):
        self.setText(f"◌ {text}")
        self.setStyleSheet(f"color: {ACCENT_AMBER}; font-weight: bold; background: transparent;")


# ─────────────────────────────────────────────
# VALUE DISPLAY PAIR  (label + value)
# ─────────────────────────────────────────────

def make_field_row(label_text: str) -> tuple[QLabel, QLabel]:
    label = QLabel(label_text)
    label.setObjectName("muted")
    label.setFixedWidth(80)
    value = QLabel("—")
    value.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: bold; background: transparent;")
    return label, value


# ─────────────────────────────────────────────
# MAIN DASHBOARD WINDOW
# ─────────────────────────────────────────────

class Dashboard(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rozproszone Systemy Pomiarowe — Dashboard")
        self.setMinimumSize(1100, 760)

        self._client: RestClient | None = None
        self._workers: list[RestWorker] = []
        self._history_records: list[dict] = []

        self._build_ui()
        self._connect_signals()
        self._setup_auto_refresh_timer()

        self.log("Dashboard initialised. Set the API URL and click Test API.")

    # ── UI CONSTRUCTION ──────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 6)
        root.setSpacing(8)

        root.addWidget(self._build_top_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 840])
        root.addWidget(splitter, stretch=1)

        root.addWidget(self._build_log_bar())
        self._build_status_bar()

    # ── TOP BAR ──────────────────────────────────────

    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet(
            f"background-color: {PANEL_BG}; border: 1px solid {BORDER}; border-radius: 6px;"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)

        title = QLabel("RSP DASHBOARD")
        title.setStyleSheet(
            f"color: {ACCENT_BLUE}; font-size: 14px; font-weight: bold; "
            f"letter-spacing: 3px; background: transparent; border: none;"
        )
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {BORDER}; background: {BORDER};")
        layout.addWidget(sep)

        layout.addWidget(QLabel("API URL:"))
        self.url_input = QLineEdit("http://localhost:5001")
        self.url_input.setFixedWidth(220)
        layout.addWidget(self.url_input)

        self.btn_test = QPushButton("Test API")
        self.btn_test.setObjectName("primary")
        self.btn_test.setFixedWidth(90)
        layout.addWidget(self.btn_test)

        self.api_status = StatusBadge()
        self.api_status.set_neutral("not tested")
        layout.addWidget(self.api_status)

        layout.addStretch()

        self.chk_autorefresh = QCheckBox("Auto-refresh")
        layout.addWidget(self.chk_autorefresh)

        layout.addWidget(QLabel("every"))
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(1, 300)
        self.spin_interval.setValue(5)
        self.spin_interval.setSuffix(" s")
        self.spin_interval.setFixedWidth(75)
        layout.addWidget(self.spin_interval)

        return bar

    # ── LEFT PANEL (config + filters) ────────────────

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(260)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(8)

        # Devices group
        grp_dev = QGroupBox("Configuration")
        dev_layout = QGridLayout(grp_dev)
        dev_layout.setSpacing(6)

        dev_layout.addWidget(QLabel("Device:"), 0, 0)
        self.combo_device = QComboBox()
        self.combo_device.setPlaceholderText("— select —")
        dev_layout.addWidget(self.combo_device, 0, 1)

        self.btn_load_devices = QPushButton("↻ Refresh devices")
        self.btn_load_devices.setToolTip("Fetch device list from /devices")
        dev_layout.addWidget(self.btn_load_devices, 1, 0, 1, 2)

        dev_layout.addWidget(QLabel("Sensor:"), 2, 0)
        self.combo_sensor = QComboBox()
        self.combo_sensor.addItems(["temperature", "humidity", "azimuth", "core_temperature"])
        dev_layout.addWidget(self.combo_sensor, 2, 1)

        dev_layout.addWidget(QLabel("Limit:"), 3, 0)
        self.spin_limit = QSpinBox()
        self.spin_limit.setRange(1, 1000)
        self.spin_limit.setValue(50)
        dev_layout.addWidget(self.spin_limit, 3, 1)

        layout.addWidget(grp_dev)

        # Actions group
        grp_actions = QGroupBox("Actions")
        act_layout = QVBoxLayout(grp_actions)
        act_layout.setSpacing(6)

        self.btn_latest = QPushButton("⬇  Fetch latest")
        self.btn_latest.setToolTip("GET /measurements/latest")
        act_layout.addWidget(self.btn_latest)

        self.btn_history = QPushButton("⬇  Fetch history")
        self.btn_history.setToolTip("GET /measurements/history?device_id=...&sensor=...&limit=...")
        act_layout.addWidget(self.btn_history)

        layout.addWidget(grp_actions)
        layout.addStretch()
        return panel

    # ── RIGHT PANEL (data presentation) ──────────────

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Latest measurement
        grp_latest = QGroupBox("Latest Measurement")
        g_layout = QGridLayout(grp_latest)
        g_layout.setSpacing(6)
        g_layout.setColumnStretch(1, 1)
        g_layout.setColumnStretch(3, 1)

        fields = ["Device ID", "Sensor", "Value", "Unit", "Timestamp", "Seq"]
        self._latest_values: dict[str, QLabel] = {}
        for i, name in enumerate(fields):
            row, col = divmod(i, 2)
            lbl, val = make_field_row(name)
            self._latest_values[name] = val
            g_layout.addWidget(lbl, row, col * 2)
            g_layout.addWidget(val, row, col * 2 + 1)

        # Make "Value" bigger — it's the star of the show
        self._latest_values["Value"].setStyleSheet(
            f"color: {ACCENT_BLUE}; font-size: 22px; font-weight: bold; background: transparent;"
        )
        layout.addWidget(grp_latest)

        # History + chart
        grp_history = QGroupBox("History / Trend")
        h_layout = QVBoxLayout(grp_history)
        h_layout.setSpacing(6)

        self.trend_chart = TrendChart()
        h_layout.addWidget(self.trend_chart, stretch=3)

        # Recent records table
        table_label = QLabel("Recent records")
        table_label.setObjectName("muted")
        h_layout.addWidget(table_label)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Sensor", "Value", "Unit"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            self.table.styleSheet() +
            f"QTableWidget {{ alternate-background-color: #1a1f27; }}"
        )
        self.table.setMaximumHeight(180)
        h_layout.addWidget(self.table, stretch=1)

        layout.addWidget(grp_history, stretch=1)
        return panel

    # ── LOG BAR ──────────────────────────────────────

    def _build_log_bar(self) -> QWidget:
        grp = QGroupBox("Diagnostics")
        layout = QHBoxLayout(grp)
        layout.setContentsMargins(4, 4, 4, 4)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(60)
        layout.addWidget(self.log_output)
        return grp

    def _build_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    # ── SIGNAL CONNECTIONS ────────────────────────────

    def _connect_signals(self):
        self.btn_test.clicked.connect(self._on_test_api)
        self.btn_load_devices.clicked.connect(self._on_load_devices)
        self.btn_latest.clicked.connect(self._on_fetch_latest)
        self.btn_history.clicked.connect(self._on_fetch_history)
        self.chk_autorefresh.toggled.connect(self._on_autorefresh_toggled)
        self.spin_interval.valueChanged.connect(self._on_interval_changed)

    # ── AUTO-REFRESH ──────────────────────────────────

    def _setup_auto_refresh_timer(self):
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh_tick)

    def _on_autorefresh_toggled(self, enabled: bool):
        if enabled:
            interval_ms = self.spin_interval.value() * 1000
            self._refresh_timer.start(interval_ms)
            self.log(f"Auto-refresh enabled every {self.spin_interval.value()}s")
        else:
            self._refresh_timer.stop()
            self.log("Auto-refresh disabled")

    def _on_interval_changed(self, value: int):
        if self._refresh_timer.isActive():
            self._refresh_timer.setInterval(value * 1000)

    def _auto_refresh_tick(self):
        self._on_fetch_latest()
        if self._history_records:          # only refresh history if loaded before
            self._on_fetch_history()

    # ── CLIENT FACTORY ────────────────────────────────

    def _get_client(self) -> RestClient:
        base = self.url_input.text().strip()
        self._client = RestClient(base_url=base)
        return self._client

    # ── ACTION HANDLERS ───────────────────────────────

    def _on_test_api(self):
        self.api_status.set_pending("testing…")
        self.status_bar.showMessage("Testing API connection…")
        self._run_worker("health")

    def _on_load_devices(self):
        self.status_bar.showMessage("Fetching device list…")
        self.log("→ GET /devices")
        self._run_worker("devices")

    def _on_fetch_latest(self):
        device_id = self.combo_device.currentText().strip() or None
        sensor    = self.combo_sensor.currentText().strip()  or None
        if device_id or sensor:
            # /measurements/latest accepts no filters — use history?limit=1 instead
            self.status_bar.showMessage("Fetching latest (filtered via history?limit=1)…")
            self.log(
                f"→ GET /measurements/history?limit=1"
                f"  device={device_id or '*'}  sensor={sensor or '*'}"
            )
            self._run_worker("latest_filtered", device_id=device_id, sensor=sensor)
        else:
            self.status_bar.showMessage("Fetching global latest measurement…")
            self.log("→ GET /measurements/latest")
            self._run_worker("latest")

    def _on_fetch_history(self):
        device_id = self.combo_device.currentText().strip()
        sensor    = self.combo_sensor.currentText().strip()
        limit     = self.spin_limit.value()
        if not device_id:
            self.log("⚠ Select a device before fetching history.", level="warn")
            return
        self.status_bar.showMessage("Fetching history…")
        self.log(f"→ GET /measurements/history  device={device_id}  sensor={sensor}  limit={limit}")
        self._run_worker("history", device_id=device_id, sensor=sensor, limit=limit)

    # ── WORKER MANAGEMENT ─────────────────────────────

    def _run_worker(self, task: str, **kwargs):
        client = self._get_client()
        worker = RestWorker(task, client, **kwargs)
        worker.signals.finished.connect(self._on_worker_done)
        worker.finished.connect(lambda: self._workers.remove(worker))
        self._workers.append(worker)
        worker.start()

    @pyqtSlot(str, object, str)
    def _on_worker_done(self, task: str, result, error: str):
        if task == "health":
            self._handle_health(result, error)
        elif task == "devices":
            self._handle_devices(result, error)
        elif task in ("latest", "latest_filtered"):
            self._handle_latest(result, error)
        elif task == "history":
            self._handle_history(result, error)

    # ── RESULT HANDLERS ───────────────────────────────

    def _handle_health(self, ok: bool, error: str):
        if ok:
            self.api_status.set_ok("OK")
            self.log("✓ API reachable", level="ok")
            self.status_bar.showMessage("API connection OK")
        else:
            self.api_status.set_error("ERROR")
            self.log(f"✗ {error}", level="error")
            self.status_bar.showMessage("API connection failed")

    def _handle_devices(self, raw: list | None, error: str):
        if error or not isinstance(raw, list):
            self.log(f"✗ Devices: {error or 'unexpected response'}", level="error")
            return
        ids, info = DataParser.parse_devices(raw)
        self.combo_device.clear()
        self.combo_device.addItems(ids)
        online  = sum(1 for d in info if d["is_online"])
        offline = len(info) - online
        self.log(
            f"✓ {len(ids)} device(s) — {online} online, {offline} offline: {', '.join(ids)}",
            level="ok"
        )
        self.status_bar.showMessage(f"{len(ids)} devices loaded ({online} online)")

    def _handle_latest(self, raw: dict | None, error: str):
        if error:
            self.log(f"✗ Latest: {error}", level="error")
            self.status_bar.showMessage("Failed to fetch latest measurement")
            return
        if not isinstance(raw, dict):
            self.log("✗ Latest: no data returned", level="warn")
            return
        data = DataParser.parse_latest(raw)
        self._latest_values["Device ID"].setText(str(data["device_id"]))
        self._latest_values["Sensor"].setText(str(data["sensor"]))
        self._latest_values["Value"].setText(str(data["sensor_value"]))
        self._latest_values["Unit"].setText(str(data["unit"]))
        self._latest_values["Timestamp"].setText(
            DataParser.format_timestamp(data["ts_ms"])
        )
        self._latest_values["Seq"].setText(str(data["seq"]))
        self.log(
            f"✓ Latest: {data['sensor_value']} {data['unit']}  ({data['sensor']} / {data['device_id']})",
            level="ok"
        )
        self.status_bar.showMessage(f"Latest: {data['sensor_value']} {data['unit']}")

    def _handle_history(self, raw: list | None, error: str):
        if error:
            self.log(f"✗ History: {error}", level="error")
            self.status_bar.showMessage("Failed to fetch history")
            return
        if not isinstance(raw, list):
            self.log("✗ History: no data returned", level="warn")
            return
        records = DataParser.parse_history(raw)
        self._history_records = records
        sensor = self.combo_sensor.currentText().strip()
        # records are now ascending (oldest first after parse_history.reverse())
        unit = records[-1]["unit"] if records else ""
        self.trend_chart.plot(records, sensor, unit)
        self._populate_table(records)
        self.log(f"✓ History: {len(records)} records plotted", level="ok")
        self.status_bar.showMessage(f"History loaded — {len(records)} records")

    # ── TABLE POPULATION ──────────────────────────────

    def _populate_table(self, records: list[dict]):
        # records are ascending (oldest→newest); display newest first in table
        display = list(reversed(records))[:50]
        self.table.setRowCount(len(display))
        for row, rec in enumerate(display):
            ts   = DataParser.format_timestamp(rec["ts_ms"])
            val  = str(rec["sensor_value"])
            unit = rec["unit"]
            snsr = rec["sensor"]
            for col, text in enumerate([ts, snsr, val, unit]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

    # ── LOGGING ───────────────────────────────────────

    def log(self, msg: str, level: str = "info"):
        colors = {
            "ok":    ACCENT_GREEN,
            "warn":  ACCENT_AMBER,
            "error": ACCENT_RED,
            "info":  TEXT_MUTED,
        }
        color = colors.get(level, TEXT_MUTED)
        ts = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color:{TEXT_MUTED}">[{ts}]</span> <span style="color:{color}">{msg}</span>'
        self.log_output.append(html)
        self.log_output.ensureCursorVisible()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

# def main():
#     app = QApplication(sys.argv)
#     app.setStyleSheet(STYLESHEET)

#     # Try to use a monospaced font if available
#     QFontDatabase.addApplicationFont("JetBrainsMono-Regular.ttf")
#     app.setFont(QFont("Consolas", 10))

#     window = Dashboard()
#     window.show()
#     sys.exit(app.exec())


# if __name__ == "__main__":
#     main()