from dashboard import Dashboard, STYLESHEET
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont
import sys


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    QFontDatabase.addApplicationFont("JetBrainsMono-Regular.ttf")
    app.setFont(QFont("Consolas", 10))

    window = Dashboard()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()