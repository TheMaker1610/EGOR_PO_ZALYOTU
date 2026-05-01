from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
)


class LoginWindow(QDialog):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.setWindowTitle("Вход в систему — ТЭС Оптимизация")
        self.setFixedSize(400, 280)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("Система оптимизации ТЭС")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:16px; font-weight:bold; margin-bottom:12px;")
        outer.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        outer.addWidget(sep)

        form = QFormLayout()
        form.setVerticalSpacing(10)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Введите логин")
        form.addRow("Логин:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Введите пароль")
        form.addRow("Пароль:", self.password_edit)

        outer.addLayout(form)
        outer.addSpacing(8)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        self.status_label.setWordWrap(True)
        outer.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.login_btn = QPushButton("Войти")
        self.login_btn.setDefault(True)
        self.login_btn.clicked.connect(self._do_login)
        self.password_edit.returnPressed.connect(self._do_login)
        btn_row.addWidget(self.login_btn)
        outer.addLayout(btn_row)

    def _do_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not username or not password:
            self.status_label.setText("Заполните все поля")
            return

        self.login_btn.setEnabled(False)
        self.status_label.setText("")

        result = self.api.login(username, password)
        self.login_btn.setEnabled(True)

        if result["ok"]:
            self.accept()
        else:
            err = result["error"]
            if isinstance(err, list):
                err = err[0].get("msg", str(err)) if err else "Ошибка"
            self.status_label.setText(str(err))
            self.password_edit.clear()
