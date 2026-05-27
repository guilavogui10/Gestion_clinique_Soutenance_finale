"""
patient_service.py
-------------------
Service métier — Gestion des patients.

Responsabilités :
  - Validation des données patient (nom, prénom, téléphone, date, genre, etc.)
  - Contrôle d'unicité (doublon téléphone)
  - CRUD : ajout, mise à jour, lecture, recherche, statistiques
  - Export / Import (Excel, CSV)
  - Génération PDF (carnet patient, liste par genre, liste complète)
  - Informations cabinet

Pattern :
  Le contrôleur instancie ce service et lui délègue TOUTE la logique métier.
  Le service interagit avec le DAO et le modèle Patient.
"""

import re
import os
import pandas as pd
from datetime import datetime

from data.dao_patient import PatientDao
from models.model_patient import Patient
from parametre.dao_param import CabinetDAO
from services.pdf_patient.patient_pdf import PatientPDFService


class PatientService:
    """
    Service métier pour la gestion des patients.
    Contient la validation, le CRUD, les exports/imports et la génération PDF.
    """

    def __init__(self, dao=None, cabinet_dao=None):
        """
        Initialise le service avec injection optionnelle des DAOs.

        Args:
            dao: Instance de PatientDao (injection pour tests).
            cabinet_dao: Instance de CabinetDAO (injection pour tests).
        """
        self.dao = dao or PatientDao()
        self.cabinet_dao = cabinet_dao or CabinetDAO()
        self.patient_classe = Patient

    # =========================================================================
    # MÉTHODES DE VALIDATION (LOGIQUE MÉTIER)
    # =========================================================================

    def _valider_nom(self, nom):
        """Valide le nom du patient (min 3 caractères, pas de caractères spéciaux)."""
        if len(nom) < 3:
            return False, "le nom doit contenir au moins trois lettres !"
        if re.match(r"^[a-zA-Z0-9\s'-]+$", nom) is None:
            return False, "le Le nom contient des caractères spéciaux non autorisés."
        return True, ""

    def _valider_prenom(self, prenom):
        """Valide le prénom du patient (min 3 caractères, pas de caractères spéciaux)."""
        if len(prenom) < 3:
            return False, "le nom doit contenir au moins trois lettres !"
        if re.match(r"^[a-zA-Z0-9\s'-]+$", prenom) is None:
            return False, "le nom contient des caractères spéciaux non autorisés. !"
        return True, ""

    def _valider_telephone(self, telephone):
        """Valide le téléphone (exactement 9 chiffres)."""
        telephone = str(telephone).strip()
        if len(telephone) != 9:
            return False, "le telephone doit contenir exactement neuf chiffres !"
        if not telephone.isdigit():
            return False, "le numero de telephone doit contenir seulement que des chiffres !"
        return True, ""

    def _valider_date(self, naissance):
        """Valide la date de naissance (formats acceptés : YYYY-MM-DD, DD/MM/YYYY)."""
        if isinstance(naissance, datetime):
            return True, ""
        if pd.notna(naissance) and isinstance(naissance, float):
            naissance = str(pd.to_datetime(naissance).date())
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                datetime.strptime(str(naissance), fmt)
                return True, ""
            except Exception:
                continue
        return False, "Date invalide. Format attendu: YYYY-MM-DD ou DD/MM/YYYY."

    def _valider_genre(self, genre):
        """Valide le genre du patient (min 3 caractères)."""
        if len(genre) < 3:
            return False, "le genre doit contenir au moins trois lettres !"
        if re.match(r"^[a-zA-Z0-9\s'-]+$", genre) is None:
            return False, "le genre contient des caracteres spéciaux non autorisés !"
        return True, ""

    def _valider_profession(self, profession):
        """Valide la profession du patient (min 3 caractères)."""
        if len(profession) < 3:
            return False, "la profession doit contenir au moins trois lettres !"
        if re.match(r"^[a-zA-Z0-9\s'-]+$", profession) is None:
            return False, "la profession contient des caracteres speciaux non autorisé !"
        return True, ""

    def _valider_adresse(self, adresse):
        """Valide l'adresse du patient (min 3 caractères)."""
        if len(adresse) < 3:
            return False, "l'adresse doit contenir au moins trois lettres !"
        if re.match(r"^[a-zA-Z0-9\s'-]+$", adresse) is None:
            return False, "l'adresse contient des caracteres spéciaux non autorisés !"
        return True, ""

    def _control_exist(self, telephone):
        """
        Vérifie dans la base de données si un patient utilise déjà ce numéro.
        Retourne (False, message) si le patient existe, (True, "") sinon.
        """
        result = self.dao.reed_by_critere_patient(telephone)
        if len(result) > 0:
            return False, "Ce patient est déjà enregistré !"
        return True, ""

    def _valider_patient_complet(self, patient_objet):
        """
        Applique toutes les validations sur un objet Patient.
        Retourne (True, "") si tout est valide, (False, message) sinon.
        """
        valid, msg = self._valider_nom(patient_objet.get_nom())
        if not valid:
            return False, msg

        valid, msg = self._valider_prenom(patient_objet.get_prenom())
        if not valid:
            return False, msg

        valid, msg = self._valider_telephone(patient_objet.get_telephone())
        if not valid:
            return False, msg

        valid, msg = self._valider_date(patient_objet.get_naissance())
        if not valid:
            return False, msg

        valid, msg = self._valider_genre(patient_objet.get_genre())
        if not valid:
            return False, msg

        valid, msg = self._valider_profession(patient_objet.get_profession())
        if not valid:
            return False, msg

        valid, msg = self._valider_adresse(patient_objet.get_adresse())
        if not valid:
            return False, msg

        return True, ""

    # =========================================================================
    # MÉTHODES CRUD
    # =========================================================================

    def save_patient(self, patient_objet):
        """
        Valide et enregistre un nouveau patient.
        Génère automatiquement le code_patient via le DAO.

        Args:
            patient_objet (Patient): Objet Patient à enregistrer.

        Returns:
            tuple: (succès, message)
        """
        # 1. Validation complète
        valid, msg = self._valider_patient_complet(patient_objet)
        if not valid:
            return False, msg

        # 2. Contrôle d'existence (doublon téléphone)
        existe_deja, msg_exist = self._control_exist(patient_objet.get_telephone())
        if not existe_deja:
            return False, msg_exist

        # 3. Génération du code automatique
        nouveau_code = self.dao.generate_code_patient()
        patient_objet.set_code_patient(nouveau_code)

        # 4. Envoi au DAO
        return self.dao.createPatient(patient_objet)

    def update_patient(self, patient_update):
        """
        Valide et met à jour un patient existant.
        Vérifie que le téléphone n'est pas utilisé par un autre patient.

        Args:
            patient_update (Patient): Objet Patient avec les modifications.

        Returns:
            tuple: (succès, message)
        """
        # 1. Validation complète
        valid, msg = self._valider_patient_complet(patient_update)
        if not valid:
            return False, msg

        # 2. Contrôle d'unicité du téléphone (sauf si inchangé)
        telephone_patient_en_base = self.dao.reed_by_code_patient(
            patient_update.get_code_patient()
        )
        if telephone_patient_en_base:
            if patient_update.get_telephone() != telephone_patient_en_base.get_telephone():
                exist_deja, message_exist = self._control_exist(patient_update.get_telephone())
                if not exist_deja:
                    return False, "Ce telephone existe déja pour un autre patient"

        # 3. Envoi au DAO
        return self.dao.updatePatient(patient_update)

    # =========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # =========================================================================

    def reed_Allpatient(self):
        """Retourne la liste de tous les patients (objets Patient)."""
        return self.dao.reedAllPatient()

    def reed_by_code_patient(self, code_patient):
        """Recherche un patient par son code."""
        if not code_patient.strip():
            return self.dao.reedAllPatient()
        return self.dao.reed_by_code_patient(code_patient)

    def reed_by_sexe_patient(self, sexe):
        """Filtre les patients par genre/sexe."""
        if not sexe.strip():
            return self.dao.reedAllPatient()
        return self.dao.reed_by_genre_patient(sexe)

    def reed_by_critere_patient(self, critere):
        """Recherche par critère (date, téléphone, etc.)."""
        if not critere.strip():
            return self.dao.reedAllPatient()
        return self.dao.reed_by_critere_patient(critere)

    # =========================================================================
    # STATISTIQUES
    # =========================================================================

    def statistique(self):
        """Retourne les statistiques globales des patients."""
        return self.dao.stat_patients()

    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================

    def export_to_excel(self, fichier):
        """
        Exporte tous les patients vers un fichier Excel.

        Args:
            fichier (str): Chemin du fichier de destination.

        Returns:
            tuple: (succès, message)
        """
        try:
            liste_objets = self.dao.reedAllPatient()
            if not liste_objets:
                return False, "Aucune donnée à exporter"

            donnees_propres = []
            for p in liste_objets:
                donnees_propres.append({
                    "Code": p.get_code_patient(),
                    "Nom": p.get_nom(),
                    "Prénom": p.get_prenom(),
                    "Téléphone": p.get_telephone(),
                    "Date de Naissance": p.get_naissance(),
                    "Genre": p.get_genre(),
                    "Profession": p.get_profession(),
                    "Adresse": p.get_adresse()
                })

            df = pd.DataFrame(donnees_propres)
            df.to_excel(fichier, index=False)
            return True, f"L'exportation vers {os.path.basename(fichier)} a réussi !"
        except Exception as e:
            return False, f"Erreur lors de l'exportation : {str(e)}"

    def export_to_csv(self, fichier):
        """
        Exporte tous les patients vers un fichier CSV.

        Args:
            fichier (str): Chemin du fichier de destination.

        Returns:
            tuple: (succès, message)
        """
        try:
            liste_patient = self.dao.reedAllPatient()
            if not liste_patient:
                return False, "Aucun patient trouvé pour l'exportation."

            donne_propre = []
            for p in liste_patient:
                donne_propre.append({
                    "code patient": p.get_code_patient(),
                    "nom patient": p.get_nom(),
                    "prenom patient": p.get_prenom(),
                    "telephone patient": p.get_telephone(),
                    "date naissance": p.get_naissance(),
                    "genre": p.get_genre(),
                    "profession": p.get_profession(),
                    "adresse": p.get_adresse()
                })

            df = pd.DataFrame(donne_propre)
            df.to_csv(fichier, index=False, sep=';', encoding='utf-8-sig')
            return True, f"L'exportation vers {os.path.basename(fichier)} a réussi !"
        except Exception as e:
            return False, f"Erreur lors de l'exportation : {str(e)}"

    def import_from_excel(self, fichier):
        """
        Importe des patients depuis un fichier Excel.
        Chaque ligne est validée individuellement.

        Args:
            fichier (str): Chemin du fichier source.

        Returns:
            tuple: (succès, message)
        """
        try:
            df = pd.read_excel(fichier)
            df = df.fillna("")
            succes_count = 0
            erreur = []

            for index, row in df.iterrows():
                nouveau_patient = self.patient_classe(
                    code_patient="",
                    nom=str(row.get('Nom', '')),
                    prenom=str(row.get('Prénom', '')),
                    telephone=str(row.get('Telephone', '')),
                    naissance=row.get('Date de naissance', ''),
                    genre=str(row.get('genre', '')),
                    profession=str(row.get('Profession', '')),
                    adresse=str(row.get('Adresse', ''))
                )

                reussite, message = self.save_patient(nouveau_patient)
                if reussite:
                    succes_count += 1
                else:
                    erreur.append(f"ligne {index + 2}: {message}")

            if not erreur:
                return True, f"Importation réussie : {succes_count} patients ajoutés"
            else:
                msg_final = (
                    f"{succes_count} patients jouté. "
                    f"Erreurs sur les lignes suivantes :\n" + "\n".join(erreur[:5])
                )
                if len(erreur) > 5:
                    msg_final += "\n..."
                return False, msg_final
        except Exception as e:
            return False, f"Erreur de lecture du fichier: {e}"

    def import_from_csv(self, chemin_fichier):
        """
        Importe des patients depuis un fichier CSV.
        Détection automatique du séparateur.

        Args:
            chemin_fichier (str): Chemin du fichier source.

        Returns:
            tuple: (succès, message)
        """
        try:
            df = pd.read_csv(chemin_fichier, sep=None, engine='python')
            df = df.fillna("")
            succes_count = 0
            erreur = []

            for index, row in df.iterrows():
                nouveau_patient = self.patient_classe(
                    code_patient='',
                    nom=str(row.get('Nom', '')).strip(),
                    prenom=str(row.get('Prenom', '')).strip(),
                    telephone=str(row.get('Telephone', '')).strip(),
                    naissance=row.get('Date de naissance', ''),
                    genre=str(row.get('genre', '')).strip(),
                    profession=str(row.get('Profession', '')).strip(),
                    adresse=str(row.get('adresse', '')).strip()
                )

                reussite, message = self.save_patient(nouveau_patient)
                if reussite:
                    succes_count += 1
                else:
                    erreur.append(f"Ligne {index + 2} : {message}")

            if not erreur:
                return True, f"Importation réussie : {succes_count} patients ajoutés."
            else:
                msg_final = (
                    f"{succes_count} ajouté(s). "
                    f"Erreurs sur les lignes suivantes :\n" + "\n".join(erreur[:5])
                )
                if len(erreur) > 5:
                    msg_final += "\n..."
                return False, msg_final
        except Exception as e:
            return False, f"Erreur de lecture du fichier CSV : {e}"

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self):
        """
        Récupère les informations du cabinet (nom, adresse, logo).

        Returns:
            dict: {'nom_cabinet', 'adresse_cabinet', 'logo_url'}
        """
        info = self.cabinet_dao.get_info_cabinet() or {}
        nom_cabinet = info.get("nom_cabinet", "Cabinet ophtalmologique")
        adresse_cabinet = info.get("adresse", "")
        logo_cabinet = info.get("logo", None)

        final_logo = None
        if logo_cabinet:
            script = os.path.dirname(__file__)
            path = os.path.join(script, "..", "connexion", "image", logo_cabinet)
            if os.path.exists(path):
                final_logo = path

        return {
            "nom_cabinet": nom_cabinet,
            "adresse_cabinet": adresse_cabinet,
            "logo_url": final_logo
        }

    # =========================================================================
    # GÉNÉRATION PDF
    # =========================================================================

    def generer_carnet_par_code(self, code_patient, dossier_destination):
        """
        Génère le carnet PDF d'un patient identifié par son code.

        Args:
            code_patient (str): Code du patient.
            dossier_destination (str): Dossier de sortie.

        Returns:
            tuple: (succès, message)
        """
        try:
            patient = self.dao.reed_by_code_patient(code_patient)
            if not patient:
                return False, f"Aucun patient trouvé avec le code {code_patient}"

            nom_f = f"Carnet_{patient.get_nom()}_{code_patient}.pdf".replace("/", "_")
            chemin_complet = os.path.join(dossier_destination, nom_f)

            return PatientPDFService.generer_carnet_patient(
                controller=self,
                chemin_save=chemin_complet,
                patient=patient
            )
        except Exception as e:
            return False, f"Erreur contrôleur : {e}"

    def generer_liste_patients_par_genre(self, genre, dossier_destination):
        """
        Génère le PDF de la liste des patients filtrés par genre.

        Args:
            genre (str): Genre à filtrer.
            dossier_destination (str): Dossier de sortie.

        Returns:
            tuple: (succès, message)
        """
        try:
            liste_patients = self.dao.reed_by_genre_patient(genre)
            if not liste_patients:
                return False, f"Aucun patient de genre '{genre}' trouvé dans la base."

            horodatage = datetime.now().strftime("%Y%m%d_%H%M")
            nom_fichier = f"Liste_Patients_{genre}_{horodatage}.pdf"
            chemin_complet = os.path.join(dossier_destination, nom_fichier)

            return PatientPDFService.generer_liste_patients_par_genre(
                controller=self,
                chemin_save=chemin_complet,
                liste_patients=liste_patients,
                genre_selectionne=genre
            )
        except Exception as e:
            return False, f"Erreur lors de l'exportation : {str(e)}"

    def generer_liste_total_patient(self, dossier_destination):
        """
        Génère le PDF de la liste complète de tous les patients.

        Args:
            dossier_destination (str): Dossier de sortie.

        Returns:
            tuple: (succès, message)
        """
        try:
            liste_patients = self.dao.reedAllPatient()
            if not liste_patients:
                return False, "Aucun patient trouvé dans la base"

            horodate = datetime.now().strftime("%Y%m%d_%H%M")
            nom_f = f"Liste de fichier_{horodate}.pdf"
            chemin_complet = os.path.join(dossier_destination, nom_f)

            return PatientPDFService.generer_liste_total_patients(
                controller=self,
                chemin_save=chemin_complet,
                liste_patients=liste_patients
            )
        except Exception as e:
            return False, f"Erreur lors de la génération du pdf: {str(e)}"
