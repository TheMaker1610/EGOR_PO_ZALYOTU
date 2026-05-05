from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout,
)


class ChangePasswordWindow(QDialog):
    def __init__(self, api_client, forced: bool = False, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.forced = forced
        self.setWindowTitle("Смена пароля")
        self.setFixedSize(420, 380)
        if forced:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        if self.forced:
            notice = QLabel("Необходимо сменить пароль перед началом работы")
            notice.setStyleSheet("color: #b54800; font-weight: bold;")
            notice.setAlignment(Qt.AlignCenter)
            notice.setWordWrap(True)
            outer.addWidget(notice)

        form = QFormLayout()
        form.setVerticalSpacing(10)

        self.current_edit = QLineEdit()
        self.current_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Текущий пароль:", self.current_edit)

        self.new_edit = QLineEdit()
        self.new_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Новый пароль:", self.new_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Подтверждение:", self.confirm_edit)

        outer.addLayout(form)

        hint = QLabel(
            "Требования к паролю:\n"
            "  • Пользователь: не менее 6 символов\n"
            "  • Администратор: не менее 7 символов\n"
            "  • Заглавная буква (A-Z)\n"
            "  • Строчная буква (a-z)\n"
            "  • Цифра (0-9)\n"
            "  • Спецсимвол: ~ @ % & * $ ^ ! #\n"
            "  • Пароль не должен содержать имя пользователя"
        )
        hint.setStyleSheet("color: gray; font-size: 11px;")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        outer.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.save_btn)

        if not self.forced:
            cancel_btn = QPushButton("Отмена")
            cancel_btn.clicked.connect(self.reject)
            btn_row.addWidget(cancel_btn)

        outer.addLayout(btn_row)

    def _save(self):
        current = self.current_edit.text()
        new = self.new_edit.text()
        confirm = self.confirm_edit.text()

        if not current or not new or not confirm:
            self.status_label.setText("Заполните все поля")
            return
        if new != confirm:
            self.status_label.setText("Новые пароли не совпадают")
            return

        self.save_btn.setEnabled(False)
        result = self.api.change_password(current, new)
        self.save_btn.setEnabled(True)

        if result["ok"]:
            self.accept()
        else:
            err = result.get("error", "Ошибка")
            if isinstance(err, list):
                err = "; ".join(str(e) for e in err)
            self.status_label.setText(str(err))
