"""
minio_manager.py
----------------
Gestionnaire de demarrage automatique de MinIO.
Lance MinIO en arriere-plan et configure le bucket automatiquement.
"""

import logging
import os
import subprocess
import time
import requests

logger = logging.getLogger(__name__)


class MinIOManager:
    """Gestionnaire de MinIO pour demarrage/arret automatique."""

    def __init__(self):
        self.minio_process = None
        self.minio_api_port = "9000"
        self.minio_console_port = "9001"
        self.minio_root_user = "minioadmin"
        self.minio_root_password = "minioadmin"
        self.minio_data_dir = None

    def est_minio_installe(self) -> bool:
        """Verifie si MinIO est installe sur le systeme."""
        try:
            result = subprocess.run(
                ["minio", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            if result.returncode == 0:
                logger.info(f"[MinIO] Version detectee: {result.stdout.strip()}")
                return True
            return False
        except subprocess.TimeoutExpired:
            logger.warning("[MinIO] Timeout lors de la verification de la version")
            return False
        except FileNotFoundError:
            logger.warning("[MinIO] Commande 'minio' introuvable")
            return False
        except Exception as e:
            logger.error(f"[MinIO] Erreur lors de la verification: {e}")
            return False

    def est_minio_actif(self) -> bool:
        """Verifie si un serveur MinIO est deja actif."""
        try:
            response = requests.get(
                f"http://127.0.0.1:{self.minio_api_port}/minio/health/live",
                timeout=2
            )
            is_active = response.status_code == 200
            if is_active:
                logger.info("[MinIO] Serveur MinIO detecte comme actif")
            return is_active
        except requests.exceptions.RequestException:
            return False
        except Exception as e:
            logger.error(f"[MinIO] Erreur lors de la verification du statut: {e}")
            return False

    def demarrer_minio(self) -> bool:
        """
        Demarre le serveur MinIO en arriere-plan.
        Retourne True si le demarrage a reussi.
        """
        try:
            # Verifier si MinIO est installe
            if not self.est_minio_installe():
                logger.warning("[MinIO] MinIO n'est pas installe sur ce systeme")
                return False

            # Verifier si MinIO est deja actif
            if self.est_minio_actif():
                logger.info("[MinIO] Serveur MinIO deja actif")
                return True

            logger.info("[MinIO] Demarrage du serveur MinIO...")

            # Determiner le repertoire de donnees
            from pathlib import Path
            project_root = Path(__file__).resolve().parent.parent
            self.minio_data_dir = str(project_root / "minio_data")

            # Creer le repertoire s'il n'existe pas
            os.makedirs(self.minio_data_dir, exist_ok=True)
            logger.info(f"[MinIO] Repertoire de donnees: {self.minio_data_dir}")

            # Preparer les variables d'environnement
            env = os.environ.copy()
            env["MINIO_ROOT_USER"] = self.minio_root_user
            env["MINIO_ROOT_PASSWORD"] = self.minio_root_password

            # Configuration pour Windows (masquer la fenetre)
            startupinfo = None
            creation_flags = 0
            
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                    creation_flags = subprocess.CREATE_NO_WINDOW

            # Demarrer MinIO
            self.minio_process = subprocess.Popen(
                [
                    "minio", "server", self.minio_data_dir,
                    "--address", f":{self.minio_api_port}",
                    "--console-address", f":{self.minio_console_port}"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                startupinfo=startupinfo,
                creationflags=creation_flags,
                shell=True
            )

            # Attendre que MinIO soit pret (max 30 secondes)
            for i in range(60):
                time.sleep(0.5)
                if self.est_minio_actif():
                    logger.info("[MinIO] Serveur MinIO demarre avec succes")
                    return True

            logger.error("[MinIO] Timeout lors du demarrage de MinIO")
            return False

        except Exception as e:
            logger.error(f"[MinIO] Erreur lors du demarrage: {e}")
            return False

    def configurer_bucket(self) -> bool:
        """
        Configure le bucket 'clinique-data' dans MinIO.
        Retourne True si la configuration a reussi.
        """
        try:
            logger.info("[MinIO] Configuration du bucket 'clinique-data'...")

            # Verifier si mc (client MinIO) est installe
            try:
                result = subprocess.run(
                    ["mc", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                if result.returncode != 0:
                    logger.warning("[MinIO] Client 'mc' non installe - creation du bucket ignoree")
                    logger.info("[MinIO] Vous pouvez creer le bucket manuellement via http://127.0.0.1:9001")
                    return True  # Ne pas bloquer l'application
            except:
                logger.warning("[MinIO] Client 'mc' non installe - creation du bucket ignoree")
                return True

            # Configurer l'alias MinIO
            subprocess.run(
                [
                    "mc", "alias", "set", "local",
                    f"http://127.0.0.1:{self.minio_api_port}",
                    self.minio_root_user,
                    self.minio_root_password
                ],
                capture_output=True,
                timeout=10,
                shell=True
            )

            # Verifier si le bucket existe
            result = subprocess.run(
                ["mc", "ls", "local/clinique-data"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )

            if result.returncode == 0:
                logger.info("[MinIO] Bucket 'clinique-data' deja existant")
            else:
                # Creer le bucket
                result = subprocess.run(
                    ["mc", "mb", "local/clinique-data"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True
                )
                if result.returncode == 0:
                    logger.info("[MinIO] Bucket 'clinique-data' cree avec succes")
                else:
                    logger.warning(f"[MinIO] Erreur lors de la creation du bucket: {result.stderr}")

            return True

        except Exception as e:
            logger.error(f"[MinIO] Erreur lors de la configuration: {e}")
            return True  # Ne pas bloquer l'application

    def initialiser(self) -> bool:
        """
        Initialise MinIO : demarre le serveur et configure le bucket.
        Retourne True si tout s'est bien passe.
        """
        try:
            # Demarrer MinIO
            if not self.demarrer_minio():
                logger.warning("[MinIO] Impossible de demarrer MinIO - Mode degrade")
                return False

            # Configurer le bucket
            self.configurer_bucket()

            logger.info("[MinIO] Initialisation complete reussie")
            return True

        except Exception as e:
            logger.error(f"[MinIO] Erreur lors de l'initialisation: {e}")
            return False

    def arreter_minio(self):
        """Arrete proprement le serveur MinIO."""
        try:
            if self.minio_process:
                logger.info("[MinIO] Arret du serveur MinIO...")
                self.minio_process.terminate()
                self.minio_process.wait(timeout=5)
                logger.info("[MinIO] Serveur MinIO arrete")
        except Exception as e:
            logger.error(f"[MinIO] Erreur lors de l'arret: {e}")
            if self.minio_process:
                self.minio_process.kill()


# Instance globale
_minio_manager = None


def get_minio_manager() -> MinIOManager:
    """Retourne l'instance globale du gestionnaire MinIO."""
    global _minio_manager
    if _minio_manager is None:
        _minio_manager = MinIOManager()
    return _minio_manager
