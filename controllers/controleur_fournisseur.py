import sys
import os
import re
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.dao_fournisseur import FournisseurDAO
from models.modele_fournisseur import Fournisseur
from parametre.dao_param import CabinetDAO
from services.fournisseur_pdf_service import FournisseurPDFService


class FournisseurControleur:
    """
    Controleur pour la gestion des fournisseurs.
    Fait le lien entre la vue et le DAO.
    """

    def __init__(self):
        self.dao = FournisseurDAO()
        self.fournisseur_dao = self.dao
        self.cabinet_dao = CabinetDAO()
        self.Fournisseur = Fournisseur

    # ----------------- COMPAT : LISTE -----------------
    def lister_fournisseurs(self, code_session: str) -> list:
        """
        Retourne la liste des fournisseurs pour remplir les ComboBox.
        Note : les fournisseurs sont globaux (pas de code_session).
        """
        print(f"[FournisseurControleur] lister_fournisseurs appele avec session={code_session}")
        result = self.dao.lister_fournisseurs(code_session)
        print(f"[FournisseurControleur] Resultat: {len(result)} fournisseurs")
        return result

    def obtenir_par_code(self, code_fournisseur: str):
        """Retourne un fournisseur par son code."""
        return self.dao.obtenir_par_code(code_fournisseur)

    # ----------------- VALIDATIONS -----------------
    def _valider_nom(self, nom):
        if len(nom) < 3:
            return False, "Le nom doit contenir au moins 3 caracteres."
        if re.match(r"^[a-zA-Z0-9\\s'-]+$", nom) is None:
            return False, "Le nom contient des caracteres speciaux non autorises."
        return True, ""

    def _valider_adresse(self, adresse):
        if len(adresse) < 3:
            return False, "L'adresse doit contenir au moins 3 caracteres."
        if re.match(r"^[a-zA-Z0-9\\s'-]+$", adresse) is None:
            return False, "L'adresse contient des caracteres speciaux non autorises."
        return True, ""

    def _valider_mail(self, mail):
        if mail != mail.lower():
            return False, "L'email doit etre en minuscules."
        if re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,4}$", mail) is None:
            return False, "Format d'email invalide."
        return True, ""

    def _valider_telephone(self, telephone):
        telephone = str(telephone).strip()
        if len(telephone) != 9:
            return False, "Le numero doit contenir exactement 9 chiffres."
        if not telephone.isdigit():
            return False, "Le numero ne doit contenir que des chiffres."
        return True, ""

    # ----------------- CRUD : AJOUT -----------------
    def add_new_fournisseur(self, donnees):
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

    # ----------------- CRUD : LECTURE -----------------
    def get_all_fournisseurs(self):
        return self.fournisseur_dao.lister_fournisseurs()

    def get_fournisseur_by_mail(self, mail):
        return self.fournisseur_dao.get_fournisseur_by_mail(mail)

    def search_fournisseurs(self, critere=None, valeur=None):
        """
        Recherche flexible :
        - critere = 'mail'
        - critere = 'telephone'
        - sinon recherche large dans email + telephone (DAO.search_fournisseur)
        """
        if critere == 'mail':
            res = self.fournisseur_dao.get_fournisseur_by_mail(valeur)
            return [res] if res else []

        if critere == 'telephone':
            return self.fournisseur_dao.search_fournisseur(valeur)

        if not valeur:
            return self.get_all_fournisseurs()

        return self.fournisseur_dao.search_fournisseur(valeur)

    # ----------------- CRUD : UPDATE / DELETE -----------------
    def update_fournisseur(self, donnees):
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
        if not mail:
            return False, "Email requis."
        return self.fournisseur_dao.delete_fournisseur(mail)

    # ----------------- STATS -----------------
    def get_fournisseur_stats(self, code_session: str = None):
        return self.fournisseur_dao.get_fournisseur_stats(code_session)

    def get_fournisseurs_actifs(self, code_session: str = None):
        return self.fournisseur_dao.get_fournisseurs_actifs(code_session)

    def get_stats_fournisseur_detail(self, mail_fournisseur, code_session: str = None):
        return self.fournisseur_dao.get_stats_fournisseur_detail(mail_fournisseur, code_session)

    def get_fournissseur_recent(self, code_session: str = None):
        return self.fournisseur_dao.get_fournisseurs_recents(code_session)

    # ----------------- EXPORTATIONS -----------------
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

    def get_cabinet_info(self):
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

    # ----------------- PDF -----------------
    def generer_liste_pdf(self, chemin_fichier):
        try:
            fournisseurs = self.fournisseur_dao.lister_fournisseurs()

            return FournisseurPDFService.generer_liste_pdf(
                controller=self,
                chemin_fichier=chemin_fichier,
                fournisseurs=fournisseurs
            )

        except Exception as e:
            return False, f"Erreur PDF : {e}"
