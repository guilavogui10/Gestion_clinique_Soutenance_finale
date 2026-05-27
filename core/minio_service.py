"""
minio_service.py
-----------------
Service MinIO pour le stockage des fichiers médicaux (PDF, image, vidéo).
Lit la configuration depuis le fichier .env à la racine du projet.

Utilisation :
    from core.minio_service import MinIOService
    svc = MinIOService()
    url = svc.upload_fichier("/chemin/local/scan.pdf", "pdf", "RES-00000001")
    svc.supprimer_fichier("resultat/RES-00000001/scan.pdf")
    url_temp = svc.get_url_temporaire("resultat/RES-00000001/scan.pdf", duree_minutes=60)
"""

import os
import io
import logging
from pathlib import Path
from datetime import timedelta

from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

# Charger .env depuis la racine du projet (un niveau au-dessus de 'core')
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


class MinIOService:
    """
    Service d'accès à un serveur MinIO.
    Toutes les configurations sont lues depuis le fichier .env.
    """

    # Extensions autorisées par type
    EXTENSIONS_AUTORISEES = {
        "image": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"},
        "video": {".mp4", ".avi", ".mov", ".mkv", ".webm"},
        "pdf":   {".pdf"},
    }

    # Taille maximale : 50 Mo
    TAILLE_MAX_OCTETS = 50 * 1024 * 1024

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        endpoint   = os.getenv("MINIO_ENDPOINT",   "127.0.0.1:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY",  "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY",  "minioadmin")
        secure_str = os.getenv("MINIO_SECURE",       "False")
        self.bucket = os.getenv("MINIO_BUCKET",      "clinique-data")

        self.secure = secure_str.strip().lower() in ("true", "1", "yes")

        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=self.secure,
        )

        # Flag de disponibilité — False si MinIO n'est pas joignable
        self.disponible = False
        self._verifier_bucket()

    # =========================================================================
    # INITIALISATION
    # =========================================================================

    def _verifier_bucket(self) -> None:
        """Vérifie que le bucket existe, le crée s'il n'existe pas."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                self.logger.info(f"[MinIO] Bucket '{self.bucket}' créé.")
            else:
                self.logger.debug(f"[MinIO] Bucket '{self.bucket}' OK.")
            self.disponible = True
        except S3Error as e:
            self.logger.error(f"[MinIO] Erreur vérification bucket: {e}")
            self.disponible = False
        except Exception as e:
            # MinIO non démarré (ConnectionRefusedError, NewConnectionError, etc.)
            self.logger.warning(
                f"[MinIO] Service non disponible (le serveur MinIO n'est peut-être pas démarré) : {e}"
            )
            self.disponible = False

    # =========================================================================
    # UPLOAD
    # =========================================================================

    def upload_fichier(self,
                       chemin_local: str,
                       type_fichier: str,
                       id_resultat: str) -> str | None:
        if not self.disponible:
            self.logger.warning("[MinIO] upload_fichier ignoré : service non disponible.")
            return None
        chemin = Path(chemin_local)
        if not chemin.is_file():
            self.logger.error(f"[MinIO] Fichier introuvable : {chemin_local}")
            return None

        # Validation extension
        ext = chemin.suffix.lower()
        exts_ok = self.EXTENSIONS_AUTORISEES.get(type_fichier, set())
        if ext not in exts_ok:
            self.logger.error(
                f"[MinIO] Extension '{ext}' non autorisée pour type '{type_fichier}'. "
                f"Attendu : {exts_ok}"
            )
            return None

        # Validation taille
        taille = chemin.stat().st_size
        if taille > self.TAILLE_MAX_OCTETS:
            self.logger.error(
                f"[MinIO] Fichier trop volumineux ({taille} octets > {self.TAILLE_MAX_OCTETS})"
            )
            return None

        # Nom de l'objet : resultat/<id>/<nom_fichier>
        object_name = f"resultat/{id_resultat}/{chemin.name}"

        content_type = self._content_type(ext)

        try:
            self.client.fput_object(
                self.bucket,
                object_name,
                str(chemin),
                content_type=content_type,
            )
            self.logger.info(f"[MinIO] Upload OK : {object_name}")
            return object_name
        except S3Error as e:
            self.logger.error(f"[MinIO] Erreur upload : {e}")
            return None

    def upload_bytes(self,
                     data: bytes,
                     nom_fichier: str,
                     type_fichier: str,
                     id_resultat: str) -> str | None:
        if not self.disponible:
            self.logger.warning("[MinIO] upload_bytes ignoré : service non disponible.")
            return None
        ext = Path(nom_fichier).suffix.lower()
        exts_ok = self.EXTENSIONS_AUTORISEES.get(type_fichier, set())
        if ext not in exts_ok:
            self.logger.error(f"[MinIO] Extension '{ext}' non autorisée pour type '{type_fichier}'.")
            return None

        if len(data) > self.TAILLE_MAX_OCTETS:
            self.logger.error(f"[MinIO] Données trop volumineuses ({len(data)} octets).")
            return None

        object_name  = f"resultat/{id_resultat}/{nom_fichier}"
        content_type = self._content_type(ext)

        try:
            self.client.put_object(
                self.bucket,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            self.logger.info(f"[MinIO] Upload bytes OK : {object_name}")
            return object_name
        except S3Error as e:
            self.logger.error(f"[MinIO] Erreur upload bytes : {e}")
            return None

    # =========================================================================
    # TÉLÉCHARGEMENT & URL
    # =========================================================================

    def telecharger_fichier(self, object_name: str, destination: str) -> bool:
        """
        Télécharge un objet MinIO vers un chemin local.

        Args:
            object_name:  Nom de l'objet MinIO (valeur de chemin_fichier en BD).
            destination:  Chemin local de destination.

        Returns:
            True si succès, False sinon.
        """
        if not self.disponible:
            self.logger.warning("[MinIO] telecharger_fichier ignoré : service non disponible.")
            return False
        try:
            self.client.fget_object(self.bucket, object_name, destination)
            self.logger.info(f"[MinIO] Téléchargement OK : {object_name} → {destination}")
            return True
        except S3Error as e:
            self.logger.error(f"[MinIO] Erreur téléchargement : {e}")
            return False

    def get_url_temporaire(self, object_name: str, duree_minutes: int = 60) -> str | None:
        """
        Génère une URL présignée temporaire pour accéder directement au fichier.

        Args:
            object_name:    Nom de l'objet MinIO.
            duree_minutes:  Durée de validité de l'URL (défaut 60 min).

        Returns:
            URL de téléchargement temporaire, ou None en cas d'erreur.
        """
        if not self.disponible:
            self.logger.warning("[MinIO] get_url_temporaire ignoré : service non disponible.")
            return None
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(minutes=duree_minutes),
            )
            return url
        except S3Error as e:
            self.logger.error(f"[MinIO] Erreur génération URL : {e}")
            return None

    def lire_bytes(self, object_name: str) -> bytes | None:
        """
        Lit le contenu d'un objet MinIO directement en mémoire.

        Returns:
            Contenu binaire ou None.
        """
        if not self.disponible:
            self.logger.warning("[MinIO] lire_bytes ignoré : service non disponible.")
            return None
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            self.logger.error(f"[MinIO] Erreur lecture bytes : {e}")
            return None

    # =========================================================================
    # SUPPRESSION
    # =========================================================================

    def supprimer_fichier(self, object_name: str) -> bool:
        """
        Supprime un fichier du bucket MinIO.

        Args:
            object_name:  Valeur de chemin_fichier stockée en BD.

        Returns:
            True si supprimé, False sinon.
        """
        if not self.disponible:
            self.logger.warning("[MinIO] supprimer_fichier ignoré : service non disponible.")
            return False
        try:
            self.client.remove_object(self.bucket, object_name)
            self.logger.info(f"[MinIO] Suppression OK : {object_name}")
            return True
        except S3Error as e:
            self.logger.error(f"[MinIO] Erreur suppression : {e}")
            return False

    def supprimer_tous_fichiers_resultat(self, id_resultat: str) -> int:
        """
        Supprime tous les objets MinIO liés à un identifiant de résultat.
        Préfixe utilisé : resultat/<id_resultat>/

        Returns:
            Nombre d'objets supprimés.
        """
        if not self.disponible:
            self.logger.warning("[MinIO] supprimer_tous_fichiers_resultat ignoré : service non disponible.")
            return 0
        prefixe = f"resultat/{id_resultat}/"
        compteur = 0
        try:
            objets = self.client.list_objects(self.bucket, prefix=prefixe, recursive=True)
            for obj in objets:
                self.client.remove_object(self.bucket, obj.object_name)
                compteur += 1
            self.logger.info(
                f"[MinIO] {compteur} objet(s) supprimé(s) pour resultat {id_resultat}"
            )
        except S3Error as e:
            self.logger.error(f"[MinIO] Erreur suppression groupe : {e}")
        return compteur

    # =========================================================================
    # TEST DE CONNEXION
    # =========================================================================

    def tester_connexion(self) -> bool:
        """
        Vérifie que la connexion au serveur MinIO fonctionne.
        Utile au démarrage de l'application.

        Returns:
            True si le bucket est accessible, False sinon.
        """
        try:
            existe = self.client.bucket_exists(self.bucket)
            if existe:
                self.logger.info(f"[MinIO] Connexion OK — bucket '{self.bucket}' accessible.")
            else:
                self.logger.warning(f"[MinIO] Connexion OK mais bucket '{self.bucket}' introuvable.")
            return existe
        except Exception as e:
            self.logger.error(f"[MinIO] Connexion échouée : {e}")
            return False

    # =========================================================================
    # UTILITAIRES PRIVÉS
    # =========================================================================

    @staticmethod
    def _content_type(ext: str) -> str:
        """Retourne le Content-Type MIME correspondant à l'extension."""
        types = {
            ".pdf":  "application/pdf",
            ".jpg":  "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png":  "image/png",
            ".gif":  "image/gif",
            ".bmp":  "image/bmp",
            ".tiff": "image/tiff",
            ".webp": "image/webp",
            ".mp4":  "video/mp4",
            ".avi":  "video/x-msvideo",
            ".mov":  "video/quicktime",
            ".mkv":  "video/x-matroska",
            ".webm": "video/webm",
        }
        return types.get(ext, "application/octet-stream")
