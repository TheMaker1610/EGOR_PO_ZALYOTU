"""Клиентское приложение PyQt5."""
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

from gui.utils import ApiClient
from gui.windows.login_window import LoginWindow
from gui.windows.change_password_window import ChangePasswordWindow
from gui.windows.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    api = ApiClient()

    # Show login
    login_win = LoginWindow(api)
    if login_win.exec_() != login_win.Accepted:
        sys.exit(0)

    # Force password change if required
    if api.must_change_password:
        chg_win = ChangePasswordWindow(api, forced=True)
        if chg_win.exec_() != chg_win.Accepted:
            api.logout()
            sys.exit(0)

    # Main window
    main_win = MainWindow(api)
    main_win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
