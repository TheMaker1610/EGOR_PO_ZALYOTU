from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableView, QPushButton, QLabel, QLineEdit,
    QComboBox, QMessageBox, QDialog, QFormLayout,
    QHeaderView, QGroupBox, QSizePolicy,
)


class _TableModel(QAbstractTableModel):
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


class _CreateUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать пользователя")
        self.setFixedSize(360, 240)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.username_edit = QLineEdit()
        form.addRow("Логин:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Пароль:", self.password_edit)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "admin"])
        form.addRow("Роль:", self.role_combo)

        layout.addLayout(form)

        hint = QLabel("Пароль: ≥6 (user) / ≥7 (admin) символов,\nA-Z, a-z, 0-9, спецсимвол")
        hint.setStyleSheet("color:gray; font-size:10px;")
        layout.addWidget(hint)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color:red;")
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("Создать")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)


class _ResetPasswordDialog(QDialog):
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Сброс пароля: {username}")
        self.setFixedSize(340, 160)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Новый пароль:", self.password_edit)
        layout.addLayout(form)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color:red;")
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("Сохранить")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)


class AdminWindow(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api = api_client
        self._users_data = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1 — Users
        users_tab = QWidget()
        users_layout = QVBoxLayout(users_tab)

        users_toolbar = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._load_users)
        create_btn = QPushButton("Создать пользователя")
        create_btn.clicked.connect(self._create_user)
        users_toolbar.addWidget(refresh_btn)
        users_toolbar.addWidget(create_btn)
        users_toolbar.addStretch()
        users_layout.addLayout(users_toolbar)

        self.users_table = QTableView()
        self.users_table.setSelectionBehavior(QTableView.SelectRows)
        self.users_table.setEditTriggers(QTableView.NoEditTriggers)
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        users_layout.addWidget(self.users_table)

        actions_row = QHBoxLayout()
        self.toggle_active_btn = QPushButton("Вкл/Выкл аккаунт")
        self.toggle_active_btn.clicked.connect(self._toggle_active)
        self.unlock_btn = QPushButton("Разблокировать")
        self.unlock_btn.clicked.connect(self._unlock)
        self.reset_pwd_btn = QPushButton("Сбросить пароль")
        self.reset_pwd_btn.clicked.connect(self._reset_password)
        actions_row.addWidget(self.toggle_active_btn)
        actions_row.addWidget(self.unlock_btn)
        actions_row.addWidget(self.reset_pwd_btn)
        actions_row.addStretch()
        users_layout.addLayout(actions_row)

        tabs.addTab(users_tab, "Пользователи")

        # Tab 2 — Audit
        audit_tab = QWidget()
        audit_layout = QVBoxLayout(audit_tab)

        audit_toolbar = QHBoxLayout()
        audit_refresh = QPushButton("Обновить журнал")
        audit_refresh.clicked.connect(self._load_audit)
        audit_toolbar.addWidget(audit_refresh)
        audit_toolbar.addStretch()
        audit_layout.addLayout(audit_toolbar)

        self.audit_table = QTableView()
        self.audit_table.setSelectionBehavior(QTableView.SelectRows)
        self.audit_table.setEditTriggers(QTableView.NoEditTriggers)
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        audit_layout.addWidget(self.audit_table)

        tabs.addTab(audit_tab, "Журнал событий")

        self._load_users()
        self._load_audit()

    def _load_users(self):
        result = self.api.get_users()
        if not result["ok"]:
            QMessageBox.warning(self, "Ошибка", str(result.get("error")))
            return
        users = result["data"]
        self._users_data = users
        headers = ["ID", "Логин", "Роль", "Активен", "Блокировка", "Попытки", "Последний вход"]
        rows = []
        for u in users:
            locked = u.get("locked_until") or "—"
            last = u.get("last_login_at") or "—"
            if last and last != "—":
                last = str(last)[:19]
            rows.append([
                u["id"],
                u["username"],
                u["role"],
                "Да" if u["is_active"] else "Нет",
                str(locked)[:19] if locked != "—" else "—",
                u.get("failed_attempts", 0),
                last,
            ])
        model = _TableModel(headers, rows)
        self.users_table.setModel(model)

    def _get_selected_user(self):
        idx = self.users_table.currentIndex()
        if not idx.isValid() or not self._users_data:
            QMessageBox.information(self, "Выбор", "Выберите пользователя в таблице")
            return None
        row = idx.row()
        if row >= len(self._users_data):
            return None
        return self._users_data[row]

    def _create_user(self):
        dlg = _CreateUserDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        username = dlg.username_edit.text().strip()
        password = dlg.password_edit.text()
        role = dlg.role_combo.currentText()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
        result = self.api.create_user(username, password, role)
        if result["ok"]:
            QMessageBox.information(self, "Готово", f"Пользователь '{username}' создан")
            self._load_users()
        else:
            QMessageBox.warning(self, "Ошибка", str(result.get("error")))

    def _toggle_active(self):
        user = self._get_selected_user()
        if not user:
            return
        new_state = not user["is_active"]
        result = self.api.update_user(user["id"], is_active=new_state)
        if result["ok"]:
            state_str = "активирован" if new_state else "деактивирован"
            QMessageBox.information(self, "Готово", f"Пользователь {state_str}")
            self._load_users()
        else:
            QMessageBox.warning(self, "Ошибка", str(result.get("error")))

    def _unlock(self):
        user = self._get_selected_user()
        if not user:
            return
        result = self.api.unlock_user(user["id"])
        if result["ok"]:
            QMessageBox.information(self, "Готово", "Пользователь разблокирован")
            self._load_users()
        else:
            QMessageBox.warning(self, "Ошибка", str(result.get("error")))

    def _reset_password(self):
        user = self._get_selected_user()
        if not user:
            return
        dlg = _ResetPasswordDialog(user["username"], self)
        if dlg.exec_() != QDialog.Accepted:
            return
        new_pwd = dlg.password_edit.text()
        if not new_pwd:
            return
        result = self.api.reset_password(user["id"], new_pwd)
        if result["ok"]:
            QMessageBox.information(self, "Готово", "Пароль сброшен")
        else:
            QMessageBox.warning(self, "Ошибка", str(result.get("error")))

    def _load_audit(self):
        result = self.api.get_audit()
        if not result["ok"]:
            QMessageBox.warning(self, "Ошибка", str(result.get("error")))
            return
        events = result["data"]
        headers = ["#", "Время", "Тип события", "Компонент",
                   "Пользователь", "IP", "Служебные заголовки", "Детали"]
        rows = []
        for e in events:
            ts = str(e.get("timestamp", ""))[:19]
            rows.append([
                e.get("id", ""),
                ts,
                e.get("event_type", ""),
                e.get("component", ""),
                e.get("username") or "—",
                e.get("ip_address") or "—",
                e.get("headers") or "—",
                e.get("details") or "—",
            ])
        model = _TableModel(headers, rows)
        self.audit_table.setModel(model)
