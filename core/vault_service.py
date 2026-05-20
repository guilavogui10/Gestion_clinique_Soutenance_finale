"""
vault_service.py
----------------
Service HashiCorp Vault pour :
  - Moteur TOTP : generation et verification de codes OTP (MFA par email)
  - Moteur Transit : HMAC SHA-256 pour l'integrite des fichiers medicaux

Configuration lue depuis le fichier .env a la racine du projet :
    VAULT_URL   = http://<hote>:8200
    VAULT_TOKEN = <jeton_vault>
    EMAIL_HOST  = smtp.gmail.com
    EMAIL_PORT  = 587
    EMAIL_USER  = <adresse expediteur>
    EMAIL_PASS  = <mot de passe application>

Prerequis Vault (a executer une seule fois sur le serveur) :
    vault secrets enable totp
    vault secrets enable transit
    vault write -f transit/keys/clinique-hmac type=hmac
"""

import base64
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import hvac
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT / ".env")


class VaultService:
    """
    Facade vers HashiCorp Vault.
    """

    TOTP_MOUNT = "totp"
    TRANSIT_MOUNT = "transit"
    TRANSIT_KEY = "clinique-hmac"

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Configurer le niveau de log pour voir les erreurs
        logging.basicConfig(level=logging.INFO)
        
        self.client = hvac.Client(
            url=os.getenv("VAULT_URL", "http://127.0.0.1:8200"),
            token=os.getenv("VAULT_TOKEN"),
        )
        
        # Afficher l'état de connexion au démarrage
        try:
            if self.client.is_authenticated():
                self.logger.info("[Vault] Connexion réussie à %s", os.getenv("VAULT_URL"))
            else:
                self.logger.error("[Vault] Échec d'authentification")
        except Exception as e:
            self.logger.error("[Vault] Erreur de connexion: %s", e)

        self._email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self._email_port = int(os.getenv("EMAIL_PORT", 587))
        self._email_user = os.getenv("EMAIL_USER", "")
        self._email_pass = os.getenv("EMAIL_PASS", "")

    # ------------------------------------------------------------------
    # Sante
    # ------------------------------------------------------------------

    def est_connecte(self) -> bool:
        """Retourne True si le client Vault est authentifie et actif."""
        try:
            return self.client.is_authenticated()
        except Exception:
            return False

    # ------------------------------------------------------------------
    # TOTP - gestion des cles
    # ------------------------------------------------------------------

    def creer_cle_totp(self, identifiant: str, account_name: str | None = None) -> bool:
        """
        Cree une cle TOTP dans Vault pour un identifiant donne.
        Retourne True si la cle existe deja ou si elle a ete creee.
        
        Duree de validite : 5 minutes (300 secondes)
        """
        try:
            # Vérifier d'abord si la clé existe déjà
            try:
                code_test = self.generer_code_otp(identifiant)
                if code_test:
                    self.logger.info("[Vault] Cle TOTP existe deja pour %s", identifiant)
                    return True
            except:
                pass  # La clé n'existe pas, on va la créer
            
            # Créer la clé TOTP via API directe avec période de 300 secondes (5 minutes)
            path = f"{self.TOTP_MOUNT}/keys/{identifiant}"
            payload = {
                "generate": True,
                "issuer": "CliniqueMFA",
                "account_name": account_name or identifiant,
                "period": 300,  # 5 minutes (300 secondes)
                "algorithm": "SHA256",
                "digits": 6,
            }
            self.client.write(path, **payload)
            self.logger.info("[Vault] Cle TOTP creee pour %s (validite: 5 minutes)", identifiant)
            return True
        except Exception as e:
            self.logger.error("[Vault] creer_cle_totp(%s): %s", identifiant, e)
            return False

    def supprimer_cle_totp(self, identifiant: str) -> bool:
        """Supprime la cle TOTP d'un utilisateur."""
        try:
            path = f"{self.TOTP_MOUNT}/keys/{identifiant}"
            self.client.delete(path)
            return True
        except Exception as e:
            self.logger.error("[Vault] supprimer_cle_totp(%s): %s", identifiant, e)
            return False

    # ------------------------------------------------------------------
    # TOTP - generation et verification
    # ------------------------------------------------------------------

    def generer_code_otp(self, identifiant: str) -> str | None:
        """Demande a Vault de generer le code TOTP courant."""
        try:
            path = f"{self.TOTP_MOUNT}/code/{identifiant}"
            resp = self.client.read(path)
            if resp and "data" in resp and "code" in resp["data"]:
                return resp["data"]["code"]
            return None
        except Exception as e:
            self.logger.error("[Vault] generer_code_otp(%s): %s", identifiant, e)
            return None

    def verifier_code_otp(self, identifiant: str, code: str) -> bool:
        """Verifie le code OTP saisi par l'utilisateur."""
        try:
            path = f"{self.TOTP_MOUNT}/code/{identifiant}"
            payload = {"code": str(code).strip()}
            resp = self.client.write(path, **payload)
            if resp and "data" in resp and "valid" in resp["data"]:
                return bool(resp["data"]["valid"])
            return False
        except Exception as e:
            self.logger.error("[Vault] verifier_code_otp(%s): %s", identifiant, e)
            return False

    # ------------------------------------------------------------------
    # Email - envoi du code OTP
    # ------------------------------------------------------------------

    def envoyer_otp_par_email(self, destinataire: str, code: str, prenom: str = "") -> bool:
        """Envoie le code OTP par email via SMTP TLS."""
        salutation = f"Bonjour {prenom.strip()}," if prenom.strip() else "Bonjour,"
        corps = (
            f"{salutation}\n\n"
            "Une tentative de connexion a ete detectee sur votre compte.\n\n"
            "Votre code de verification est :\n\n"
            f"        {code}\n\n"
            "Ce code est valable 5 minutes. Ne le communiquez a personne.\n\n"
            "Si vous n'etes pas a l'origine de cette connexion, "
            "veuillez contacter l'administrateur immediatement.\n\n"
            "Cordialement,\n"
            "Le systeme de gestion de la clinique"
        )
        try:
            if not self._email_user or not self._email_pass:
                raise ValueError("Configuration EMAIL_USER/EMAIL_PASS manquante")

            msg = MIMEMultipart()
            msg["From"] = self._email_user
            msg["To"] = destinataire
            msg["Subject"] = "Code de verification - Connexion Clinique"
            msg.attach(MIMEText(corps, "plain", "utf-8"))

            with smtplib.SMTP(self._email_host, self._email_port) as serveur:
                serveur.ehlo()
                serveur.starttls()
                serveur.login(self._email_user, self._email_pass)
                serveur.sendmail(self._email_user, destinataire, msg.as_string())

            self.logger.info("[Vault] OTP envoye a %s", destinataire)
            return True
        except Exception as e:
            self.logger.error("[Vault] envoyer_otp_par_email(%s): %s", destinataire, e)
            return False

    # ------------------------------------------------------------------
    # Transit - intégrité des fichiers médicaux (avec chiffrement)
    # ------------------------------------------------------------------

    def calculer_hmac(self, donnees: bytes) -> str | None:
        """
        Calcule un hash via Vault Transit pour des données binaires.
        Utilise le chiffrement puis déchiffrement pour vérifier l'intégrité.
        Retourne la chaîne chiffrée au format 'vault:v1:...' ou None si erreur.
        """
        try:
            b64 = base64.b64encode(donnees).decode("utf-8")
            path = f"{self.TRANSIT_MOUNT}/encrypt/{self.TRANSIT_KEY}"
            payload = {"plaintext": b64}
            resp = self.client.write(path, **payload)
            if resp and "data" in resp and "ciphertext" in resp["data"]:
                return resp["data"]["ciphertext"]
            return None
        except Exception as e:
            self.logger.error("[Vault] calculer_hmac: %s", e)
            return None

    def verifier_hmac(self, donnees: bytes, hmac_attendu: str) -> bool:
        """
        Vérifie l'intégrité de données en comparant les hash.
        Retourne True si les données n'ont pas été altérées.
        """
        try:
            # Calculer le hash actuel des données
            hash_actuel = self.calculer_hmac(donnees)
            if not hash_actuel:
                self.logger.error("[Vault] Impossible de calculer le hash actuel")
                return False
            
            # Déchiffrer le hash attendu pour obtenir les données originales
            try:
                path = f"{self.TRANSIT_MOUNT}/decrypt/{self.TRANSIT_KEY}"
                payload = {"ciphertext": hmac_attendu}
                resp = self.client.write(path, **payload)
                
                if not resp or "data" not in resp or "plaintext" not in resp["data"]:
                    self.logger.error("[Vault] Réponse de déchiffrement invalide")
                    return False
                
                # Déchiffrer le hash actuel pour comparer
                path_actuel = f"{self.TRANSIT_MOUNT}/decrypt/{self.TRANSIT_KEY}"
                payload_actuel = {"ciphertext": hash_actuel}
                resp_actuel = self.client.write(path_actuel, **payload_actuel)
                
                if not resp_actuel or "data" not in resp_actuel or "plaintext" not in resp_actuel["data"]:
                    self.logger.error("[Vault] Impossible de déchiffrer le hash actuel")
                    return False
                
                # Comparer les données déchiffrées
                donnees_attendues = resp["data"]["plaintext"]
                donnees_actuelles = resp_actuel["data"]["plaintext"]
                
                resultat = donnees_attendues == donnees_actuelles
                
                if resultat:
                    self.logger.info("[Vault] Vérification HMAC réussie")
                else:
                    self.logger.warning("[Vault] Vérification HMAC échouée - données altérées")
                
                return resultat
                
            except Exception as e:
                self.logger.error("[Vault] Erreur lors du déchiffrement: %s", e)
                return False
                
        except Exception as e:
            self.logger.error("[Vault] verifier_hmac: %s", e)
            return False
