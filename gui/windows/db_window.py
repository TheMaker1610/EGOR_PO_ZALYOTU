from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableView, QPushButton, QLabel, QHeaderView, QMessageBox,
)


class _DynTableModel(QAbstractTableModel):
    def __init__(self, headers, rows, parent=None):
        super().__init__(parent)
        self._headers = headers
        self._rows = rows

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            return str(self._rows[index.row()][index.column()])
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return QVariant()


def _make_table() -> QTableView:
    t = QTableView()
    t.setSelectionBehavior(QTableView.SelectRows)
    t.setEditTriggers(QTableView.NoEditTriggers)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)
    return t


class DbWindow(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api = api_client
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        hint = QLabel("Прямой просмотр содержимого таблиц базы данных (SQLite). Только чтение.")
        hint.setStyleSheet("color: #555; font-size: 11px; margin: 4px;")
        layout.addWidget(hint)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Описания таблиц
        tables = [
            ("users",         "Таблица: users\n(пользователи, роли, статусы, хэши паролей не отображаются)"),
            ("sessions",      "Таблица: sessions\n(JWT-сессии, статус отзыва)"),
            ("calculations",  "Таблица: calculation_records\n(история расчётов)"),
            ("audit-logs",    "Таблица: audit_logs\n(журнал событий)"),
        ]

        self._tables = {}
        for endpoint, description in tables:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)

            desc = QLabel(description)
            desc.setStyleSheet("color: #333; font-size: 11px; margin-bottom: 4px;")
            tab_layout.addWidget(desc)

            toolbar = QHBoxLayout()
            refresh_btn = QPushButton("Обновить")
            refresh_btn.clicked.connect(lambda _, ep=endpoint: self._load(ep))
            self.count_lbl = QLabel("")
            toolbar.addWidget(refresh_btn)
            toolbar.addStretch()
            tab_layout.addLayout(toolbar)

            table_view = _make_table()
            tab_layout.addWidget(table_view)

            tab_name = endpoint.replace("-", "_")
            self._tables[endpoint] = {"view": table_view}
            self.tabs.addTab(tab, endpoint.replace("-", " ").title())

        self._load_all()

    def _load_all(self):
        for endpoint in self._tables:
            self._load(endpoint)

    def _load(self, endpoint: str):
        result = self.api.get_db_table(endpoint)
        if not result["ok"]:
            QMessageBox.warning(self, "Ошибка", str(result.get("error")))
            return
        rows_data = result["data"]
        if not rows_data:
            self._tables[endpoint]["view"].setModel(_DynTableModel(["(пусто)"], []))
            return

        # Заголовки — из ключей первой записи
        headers = list(rows_data[0].keys())

        # Строки — значения в том же порядке
        rows = []
        for record in rows_data:
            row = []
            for h in headers:
                val = record.get(h, "")
                if isinstance(val, dict):
                    # Для вложенных объектов (input/result расчёта) — краткий вывод
                    row.append(str(val)[:80] + "..." if len(str(val)) > 80 else str(val))
                else:
                    row.append("—" if val is None else str(val))
            rows.append(row)

        model = _DynTableModel(headers, rows)
        self._tables[endpoint]["view"].setModel(model)
