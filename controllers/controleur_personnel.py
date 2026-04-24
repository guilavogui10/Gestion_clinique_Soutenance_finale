# fichier: personnel/controller_personnel.py

from service_metier.personnel_service import PersonnelService


class ControllerPersonnel:
    def __init__(self):
        self.service = PersonnelService()
        self.dao = self.service.dao

    def _modele_vers_dict(self, personnel):
        return self.service._modele_vers_dict(personnel)

    def _modeles_vers_dicts(self, personnels):
        return self.service._modeles_vers_dicts(personnels)

    def _valider_nom_prenom_fonction(self, valeur):
        return self.service._valider_nom_prenom_fonction(valeur)

    def _valider_email(self, mail):
        return self.service._valider_email(mail)

    def _valider_adresse(self, adresse):
        return self.service._valider_adresse(adresse)

    def _valider_contact(self, contact):
        return self.service._valider_contact(contact)

    def _valider_date(self, date_str):
        return self.service._valider_date(date_str)

    def valider_champs(self, data):
        return self.service.valider_champs(data)

    def ajouter_personnel(self, data):
        return self.service.ajouter_personnel(data)

    def modifier_personnel(self, code, data):
        return self.service.modifier_personnel(code, data)

    def supprimer_par_mail(self, mail):
        return self.service.supprimer_par_mail(mail)

    def rechercher(self, critere):
        return self._modeles_vers_dicts(self.service.rechercher(critere))

    def lister_tout(self):
        return self._modeles_vers_dicts(self.service.lister_tout())

    def nombre_total(self):
        return self.service.nombre_total()

    def obtenir_par_code(self, code):
        return self._modele_vers_dict(self.service.obtenir_par_code(code))

    def obtenir_par_mail(self, mail):
        return self._modele_vers_dict(self.service.obtenir_par_mail(mail))

    def get_all_personnels(self):
        return self.lister_tout()

    def get_personnel_stats(self):
        return self.service.get_personnel_stats()

    def get_cabinet_info(self):
        return self.service.get_cabinet_info()

    def generer_liste_pdf(self, chemin_fichier):
        return self.service.generer_liste_pdf(chemin_fichier)

    def generer_carte_membre_pdf(self, code_personnel, chemin_fichier, couleur_hex="#2E86C1"):
        return self.service.generer_carte_membre_pdf(code_personnel, chemin_fichier, couleur_hex)

    def export_to_csv(self, chemin_fichier):
        return self.service.export_to_csv(chemin_fichier)

    def import_from_csv(self, chemin_fichier, action_si_existant="skip"):
        return self.service.import_from_csv(chemin_fichier, action_si_existant)

    def export_to_excel(self, chemin_fichier):
        return self.service.export_to_excel(chemin_fichier)

    def import_from_excel(self, chemin_fichier, action_si_existant="skip"):
        return self.service.import_from_excel(chemin_fichier, action_si_existant)

    def delete_personnel(self, mail):
        return self.supprimer_par_mail(mail)
