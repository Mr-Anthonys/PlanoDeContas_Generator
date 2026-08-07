"""Ponto de entrada do Gerador de Plano de Contas e Scripts SQL."""

from src.gui.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
