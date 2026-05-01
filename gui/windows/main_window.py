from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar,
    QAction, QMenuBar, QMessageBox, QLabel,
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
)

from gui.utils import ApiClient
from gui.windows.calc_window import CalcWindow
from gui.windows.history_window import HistoryWindow
from gui.windows.admin_window import AdminWindow
from gui.windows.change_password_window import ChangePasswordWindow


class MainWindow(QMainWindow):
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api = api_client
        self.setWindowTitle(f"ТЭС Оптимизация — {api_client.username} ({api_client.role})")
        self.resize(1100, 700)
        self._build_ui()

    def _build_ui(self):
        # Menu bar (macOS — отображается в системной строке вверху экрана)
        menu_bar = self.menuBar()
        user_menu = menu_bar.addMenu("Пользователь")

        chg_pwd_action = QAction("Сменить пароль", self)
        chg_pwd_action.triggered.connect(self._change_password)
        user_menu.addAction(chg_pwd_action)
        user_menu.addSeparator()
        logout_action = QAction("Выйти", self)
        logout_action.triggered.connect(self._logout)
        user_menu.addAction(logout_action)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Toolbar внутри окна (видна всегда, независимо от macOS)
        toolbar = QWidget()
        toolbar.setStyleSheet("background: #1a6faf;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 4, 10, 4)

        user_lbl = QLabel(f"  Пользователь: {self.api.username}   Роль: {self.api.role}")
        user_lbl.setStyleSheet("color: white; font-size: 12px;")
        toolbar_layout.addWidget(user_lbl)
        toolbar_layout.addStretch()

        chg_btn = QPushButton("Сменить пароль")
        chg_btn.setStyleSheet(
            "color: white; background: #155a8a; border: 1px solid #aad4f5;"
            "padding: 3px 10px; border-radius: 3px;")
        chg_btn.clicked.connect(self._change_password)
        toolbar_layout.addWidget(chg_btn)

        logout_btn = QPushButton("Выйти")
        logout_btn.setStyleSheet(
            "color: white; background: #c0392b; border: none;"
            "padding: 3px 14px; border-radius: 3px; font-weight: bold;")
        logout_btn.clicked.connect(self._logout)
        toolbar_layout.addWidget(logout_btn)

        outer.addWidget(toolbar)

        # Tabs
        self.tabs = QTabWidget()
        outer.addWidget(self.tabs)

        self.calc_tab = CalcWindow(self.api)
        self.tabs.addTab(self.calc_tab, "Расчёт")

        self.history_tab = HistoryWindow(self.api)
        self.tabs.addTab(self.history_tab, "История")

        if self.api.role == "admin":
            self.admin_tab = AdminWindow(self.api)
            self.tabs.addTab(self.admin_tab, "Администрирование")

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            f"Вы вошли как: {self.api.username}  |  Роль: {self.api.role}"
        )

    def _change_password(self):
        dlg = ChangePasswordWindow(self.api, forced=False, parent=self)
        if dlg.exec_():
            QMessageBox.information(self, "Готово", "Пароль успешно изменён")

    def _logout(self):
        self.api.logout()
        self.close()
