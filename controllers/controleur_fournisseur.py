import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service_metier.fournisseur_service import FournisseurService


class FournisseurControleur:
    """
    Contrôleur MVC pour la gestion des fournisseurs.
    Délègue toute la logique métier à FournisseurService.
    """

    def __init__(self):
        self.service = FournisseurService()
        self.logger  = logging.getLogger(__name__)

    # --------- LISTE / RECHERCHE ---------
    def lister_fournisseurs(self, code_session: str = None) -> list:
        return self.service.lister_fournisseurs(code_session)

    def obtenir_par_code(self, code_fournisseur: str):
        return self.service.obtenir_par_code(code_fournisseur)

    def get_all_fournisseurs(self):
        return self.service.get_all_fournisseurs()

    def get_fournisseur_by_mail(self, mail):
        return self.service.get_fournisseur_by_mail(mail)

    def search_fournisseurs(self, critere=None, valeur=None):
        return self.service.search_fournisseurs(critere, valeur)

    # --------- CRUD ---------
    def add_new_fournisseur(self, donnees):
        return self.service.add_new_fournisseur(donnees)

    def update_fournisseur(self, donnees):
        return self.service.update_fournisseur(donnees)

    def delete_fournisseur(self, mail):
        return self.service.delete_fournisseur(mail)

    # --------- STATISTIQUES ---------
    def get_fournisseur_stats(self, code_session: str = None):
        return self.service.get_fournisseur_stats(code_session)

    def get_fournisseurs_actifs(self, code_session: str = None):
        return self.service.get_fournisseurs_actifs(code_session)

    def get_stats_fournisseur_detail(self, mail_fournisseur, code_session: str = None):
        return self.service.get_stats_fournisseur_detail(mail_fournisseur, code_session)

    def get_fournissseur_recent(self, code_session: str = None):
        return self.service.get_fournissseur_recent(code_session)

    # --------- EXPORT / IMPORT ---------
    def exporter_fournisseurs_to_excel(self, fichier):
        return self.service.exporter_fournisseurs_to_excel(fichier)

    def exporter_fournisseurs_to_csv(self, fichier):
        return self.service.exporter_fournisseurs_to_csv(fichier)

    def importer_fournisseurs_from_csv(self, fichier):
        return self.service.importer_fournisseurs_from_csv(fichier)

    def importer_fournisseurs_from_excel(self, fichier):
        return self.service.importer_fournisseurs_from_excel(fichier)

    # --------- APERÇU EXPORT (compatibilité ApercuActeModal) ---------
    def obtenir_donnees_export(self) -> list:
        """Retourne les fournisseurs sous forme de liste de dicts pour l'aperçu."""
        fournisseurs = self.service.get_all_fournisseurs()
        return [
            {
                'email_fournisseur': str(f.get('email_fournisseur', '')),
                'nom_entreprise':    str(f.get('nom_entreprise',    '')),
                'telephone':         str(f.get('telephone',         '')),
                'adresse':           str(f.get('adresse',           '')),
            }
            for f in (fournisseurs or [])
        ]

    def export_to_excel(self, chemin: str):
        """Alias utilisé par le pattern ApercuActeModal."""
        return self.service.exporter_fournisseurs_to_excel(chemin)

    def export_to_csv(self, chemin: str):
        """Alias utilisé par le pattern ApercuActeModal."""
        return self.service.exporter_fournisseurs_to_csv(chemin)

    # --------- CABINET / PDF ---------
    def get_cabinet_info(self):
        return self.service.get_cabinet_info()

    def generer_liste_pdf(self, chemin_fichier):
        return self.service.generer_liste_pdf(chemin_fichier)

    def generer_rapport_fournisseurs(self):
        """Retourne le chemin du PDF temporaire pour ApercuPDFDialog."""
        return self.service.generer_rapport_fournisseurs()

    def generer_rapport_activites_un_fournisseur(self, email_fournisseur, code_session=None):
        return self.service.generer_rapport_activites_un_fournisseur(email_fournisseur, code_session)

    def generer_rapport_toutes_activites_fournisseurs(self, code_session=None):
        return self.service.generer_rapport_toutes_activites_fournisseurs(code_session)

