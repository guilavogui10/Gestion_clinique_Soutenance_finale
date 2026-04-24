import sys
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from views.shared.styles import Styles

if __name__ == "__main__":
    # 1. Créer l'application
    app = QApplication(sys.argv)
    
    # 2. Appliquer le style global dynamique (basé sur le thème actif)
    app.setStyleSheet(Styles.global_qss())

    # 3. Lancer la fenêtre
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
    