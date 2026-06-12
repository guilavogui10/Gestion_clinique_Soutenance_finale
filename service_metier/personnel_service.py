import os
import re
import shutil
from datetime import datetime

from fpdf import FPDF
import pandas as pd

from core.vault_service import VaultService
from data.dao_personnel import PersonnelDAO
from models.modele_personnel import ModelePersonnel
from parametre.dao_param import CabinetDAO


class PersonnelService:
    def __init__(self, dao=None, cabinet_dao=None):
        self.dao = dao or PersonnelDAO()
        self.cabinet_dao = cabinet_dao or CabinetDAO()
        self.vault = VaultService()
        script_dir = os.path.dirname(__file__)
        self.image_folder = os.path.normpath(
            os.path.join(script_dir, "..", "connexion", "image")
        )
        os.makedirs(self.image_folder, exist_ok=True)

    def _modele_vers_dict(self, personnel):
        if personnel is None:
            return None
        if isinstance(personnel, dict):
            return personnel
        if hasattr(personnel, "to_dict"):
            return personnel.to_dict()
        return {
            "code": personnel.get_code(),
            "nom": personnel.get_nom(),
            "prenom": personnel.get_prenom(),
            "adresse": personnel.get_adresse(),
            "date_naissance": personnel.get_date_naissance(),
            "contact": personnel.get_contact(),
            "mail": personnel.get_mail(),
            "fonction": personnel.get_fonction(),
            "photo_path": personnel.get_photo_path(),
            "est_responsable": personnel.get_est_responsable(),
        }

    def _modeles_vers_dicts(self, personnels):
        return [self._modele_vers_dict(personnel) for personnel in personnels]

    def _creer_modele(self, code, data, photo_nom):
        return ModelePersonnel(
            code,
            data.get("nom").strip(),
            data.get("prenom").strip(),
            data.get("adresse").strip(),
            str(data.get("date_naissance")).strip(),
            str(data.get("contact")).strip(),
            data.get("mail").strip(),
            data.get("fonction").strip(),
            photo_nom,
            int(data.get("est_responsable", 0)),
        )

    def _valider_nom_prenom_fonction(self, valeur):
        if not valeur or len(valeur.strip()) < 3:
            return False, "Doit contenir au moins 3 caractères."
        if not re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s'-]+$", valeur):
            return False, "Ne doit contenir que des lettres (pas de chiffres ni caractères spéciaux)."
        return True, None

    def _valider_email(self, mail):
        if not mail or "@" not in mail or (not (mail.endswith(".com") or mail.endswith(".fr") or "." in mail.split("@")[-1])):
            return False, "Email invalide (doit contenir '@' et domaine valide)."
        pattern = r"^[^@]+@[^@]+\.[^@]+$"
        if not re.match(pattern, mail):
            return False, "Email invalide."
        return True, None

    def _valider_adresse(self, adresse):
        if not adresse or len(adresse.strip()) == 0:
            return False, "Adresse requise."
        if not re.match(r"^[A-Za-z0-9À-ÖØ-öø-ÿ\s,.\-/']+$", adresse):
            return False, "Adresse contient des caractères non autorisés."
        return True, None

    def _valider_contact(self, contact):
        if not contact:
            return False, "Contact requis."
        contact_clean = re.sub(r"[^\d]", "", str(contact))
        if len(contact_clean) != 9:
            return False, "Le contact doit contenir exactement 9 chiffres."
        return True, None

    def _valider_date(self, date_str):
        if isinstance(date_str, datetime):
            return True, None
        if pd.notna(date_str) and isinstance(date_str, float):
            date_str = str(pd.to_datetime(date_str).date())
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                datetime.strptime(str(date_str), fmt)
                return True, None
            except Exception:
                continue
        return False, "Date invalide. Format attendu: YYYY-MM-DD ou DD/MM/YYYY."

    def valider_champs(self, data):
        ok, msg = self._valider_nom_prenom_fonction(data.get("nom"))
        if not ok:
            return False, f"Nom: {msg}"

        ok, msg = self._valider_nom_prenom_fonction(data.get("prenom"))
        if not ok:
            return False, f"Prénom: {msg}"

        ok, msg = self._valider_nom_prenom_fonction(data.get("fonction"))
        if not ok:
            return False, f"Fonction: {msg}"

        ok, msg = self._valider_email(data.get("mail"))
        if not ok:
            return False, f"Email: {msg}"

        ok, msg = self._valider_adresse(data.get("adresse"))
        if not ok:
            return False, f"Adresse: {msg}"

        ok, msg = self._valider_contact(data.get("contact"))
        if not ok:
            return False, f"Contact: {msg}"

        ok, msg = self._valider_date(data.get("date_naissance"))
        if not ok:
            return False, f"Date de naissance: {msg}"

        return True, None

    def _copier_photo_et_retourner_nom(self, source_path):
        if not source_path:
            return None, "Aucun chemin photo fourni."
        if not os.path.exists(source_path):
            return None, f"Fichier photo introuvable: {source_path}"
        try:
            filename = os.path.basename(source_path)
            dest = os.path.join(self.image_folder, filename)
            if os.path.exists(dest):
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{name}_{timestamp}{ext}"
                dest = os.path.join(self.image_folder, filename)
            shutil.copy2(source_path, dest)
            return filename, None
        except Exception as e:
            return None, f"Erreur copie photo: {e}"

    def ajouter_personnel(self, data):
        valid, msg = self.valider_champs(data)
        if not valid:
            return False, msg
        
        # Vérifier que l'email n'existe pas déjà
        email = data.get("mail", "").strip().lower()
        if email:
            personnel_existant = self.obtenir_par_mail(email)
            if personnel_existant:
                return False, f"Cet email est déjà utilisé par le personnel {personnel_existant.get_prenom()} {personnel_existant.get_nom()}."

        photo_nom = None
        if data.get("photo_path"):
            photo_nom, err = self._copier_photo_et_retourner_nom(data["photo_path"])
            if err:
                return False, err

        code = self.dao.generer_nouveau_code()
        personnel = self._creer_modele(code, data, photo_nom)
        ok = self.dao.enregistrer_personnel(personnel)
        if ok:
            # Créer automatiquement une clé TOTP Vault pour ce personnel
            self._creer_cle_vault_personnel(code, data)
            return True, f"Personnel enregistré avec code {code}."
        return False, "Erreur lors de l'enregistrement en base."

    def modifier_personnel(self, code, data):
        existing = self.dao.obtenir_par_code(code)
        if not existing:
            return False, "Personnel introuvable."

        valid, msg = self.valider_champs(data)
        if not valid:
            return False, msg
        
        # Vérifier que l'email n'est pas utilisé par un autre personnel
        email = data.get("mail", "").strip().lower()
        if email:
            personnel_existant = self.obtenir_par_mail(email)
            if personnel_existant and personnel_existant.get_code() != code:
                return False, f"Cet email est déjà utilisé par le personnel {personnel_existant.get_prenom()} {personnel_existant.get_nom()}."

        photo_nom = existing.get_photo_path()
        if data.get("photo_path"):
            photo_nom_new, err = self._copier_photo_et_retourner_nom(data["photo_path"])
            if err:
                return False, err
            photo_nom = photo_nom_new

        personnel = self._creer_modele(code, data, photo_nom)
        ok = self.dao.modifier_personnel(personnel)
        if ok:
            return True, "Personnel mis à jour."
        return False, "Erreur mise à jour en base."

    def supprimer_par_mail(self, mail):
        # Récupérer le personnel avant suppression pour obtenir son code
        personnel = self.obtenir_par_mail(mail)
        if personnel:
            code = personnel.get_code()
            # Supprimer la clé TOTP Vault
            self._supprimer_cle_vault_personnel(code)
        
        ok = self.dao.supprimer_par_mail(mail)
        if ok:
            return True, "Personnel supprimé."
        return False, "Aucun personnel supprimé (mail introuvable)."

    def rechercher(self, critere):
        return self.dao.rechercher(critere)

    def lister_tout(self):
        return self.dao.lister_tout()

    def nombre_total(self):
        return self.dao.nombre_total()

    def obtenir_par_code(self, code):
        return self.dao.obtenir_par_code(code)

    def obtenir_par_mail(self, mail):
        personnels = self.dao.rechercher(mail)
        mail_normalise = (mail or "").strip().lower()
        for personnel in personnels:
            if (personnel.get_mail() or "").strip().lower() == mail_normalise:
                return personnel
        return None

    def get_responsable(self, fonction: str) -> dict | None:
        """
        Retourne le nom et mail du responsable d'une fonction.
        Utilisé par Vault pour envoyer le code OTP par email.
        """
        return self.dao.get_responsable(fonction)
    
    def compter_par_fonction(self) -> dict:
        """
        Compte le nombre de personnels par fonction.
        Retourne un dictionnaire {fonction: nombre}
        """
        return self.dao.compter_par_fonction()
    
    # =========================================================================
    # GESTION VAULT - CLÉS TOTP
    # =========================================================================
    
    def _creer_cle_vault_personnel(self, code: str, data: dict) -> bool:
        """
        Crée une clé TOTP Vault pour un personnel.
        
        Args:
            code: Code du personnel (ex: P0001)
            data: Données du personnel (nom, prenom)
        
        Returns:
            True si créé, False sinon
        """
        try:
            if not self.vault.est_connecte():
                print(f"[Vault] Service non connecté, clé TOTP non créée pour {code}")
                return False
            
            nom_complet = f"{data.get('prenom', '')} {data.get('nom', '')}".strip()
            account_name = nom_complet or code
            
            if self.vault.creer_cle_totp(code, account_name=account_name):
                print(f"[Vault] Clé TOTP créée pour le personnel {code} ({account_name})")
                return True
            else:
                print(f"[Vault] Échec création clé TOTP pour {code}")
                return False
                
        except Exception as e:
            print(f"[Vault] Erreur création clé TOTP pour {code}: {e}")
            return False
    
    def _supprimer_cle_vault_personnel(self, code: str) -> bool:
        """
        Supprime la clé TOTP Vault d'un personnel.
        
        Args:
            code: Code du personnel (ex: P0001)
        
        Returns:
            True si supprimé, False sinon
        """
        try:
            if not self.vault.est_connecte():
                print(f"[Vault] Service non connecté, clé TOTP non supprimée pour {code}")
                return False
            
            if self.vault.supprimer_cle_totp(code):
                print(f"[Vault] Clé TOTP supprimée pour le personnel {code}")
                return True
            else:
                print(f"[Vault] Échec suppression clé TOTP pour {code}")
                return False
                
        except Exception as e:
            print(f"[Vault] Erreur suppression clé TOTP pour {code}: {e}")
            return False

    def get_personnel_stats(self):
        personnels = self.dao.lister_tout()
        total = len(personnels)
        avec_photo = sum(1 for p in personnels if p.get_photo_path())
        sans_photo = total - avec_photo
        return {
            "total": total,
            "avec_photo": avec_photo,
            "sans_photo": sans_photo,
        }

    def get_cabinet_info(self):
        info = self.cabinet_dao.get_info_cabinet() or {}

        nom_cabinet = info.get("nom_cabinet", "Cabinet Ophtalmologique")
        adresse = info.get("adresse", "")
        logo = info.get("logo")

        final_logo = None
        if logo:
            script = os.path.dirname(__file__)
            path = os.path.normpath(os.path.join(script, "..", "connexion", "image", logo))
            if os.path.exists(path):
                final_logo = path

        return {
            "nom_cabinet": nom_cabinet,
            "adresse_cabinet": adresse,
            "logo_url": final_logo,
        }

    def _get_personnel_for_printing_data(self):
        info = self.cabinet_dao.get_info_cabinet() or {}
        nom_cabinet = info.get("nom_cabinet", "Cabinet Ophtalmologique")
        adresse = info.get("adresse", "")
        logo = info.get("logo")

        final_logo = None
        if logo:
            script = os.path.dirname(__file__)
            path = os.path.normpath(os.path.join(script, "..", "connexion", "image", logo))
            if os.path.exists(path):
                final_logo = path

        entete = {
            "nom_cabinet": nom_cabinet,
            "adresse_cabinet": adresse,
            "logo_url": final_logo,
            "titre": "Liste Complète du Personnel",
            "date_heure": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        personnels = self._modeles_vers_dicts(self.dao.lister_tout())
        return entete, personnels

    def generer_liste_pdf(self, chemin_fichier):
        from services.pdf_rapports.rapport_personnel import RapportPersonnelPDF
        try:
            liste_personnels = self._modeles_vers_dicts(self.dao.lister_tout())
            if not liste_personnels:
                return False, "Aucun personnel à imprimer."
            info_cabinet = self.get_cabinet_info()
            RapportPersonnelPDF.generer_pdf_liste_personnels(liste_personnels, info_cabinet, chemin_fichier)
            return True, f"Rapport généré : {chemin_fichier}"
        except Exception as e:
            return False, f"Erreur génération PDF : {e}"

    def export_to_csv(self, chemin_fichier):
        try:
            data = self._modeles_vers_dicts(self.dao.lister_tout())
            if not data:
                return False, "Aucun personnel à exporter."
            pd.DataFrame(data).to_csv(chemin_fichier, index=False)
            return True, f"Export CSV réalisé: {chemin_fichier}"
        except Exception as e:
            return False, f"Erreur export CSV: {e}"

    def import_from_csv(self, chemin_fichier, action_si_existant="skip"):
        try:
            df = pd.read_csv(chemin_fichier)
            if df.empty:
                return False, "Fichier CSV vide."
            count = 0
            for _, row in df.iterrows():
                data = {
                    "nom": str(row.get("nom", "")).strip(),
                    "prenom": str(row.get("prenom", "")).strip(),
                    "adresse": str(row.get("adresse", "")).strip(),
                    "date_naissance": str(row.get("date_naissance", "")).strip(),
                    "contact": str(row.get("contact", "")).strip(),
                    "mail": str(row.get("mail", "")).strip(),
                    "fonction": str(row.get("fonction", "")).strip(),
                    "photo_path": row.get("photo_path"),
                }
                valid, _ = self.valider_champs(data)
                if not valid:
                    continue
                if data.get("photo_path") and pd.notna(data.get("photo_path")):
                    photo_nom, _ = self._copier_photo_et_retourner_nom(data["photo_path"])
                    data["photo_path"] = photo_nom if photo_nom else None

                code = row.get("code")
                code = str(code).strip() if pd.notna(code) else None
                if code and self.dao.obtenir_par_code(code):
                    if action_si_existant == "update":
                        ok, _ = self.modifier_personnel(code, data)
                        if ok:
                            count += 1
                    continue

                ok, _ = self.ajouter_personnel(data)
                if ok:
                    count += 1
            return True, f"Import CSV terminé. {count} enregistrements importés."
        except Exception as e:
            return False, f"Erreur import CSV: {e}"

    def export_to_excel(self, chemin_fichier):
        try:
            data = self._modeles_vers_dicts(self.dao.lister_tout())
            if not data:
                return False, "Aucun personnel à exporter."
            pd.DataFrame(data).to_excel(chemin_fichier, index=False)
            return True, f"Export Excel réalisé: {chemin_fichier}"
        except Exception as e:
            return False, f"Erreur export Excel: {e}"

    def import_from_excel(self, chemin_fichier, action_si_existant="skip"):
        try:
            df = pd.read_excel(chemin_fichier)
            if df.empty:
                return False, "Fichier Excel vide."
            count = 0
            for _, row in df.iterrows():
                data = {
                    "nom": str(row.get("nom", "")).strip(),
                    "prenom": str(row.get("prenom", "")).strip(),
                    "adresse": str(row.get("adresse", "")).strip(),
                    "date_naissance": str(row.get("date_naissance", "")).strip(),
                    "contact": str(row.get("contact", "")).strip(),
                    "mail": str(row.get("mail", "")).strip(),
                    "fonction": str(row.get("fonction", "")).strip(),
                    "photo_path": row.get("photo_path"),
                }
                valid, _ = self.valider_champs(data)
                if not valid:
                    continue
                if data.get("photo_path") and pd.notna(data.get("photo_path")):
                    photo_nom, _ = self._copier_photo_et_retourner_nom(data["photo_path"])
                    data["photo_path"] = photo_nom if photo_nom else None

                code = row.get("code")
                code = str(code).strip() if pd.notna(code) else None
                if code and self.dao.obtenir_par_code(code):
                    if action_si_existant == "update":
                        ok, _ = self.modifier_personnel(code, data)
                        if ok:
                            count += 1
                    continue

                ok, _ = self.ajouter_personnel(data)
                if ok:
                    count += 1
            return True, f"Import Excel terminé. {count} enregistrements importés."
        except Exception as e:
            return False, f"Erreur import Excel: {e}"
