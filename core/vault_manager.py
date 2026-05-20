"""
vault_manager.py
----------------
Gestionnaire de démarrage automatique de HashiCorp Vault.
Lance Vault en arrière-plan et configure les moteurs automatiquement.
"""

import logging
import os
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class VaultManager:
    """Gestionnaire de Vault pour démarrage/arrêt automatique."""

    def __init__(self):
        self.vault_process = None
        self.vault_addr = "http://127.0.0.1:8200"
        self.vault_token = "mon_token_secret"

    def est_vault_installe(self) -> bool:
        """Vérifie si Vault est installé sur le système."""
        try:
            result = subprocess.run(
                ["vault", "version"],
                capture_output=True,
                text=True,
                timeout=10,  # Augmenté de 5 à 10 secondes
                shell=True  # Utiliser shell pour Windows
            )
            if result.returncode == 0:
                logger.info(f"[Vault] Version détectée: {result.stdout.strip()}")
                return True
            return False
        except subprocess.TimeoutExpired:
            logger.warning("[Vault] Timeout lors de la vérification de la version")
            return False
        except FileNotFoundError:
            logger.warning("[Vault] Commande 'vault' introuvable")
            return False
        except Exception as e:
            logger.error(f"[Vault] Erreur lors de la vérification: {e}")
            return False

    def est_vault_actif(self) -> bool:
        """Vérifie si un serveur Vault est déjà actif."""
        try:
            env = os.environ.copy()
            env["VAULT_ADDR"] = self.vault_addr
            env["VAULT_TOKEN"] = self.vault_token
            
            result = subprocess.run(
                ["vault", "status"],
                capture_output=True,
                text=True,
                timeout=10,  # Augmenté de 5 à 10 secondes
                env=env,
                shell=True  # Utiliser shell pour Windows
            )
            # Vault retourne 0 si déscellé, 2 si scellé, autre si erreur
            is_active = result.returncode in [0, 2]
            if is_active:
                logger.info("[Vault] Serveur Vault détecté comme actif")
            return is_active
        except subprocess.TimeoutExpired:
            logger.warning("[Vault] Timeout lors de la vérification du statut")
            return False
        except FileNotFoundError:
            logger.warning("[Vault] Commande 'vault' introuvable")
            return False
        except Exception as e:
            logger.error(f"[Vault] Erreur lors de la vérification du statut: {e}")
            return False

    def demarrer_vault(self) -> bool:
        """
        Démarre le serveur Vault en mode développement en arrière-plan.
        Retourne True si le démarrage a réussi.
        """
        try:
            # Vérifier si Vault est installé
            if not self.est_vault_installe():
                logger.warning("[Vault] Vault n'est pas installé sur ce système")
                return False

            # Vérifier si Vault est déjà actif
            if self.est_vault_actif():
                logger.info("[Vault] Serveur Vault déjà actif")
                return True

            logger.info("[Vault] Démarrage du serveur Vault...")

            # Démarrer Vault en mode développement en arrière-plan
            # CREATE_NO_WINDOW pour Windows (ne pas afficher de console)
            startupinfo = None
            creation_flags = 0
            
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                # CREATE_NO_WINDOW si disponible (Python 3.7+)
                if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                    creation_flags = subprocess.CREATE_NO_WINDOW

            self.vault_process = subprocess.Popen(
                [
                    "vault", "server", "-dev",
                    f"-dev-root-token-id={self.vault_token}"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=creation_flags,
                shell=True  # Utiliser shell pour Windows
            )

            # Attendre que Vault soit prêt (max 30 secondes)
            for i in range(60):
                time.sleep(0.5)
                if self.est_vault_actif():
                    logger.info("[Vault] Serveur Vault démarré avec succès")
                    return True

            logger.error("[Vault] Timeout lors du démarrage de Vault")
            return False

        except Exception as e:
            logger.error(f"[Vault] Erreur lors du démarrage: {e}")
            return False

    def configurer_moteurs(self) -> bool:
        """
        Configure les moteurs TOTP et Transit dans Vault.
        Retourne True si la configuration a réussi.
        """
        try:
            env = os.environ.copy()
            env["VAULT_ADDR"] = self.vault_addr
            env["VAULT_TOKEN"] = self.vault_token

            logger.info("[Vault] Configuration des moteurs...")

            # Activer le moteur TOTP
            result = subprocess.run(
                ["vault", "secrets", "enable", "totp"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
                shell=True  # Utiliser shell pour Windows
            )
            if result.returncode == 0:
                logger.info("[Vault] ✓ Moteur TOTP activé")
            elif "path is already in use" in result.stderr:
                logger.info("[Vault] ✓ Moteur TOTP déjà activé")
            else:
                logger.warning(f"[Vault] Erreur TOTP: {result.stderr}")

            # Activer le moteur Transit
            result = subprocess.run(
                ["vault", "secrets", "enable", "transit"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
                shell=True  # Utiliser shell pour Windows
            )
            if result.returncode == 0:
                logger.info("[Vault] ✓ Moteur Transit activé")
            elif "path is already in use" in result.stderr:
                logger.info("[Vault] ✓ Moteur Transit déjà activé")
            else:
                logger.warning(f"[Vault] Erreur Transit: {result.stderr}")

            # Créer la clé de chiffrement
            result = subprocess.run(
                ["vault", "write", "transit/keys/clinique-hmac", "type=aes256-gcm96"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
                shell=True  # Utiliser shell pour Windows
            )
            if result.returncode == 0:
                logger.info("[Vault] ✓ Clé de chiffrement créée")
            elif "already exists" in result.stderr.lower():
                logger.info("[Vault] ✓ Clé de chiffrement déjà existante")
            else:
                logger.warning(f"[Vault] Erreur clé: {result.stderr}")

            logger.info("[Vault] Configuration terminée avec succès")
            return True

        except Exception as e:
            logger.error(f"[Vault] Erreur lors de la configuration: {e}")
            return False

    def initialiser(self) -> bool:
        """
        Initialise Vault : démarre le serveur et configure les moteurs.
        Retourne True si tout s'est bien passé.
        """
        try:
            # Démarrer Vault
            if not self.demarrer_vault():
                logger.warning("[Vault] Impossible de démarrer Vault - Mode dégradé")
                return False

            # Configurer les moteurs
            if not self.configurer_moteurs():
                logger.warning("[Vault] Impossible de configurer les moteurs")
                return False

            logger.info("[Vault] Initialisation complète réussie ✓")
            return True

        except Exception as e:
            logger.error(f"[Vault] Erreur lors de l'initialisation: {e}")
            return False

    def arreter_vault(self):
        """Arrête proprement le serveur Vault."""
        try:
            if self.vault_process:
                logger.info("[Vault] Arrêt du serveur Vault...")
                self.vault_process.terminate()
                self.vault_process.wait(timeout=5)
                logger.info("[Vault] Serveur Vault arrêté")
        except Exception as e:
            logger.error(f"[Vault] Erreur lors de l'arrêt: {e}")
            if self.vault_process:
                self.vault_process.kill()


# Instance globale
_vault_manager = None


def get_vault_manager() -> VaultManager:
    """Retourne l'instance globale du gestionnaire Vault."""
    global _vault_manager
    if _vault_manager is None:
        _vault_manager = VaultManager()
    return _vault_manager
