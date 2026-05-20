import sys
import logging
import atexit
import time
from PySide6.QtWidgets import QApplication, QSplashScreen, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont
from views.main_window import MainWindow
from views.shared.styles import Styles
from core.vault_manager import get_vault_manager
from core.minio_manager import get_minio_manager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def creer_splash_screen(app):
    """Crée un écran de chargement moderne."""
    splash = QSplashScreen()
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    
    # Créer un widget pour l'écran de chargement
    label = QLabel()
    label.setStyleSheet("""
        QLabel {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #3D9B9B, stop:1 #2C7A7B
            );
            color: white;
            padding: 40px;
            border-radius: 15px;
        }
    """)
    
    label.setText(
        "<div style='text-align: center;'>"
        "<h1 style='font-size: 28px; margin-bottom: 20px;'>🏥 Clinique VisionCare</h1>"
        "<p style='font-size: 16px; margin-bottom: 10px;'>Initialisation en cours...</p>"
        "<p style='font-size: 14px; color: #E0F2F1;'>Démarrage de Vault 🔐</p>"
        "</div>"
    )
    label.setAlignment(Qt.AlignCenter)
    label.setMinimumSize(400, 200)
    
    splash.setPixmap(label.grab())
    splash.show()
    app.processEvents()
    
    return splash


def initialiser_vault(splash, app):
    """Initialise Vault en arrière-plan avec mise à jour du splash screen."""
    try:
        # Mettre à jour le message
        splash.showMessage(
            "Vérification de Vault...",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
        app.processEvents()
        
        vault_manager = get_vault_manager()
        
        # Vérifier si Vault est installé
        if not vault_manager.est_vault_installe():
            logger.warning("Vault n'est pas installé - L'application fonctionnera en mode dégradé")
            splash.showMessage(
                "⚠️ Vault non installé - Mode dégradé",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.yellow
            )
            app.processEvents()
            QTimer.singleShot(2000, lambda: None)  # Pause de 2 secondes
            return False
        
        # Démarrer et configurer Vault
        splash.showMessage(
            "Démarrage de Vault (cela peut prendre 10-30 secondes)...",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
        app.processEvents()
        
        if vault_manager.initialiser():
            splash.showMessage(
                "✓ Vault initialisé avec succès",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.green
            )
            app.processEvents()
            time.sleep(1)  # Laisser l'utilisateur voir le message de succès
            logger.info("Vault initialisé avec succès")
            return True
        else:
            logger.warning("Impossible d'initialiser Vault - Mode dégradé")
            splash.showMessage(
                "⚠️ Vault non disponible - Mode dégradé",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.yellow
            )
            app.processEvents()
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de Vault: {e}")
        splash.showMessage(
            f"⚠️ Erreur Vault: {str(e)}",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.red
        )
        app.processEvents()
        return False


def initialiser_minio(splash, app):
    """Initialise MinIO en arrière-plan avec mise à jour du splash screen."""
    try:
        # Mettre à jour le message
        splash.showMessage(
            "Vérification de MinIO...",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
        app.processEvents()
        
        minio_manager = get_minio_manager()
        
        # Vérifier si MinIO est installé
        if not minio_manager.est_minio_installe():
            logger.warning("MinIO n'est pas installé - Stockage de fichiers désactivé")
            splash.showMessage(
                "⚠️ MinIO non installé - Stockage désactivé",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.yellow
            )
            app.processEvents()
            time.sleep(1)
            return False
        
        # Démarrer et configurer MinIO
        splash.showMessage(
            "Démarrage de MinIO (cela peut prendre 10-30 secondes)...",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
        app.processEvents()
        
        if minio_manager.initialiser():
            splash.showMessage(
                "✓ MinIO initialisé avec succès",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.green
            )
            app.processEvents()
            time.sleep(1)  # Laisser l'utilisateur voir le message de succès
            logger.info("MinIO initialisé avec succès")
            return True
        else:
            logger.warning("Impossible d'initialiser MinIO - Stockage désactivé")
            splash.showMessage(
                "⚠️ MinIO non disponible - Stockage désactivé",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.yellow
            )
            app.processEvents()
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de MinIO: {e}")
        splash.showMessage(
            f"⚠️ Erreur MinIO: {str(e)}",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.red
        )
        app.processEvents()
        return False


if __name__ == "__main__":
    # 1. Créer l'application
    app = QApplication(sys.argv)
    
    # 2. Appliquer le style global dynamique (basé sur le thème actif)
    app.setStyleSheet(Styles.global_qss())
    
    # 3. Afficher l'écran de chargement
    splash = creer_splash_screen(app)
    
    # 4. Initialiser Vault en arrière-plan
    vault_ok = initialiser_vault(splash, app)
    
    # 4.5. Attendre un peu plus pour que Vault soit complètement prêt
    if vault_ok:
        splash.showMessage(
            "Configuration de Vault en cours...",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
        app.processEvents()
        time.sleep(2)  # Attendre 2 secondes supplémentaires
    
    # 5. Initialiser MinIO en arrière-plan
    minio_ok = initialiser_minio(splash, app)
    
    # 5.5. Attendre un peu plus pour que MinIO soit complètement prêt
    if minio_ok:
        splash.showMessage(
            "Configuration de MinIO en cours...",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
        app.processEvents()
        time.sleep(1)  # Attendre 1 seconde supplémentaire
    
    # 6. Enregistrer l'arrêt des services à la fermeture de l'application
    if vault_ok:
        vault_manager = get_vault_manager()
        atexit.register(vault_manager.arreter_vault)
    
    if minio_ok:
        minio_manager = get_minio_manager()
        atexit.register(minio_manager.arreter_minio)
    
    # 7. Attendre un peu pour que l'utilisateur voie le message
    QTimer.singleShot(1500, lambda: None)
    app.processEvents()
    
    # 8. Fermer le splash screen et lancer la fenêtre principale
    splash.finish(None)
    
    # 9. Lancer la fenêtre
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
    