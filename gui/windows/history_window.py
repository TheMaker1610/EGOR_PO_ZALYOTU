from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView,
    QPushButton, QLabel, QHeaderView, QMessageBox,
)


class _HistoryModel(QAbstractTableModel):
    HEADERS = ["ID", "Дата/Время", "Нагрузка, МВт", "Блоков", "Темп., °C",
               "КПД нетто, %", "Расход топлива"]

    def __init__(self, rows, parent=None):
        super().__init__(parent)
        self._rows = rows

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            return str(self._rows[index.row()][index.column()])
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return QVariant()


class HistoryWindow(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api = api_client
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._load)
        toolbar.addWidget(refresh_btn)
        self.count_label = QLabel("")
        toolbar.addWidget(self.count_label)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self._load()

    def _load(self):
        result = self.api.get_history()
        if not result["ok"]:
            QMessageBox.warning(self, "Ошибка", str(result.get("error")))
            return
        records = result["data"]
        rows = []
        for r in records:
            ts = str(r.get("created_at", ""))[:19]
            rows.append([
                r["id"], ts,
                r["total_load_mw"], r["num_blocks"], r["temp_c"],
                r["efficiency_netto_pct"], r["fuel_consumption"],
            ])
        model = _HistoryModel(rows)
        self.table.setModel(model)
        self.count_label.setText(f"Записей: {len(rows)}")
