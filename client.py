"""Клиентское приложение PyQt5."""
import sys

from PyQt5.QtWidgets import QApplication

from gui.utils import ApiClient
from gui.windows.login_window import LoginWindow
from gui.windows.change_password_window import ChangePasswordWindow
from gui.windows.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    while True:
        api = ApiClient()

        # Окно входа
        login_win = LoginWindow(api)
        if login_win.exec_() != login_win.Accepted:
            break

        # Принудительная смена пароля при первом входе
        if api.must_change_password:
            chg_win = ChangePasswordWindow(api, forced=True)
            if chg_win.exec_() != chg_win.Accepted:
                api.logout()
                continue  # вернуться к окну входа

        # Главное окно
        main_win = MainWindow(api)
        main_win.show()
        app.exec_()

        # После закрытия главного окна — снова показать окно входа


if __name__ == "__main__":
    main()
