"""Ponto de entrada do Gerador de Plano de Contas e Scripts SQL."""

import tkinter as tk

from src.gui.connection_dialog import show_connection_dialog
from src.gui.main_window import MainWindow


def main():
    root = tk.Tk()
    root.withdraw()
    session = show_connection_dialog(root)
    root.destroy()
    if session is None:
        return

    app = MainWindow(session)
    app.mainloop()


if __name__ == "__main__":
    main()
