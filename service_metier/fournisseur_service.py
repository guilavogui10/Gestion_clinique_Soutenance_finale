"""
fournisseur_service.py
-----------------------
Service métier — Gestion des fournisseurs.

Responsabilités :
  - Validation des données fournisseur (nom, adresse, mail, téléphone)
  - CRUD : ajout, mise à jour, suppression, lecture
  - Recherche flexible (par mail, téléphone, critère libre)
  - Statistiques fournisseurs
  - Export / Import (Excel, CSV)
  - Génération PDF
  - Informations cabinet
"""

import os
import re
import logging
import pandas as pd

from data.dao_fournisseur import FournisseurDAO
from models.modele_fournisseur import Fournisseur
from parametre.dao_param import CabinetDAO
from services.fournisseur_pdf_service import FournisseurPDFService


class FournisseurService:
    """
    Service métier pour la gestion des fournisseurs.
    Contient la validation, le CRUD, les recherches, les exports et la génération PDF.
    """

    def __init__(self, dao=None, cabinet_dao=None):
        self.dao = dao or FournisseurDAO()
        self.fournisseur_dao = self.dao
        self.cabinet_dao = cabinet_dao or CabinetDAO()
        self.Fournisseur = Fournisseur
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # MÉTHODES DE VALIDATION (LOGIQUE MÉTIER)
    # =========================================================================

    def _valider_nom(self, nom):
        """Valide le nom de l'entreprise (min 3 caractères)."""
        if len(nom) < 3:
            return False, "Le nom doit contenir au moins 3 caracteres."
        if re.match(r"^[a-zA-Z0-9\\s'-]+$", nom) is None:
            return False, "Le nom contient des caracteres speciaux non autorises."
        return True, ""

    def _valider_adresse(self, adresse):
        """Valide l'adresse du fournisseur (min 3 caractères)."""
        if len(adresse) < 3:
            return False, "L'adresse doit contenir au moins 3 caracteres."
        if re.match(r"^[a-zA-Z0-9\\s'-]+$", adresse) is None:
            return False, "L'adresse contient des caracteres speciaux non autorises."
        return True, ""

    def _valider_mail(self, mail):
        """Valide le format de l'email (minuscules, format valide)."""
        if mail != mail.lower():
            return False, "L'email doit etre en minuscules."
        if re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,4}$", mail) is None:
            return False, "Format d'email invalide."
        return True, ""

    def _valider_telephone(self, telephone):
        """Valide le numéro de téléphone (exactement 9 chiffres)."""
        telephone = str(telephone).strip()
        if len(telephone) != 9:
            return False, "Le numero doit contenir exactement 9 chiffres."
        if not telephone.isdigit():
            return False, "Le numero ne doit contenir que des chiffres."
        return True, ""

    # =========================================================================
    # MÉTHODES CRUD
    # =========================================================================

    def add_new_fournisseur(self, donnees):
        """
        Valide et ajoute un nouveau fournisseur.

        Args:
            donnees (dict): Données du fournisseur.

        Returns:
            tuple: (succès, message)
        """
        mail = donnees.get('email_fournisseur', '').strip()
        nom = donnees.get('nom_entreprise', '').strip()
        telephone = donnees.get('telephone', '').strip()
        adresse = donnees.get('adresse', '').strip()

        val_mail, msg = self._valider_mail(mail)
        if not val_mail:
            return False, f"Erreur Mail : {msg}"

        val_nom, msg = self._valider_nom(nom)
        if not val_nom:
            return False, f"Erreur Nom : {msg}"

        val_tel, msg = self._valider_telephone(telephone)
        if not val_tel:
            return False, f"Erreur Telephone : {msg}"

        if self.fournisseur_dao.get_fournisseur_by_mail(mail):
            return False, f"Le fournisseur {mail} existe deja."

        val_adresse, msg = self._valider_adresse(adresse)
        if not val_adresse:
            return False, f"Erreur Adresse : {msg}"

        try:
            obj = self.Fournisseur(mail, nom, telephone, adresse)
            return self.fournisseur_dao.add_fournisseur(obj)
        except Exception as e:
            return False, f"Erreur interne : {e}"

    def update_fournisseur(self, donnees):
        """Valide et met à jour un fournisseur existant."""
        mail = donnees.get('email_fournisseur', '').strip()
        if not mail:
            return False, "Email requis pour la mise a jour."

        actuel = self.fournisseur_dao.get_fournisseur_by_mail(mail)
        if not actuel:
            return False, f"Aucun fournisseur trouve avec {mail}"

        nom = donnees.get('nom_entreprise', actuel.get('nom_entreprise', ''))
        telephone = donnees.get('telephone', actuel.get('telephone', ''))
        adresse = donnees.get('adresse', actuel.get('adresse', ''))

        val_nom, msg = self._valider_nom(nom)
        if not val_nom:
            return False, f"Erreur Nom : {msg}"

        val_tel, msg = self._valider_telephone(telephone)
        if not val_tel:
            return False, f"Erreur Telephone : {msg}"

        fournisseur_mod = self.Fournisseur(mail, nom, telephone, adresse)
        return self.fournisseur_dao.update_fournisseur(fournisseur_mod)

    def delete_fournisseur(self, mail):
        """Supprime un fournisseur par son email."""
        if not mail:
            return False, "Email requis."
        return self.fournisseur_dao.delete_fournisseur(mail)

    # =========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # =========================================================================

    def lister_fournisseurs(self, code_session: str = None) -> list:
        """Retourne la liste des fournisseurs."""
        return self.dao.lister_fournisseurs(code_session)

    def obtenir_par_code(self, code_fournisseur: str):
        """Retourne un fournisseur par son code."""
        return self.dao.obtenir_par_code(code_fournisseur)

    def get_all_fournisseurs(self):
        """Retourne tous les fournisseurs."""
        return self.fournisseur_dao.lister_fournisseurs()

    def get_fournisseur_by_mail(self, mail):
        """Retourne un fournisseur par son email."""
        return self.fournisseur_dao.get_fournisseur_by_mail(mail)

    def search_fournisseurs(self, critere=None, valeur=None):
        """
        Recherche flexible de fournisseurs.
        Par mail, téléphone, ou critère libre.
        """
        if critere == 'mail':
            res = self.fournisseur_dao.get_fournisseur_by_mail(valeur)
            return [res] if res else []
        if critere == 'telephone':
            return self.fournisseur_dao.search_fournisseur(valeur)
        if not valeur:
            return self.get_all_fournisseurs()
        return self.fournisseur_dao.search_fournisseur(valeur)

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def get_fournisseur_stats(self, code_session: str = None):
        return self.fournisseur_dao.get_fournisseur_stats(code_session)

    def get_fournisseurs_actifs(self, code_session: str = None):
        return self.fournisseur_dao.get_fournisseurs_actifs(code_session)

    def get_stats_fournisseur_detail(self, mail_fournisseur, code_session: str = None):
        return self.fournisseur_dao.get_stats_fournisseur_detail(mail_fournisseur, code_session)

    def get_fournissseur_recent(self, code_session: str = None):
        return self.fournisseur_dao.get_fournisseurs_recents(code_session)

    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================

    def exporter_fournisseurs_to_excel(self, fichier):
        try:
            data = self.fournisseur_dao.lister_fournisseurs()
            if not data:
                return False, "Aucun fournisseur a exporter."
            pd.DataFrame(data).to_excel(fichier, index=False)
            return True, f"Exportation reussie -> {fichier}"
        except Exception as e:
            return False, f"Erreur export Excel : {e}"

    def exporter_fournisseurs_to_csv(self, fichier):
        try:
            data = self.fournisseur_dao.lister_fournisseurs()
            if not data:
                return False, "Aucun fournisseur a exporter."
            pd.DataFrame(data).to_csv(fichier, index=False)
            return True, f"Exportation reussie -> {fichier}"
        except Exception as e:
            return False, f"Erreur export CSV : {e}"

    def importer_fournisseurs_from_csv(self, fichier):
        try:
            df = pd.read_csv(fichier).rename(columns={'mail': 'email_fournisseur'})
            total = 0
            for d in df.to_dict('records'):
                ok, _ = self.add_new_fournisseur(d)
                if ok:
                    total += 1
            return True, f"{total} fournisseurs importes."
        except FileNotFoundError:
            return False, "Fichier CSV introuvable."
        except Exception as e:
            return False, f"Erreur import CSV : {e}"

    def importer_fournisseurs_from_excel(self, fichier):
        try:
            df = pd.read_excel(fichier).rename(columns={'mail': 'email_fournisseur'})
            total = 0
            for d in df.to_dict('records'):
                ok, _ = self.add_new_fournisseur(d)
                if ok:
                    total += 1
            return True, f"{total} fournisseurs importes."
        except FileNotFoundError:
            return False, "Fichier Excel introuvable."
        except Exception as e:
            return False, f"Erreur import Excel : {e}"

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self):
        """Récupère les informations du cabinet."""
        info = self.cabinet_dao.get_info_cabinet() or {}
        nom_cabinet = info.get("nom_cabinet", "Cabinet Ophtalmologique")
        adresse = info.get("adresse", "")
        logo = info.get("logo", None)
        final_logo = None
        if logo:
            script = os.path.dirname(__file__)
            path = os.path.join(script, "..", "connexion", "image", logo)
            if os.path.exists(path):
                final_logo = path
        return {
            "nom_cabinet": nom_cabinet,
            "adresse_cabinet": adresse,
            "logo_url": final_logo
        }

    # =========================================================================
    # GÉNÉRATION PDF
    # =========================================================================

    def generer_liste_pdf(self, chemin_fichier):
        """Génère la liste PDF des fournisseurs."""
        try:
            fournisseurs = self.fournisseur_dao.lister_fournisseurs()
            return FournisseurPDFService.generer_liste_pdf(
                controller=self,
                chemin_fichier=chemin_fichier,
                fournisseurs=fournisseurs
            )
        except Exception as e:
            return False, f"Erreur PDF : {e}"
