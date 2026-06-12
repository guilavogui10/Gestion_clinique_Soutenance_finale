"""
consultation_service.py
------------------------
Service métier — Gestion des consultations.

Responsabilités :
  - Validation des données de consultation
  - CRUD : création, modification, suppression
  - Détermination du prochain statut patient (workflow)
  - Récupération (par code, visite, session, historique patient)
  - Listes filtrées de patients (attente, examen, chirurgie, etc.)
  - Statistiques (cards, graphiques mensuels/journaliers, revenus)
  - Recherche avancée (dates, services, par patient)
  - Informations cabinet
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, Optional

from data.dao_consultation import ConsultationDAO
from data.dao_visite import Visitedao
from models.modele_consultation import Consultation
from parametre.dao_param import CabinetDAO


class ConsultationService:
    """
    Service métier pour la gestion des consultations.
    Contient la validation, le CRUD, le workflow patient et les statistiques.
    """

    def __init__(self, dao=None, cabinet_dao=None, visite_dao=None):
        self.dao         = dao or ConsultationDAO()
        self.cabinet_dao = cabinet_dao or CabinetDAO()
        self.visite_dao  = visite_dao or Visitedao()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # MÉTHODES DE VALIDATION (LOGIQUE MÉTIER)
    # =========================================================================

    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 3) -> tuple:
        """Valide qu'un champ texte est non vide et sans caractères interdits."""
        if not texte or texte.strip() == "":
            return False, f"Le champ {nom_champ} est obligatoire"
        if len(texte.strip()) < min_longueur:
            return False, f"Le {nom_champ} doit contenir au moins {min_longueur} caractères"
        if re.search(r'[<>{}[\]\\|`~]', texte):
            return False, f"Le {nom_champ} contient des caractères spéciaux interdits"
        return True, ""

    def valider_date(self, date_consultation) -> tuple:
        """Valide que la date de consultation est exactement celle d'aujourd'hui."""
        if not date_consultation:
            return False, "La date de consultation est obligatoire"
        try:
            if isinstance(date_consultation, str):
                date_obj = datetime.strptime(date_consultation, "%d/%m/%Y").date()
            else:
                date_obj = date_consultation.date() if hasattr(date_consultation, 'date') else date_consultation
            aujourdhui = datetime.now().date()
            if date_obj < aujourdhui:
                return False, "La date de consultation ne peut pas être dans le passé"
            if date_obj > aujourdhui:
                return False, "La date de consultation ne peut pas être dans le futur"
            return True, ""
        except Exception:
            return False, "Format de date invalide (attendu: JJ/MM/AAAA)"

    def valider_frais(self, frais) -> tuple:
        """Valide que les frais sont un nombre positif."""
        try:
            frais_float = float(frais)
            if frais_float < 0:
                return False, "Les frais ne peuvent pas être négatifs"
            return True, ""
        except Exception:
            return False, "Les frais doivent être un nombre valide"

    def valider_choix(self, valeur: str, nom_champ: str) -> tuple:
        """Valide qu'un champ booléen vaut 'Oui' ou 'Non'."""
        if valeur not in ["Oui", "Non"]:
            return False, f"Le champ {nom_champ} doit être 'Oui' ou 'Non'"
        return True, ""

    def valider_codes_obligatoires(self, consultation: Consultation) -> tuple:
        """Valide que les codes visite, session et personne sont renseignés."""
        if not consultation.code_visite or not consultation.code_session or not consultation.code_personne:
            return False, "Tous les codes (visite, session, personne) sont obligatoires"
        return True, ""

    def valider_consultation(self, consultation: Consultation) -> tuple:
        """Regroupe toutes les validations communes à la création et modification."""
        valide, msg = self.valider_texte(consultation.diagnostique, "diagnostique")
        if not valide:
            return False, msg
        valide, msg = self.valider_date(consultation.date_consultation)
        if not valide:
            return False, msg
        valide, msg = self.valider_frais(consultation.frais_consultation)
        if not valide:
            return False, msg
        return True, ""

    def _nettoyer_consultation(self, consultation: Consultation) -> None:
        """Nettoie les champs texte (supprime les espaces superflus)."""
        consultation.diagnostique = consultation.diagnostique.strip()



    # =========================================================================
    # MÉTHODES CRUD
    # =========================================================================

    def creer_consultation(self, consultation: Consultation) -> tuple:
        """Valide et crée une nouvelle consultation."""
        valide, msg = self.valider_consultation(consultation)
        if not valide:
            return False, msg
        valide, msg = self.valider_codes_obligatoires(consultation)
        if not valide:
            return False, msg
        if self.dao.obtenir_par_visite(consultation.code_visite):
            return False, "Une consultation existe déjà pour cette visite"
        self._nettoyer_consultation(consultation)
        if self.dao.ajouter(consultation):
            self.logger.info(f"Consultation {consultation.code} créée pour visite {consultation.code_visite}")
            return True, "Consultation créée avec succès"
        return False, "Erreur lors de la création de la consultation"

    def modifier_consultation(self, consultation: Consultation) -> tuple:
        """Valide et met à jour une consultation existante."""
        valide, msg = self.valider_consultation(consultation)
        if not valide:
            return False, msg
        self._nettoyer_consultation(consultation)
        if self.dao.modifier(consultation):
            self.logger.info(f"Consultation {consultation.code} modifiée")
            return True, "Consultation modifiée avec succès"
        return False, "Erreur lors de la modification de la consultation"

    def supprimer_consultation(self, code: str) -> tuple:
        """Supprime une consultation par son code."""
        if not code:
            return False, "Code de consultation invalide"
        if self.dao.supprimer(code):
            return True, "Consultation supprimée avec succès"
        return False, "Erreur lors de la suppression de la consultation"

    # =========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        return self.dao.obtenir_par_code(code)
    
    def obtenir_consultation(self, code: str):
        """Alias pour obtenir_par_code"""
        return self.obtenir_par_code(code)

    def obtenir_par_visite(self, code_visite: str):
        return self.dao.obtenir_par_visite(code_visite)
    
    def lister_consultations_par_visite(self, code_visite: str) -> list:
        """Retourne toutes les consultations d'une visite (retourne une liste)"""
        consultation = self.dao.obtenir_par_visite(code_visite)
        if consultation:
            return [consultation]
        return []

    def lister_consultations(self, code_session: str) -> list:
        return self.dao.lister_par_session(code_session)

    def lister_toutes(self) -> list:
        return self.dao.lister_toutes()

    def rechercher_consultation(self, critere: str, code_session: str) -> list:
        return self.dao.rechercher_par_critere(critere, code_session)

    def obtenir_consultation_complete(self, code_consultation: str):
        return self.dao.consultation_complete(code_consultation)

    def obtenir_services_lies(self, code_consultation: str) -> dict:
        return self.dao.services_lies(code_consultation)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        return self.dao.historique_patient(code_patient)

    # =========================================================================
    # MÉTHODES PATIENTS (LISTES FILTRÉES)
    # =========================================================================

    def obtenir_patients_attente(self, code_session: str) -> list:
        return self.dao.patients_en_attente(code_session)

    def obtenir_patients_examen(self, code_session: str) -> list:
        return self.dao.patients_pour_examen(code_session)

    def obtenir_patients_chirurgie(self, code_session: str) -> list:
        return self.dao.patients_pour_chirurgie(code_session)

    def obtenir_patients_lunette(self, code_session: str) -> list:
        return self.dao.patients_pour_lunette(code_session)

    def obtenir_patients_prescription(self, code_session: str) -> list:
        return self.dao.patients_pour_prescription(code_session)

    def info_cabinet(self) -> dict:
        return self.cabinet_dao.get_info_cabinet()

    # =========================================================================
    # MÉTHODES STATISTIQUES CARDS
    # =========================================================================

    def obtenir_nombre_total(self, code_session: str) -> int:
        return self.dao.nombre_total_par_session(code_session)

    def obtenir_consultations_aujourd_hui(self, code_session: str) -> int:
        return self.dao.nombre_consultations_aujourd_hui(code_session)

    def obtenir_nombre_patients_en_attente(self, code_session: str) -> int:
        return self.dao.nombre_patients_en_attente(code_session)

    def obtenir_montant_aujourd_hui(self, code_session: str) -> float:
        return self.dao.montant_consultations_aujourd_hui(code_session)

    def obtenir_montant_session(self, code_session: str) -> float:
        return self.dao.montant_consultations_session(code_session)

    # =========================================================================
    # MÉTHODES STATISTIQUES & GRAPHES
    # =========================================================================

    def obtenir_nombre_par_mois(self, code_session: str) -> dict:
        return self.dao.nombre_par_mois(code_session)

    def obtenir_nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.dao.nombre_par_jour(code_session, annee, mois)

    def obtenir_montant_par_mois(self, code_session: str) -> dict:
        return self.dao.montant_par_mois(code_session)

    def obtenir_montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        return self.dao.montant_par_jour(code_session, annee, mois)

    def obtenir_revenu_moyen_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_montant_journalier_mois(code_session)

    def obtenir_moyenne_montant_journalier_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_montant_journalier_mois(code_session)

    def obtenir_moyenne_consultations_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_consultations_journalieres_mois(code_session)

    def obtenir_moyenne_nombre_journalier_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_consultations_journalieres_mois(code_session)

    def obtenir_moyenne_journaliere_par_mois(self, code_session: str) -> dict:
        return self.dao.moyenne_consultations_journalieres_mois(code_session)

    def obtenir_resume_session(self, code_session: str) -> dict:
        return self.dao.resume_session(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        return self.dao.revenu_total(code_session, date_debut, date_fin)

    def obtenir_top_diagnostics(self, code_session: str, limite: int = 10) -> list:
        return self.dao.top_diagnostics(code_session, limite)

    def obtenir_consultations_par_personnel(self, code_session: str) -> list:
        return self.dao.consultations_par_personnel(code_session)

    def obtenir_taux_conversion(self, code_session: str) -> dict:
        return self.dao.taux_conversion_services(code_session)

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Récupère les informations du cabinet médical."""
        try:
            info = self.cabinet_dao.get_info_cabinet() or {}
            nom_cabinet = info.get("nom_cabinet", "Cabinet ophtalmologique")
            adresse_cabinet = info.get("adresse", "")
            logo_cabinet = info.get("logo", None)
            final_logo = None
            if logo_cabinet:
                try:
                    base_dir = os.path.dirname(os.path.dirname(__file__))
                    logo_path = os.path.join(base_dir, "connexion", "image", logo_cabinet)
                    if os.path.exists(logo_path) and os.path.isfile(logo_path):
                        final_logo = os.path.abspath(logo_path)
                except Exception as e:
                    self.logger.warning(f"Erreur chemin logo: {e}")
            return {
                "nom_cabinet": nom_cabinet,
                "adresse_cabinet": adresse_cabinet,
                "logo_url": final_logo
            }
        except Exception as e:
            self.logger.error(f"Erreur get_cabinet_info: {e}")
            return {"nom_cabinet": "Cabinet ophtalmologique", "adresse_cabinet": "", "logo_url": None}

    def lister_personnel(self) -> list:
        """Retourne la liste du personnel pour le formulaire."""
        return self.dao.lister_personnel()

    def lister_personnel_par_roles(self, roles: list) -> list:
        from data.dao_user import UserDAO
        return UserDAO().lister_personnel_par_roles(roles)

    # =========================================================================
    # MÉTHODES DE RECHERCHE AVANCÉE & FILTRAGE
    # =========================================================================

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        try:
            return self.dao.rechercher_entre_dates(code_session, date_debut, date_fin) or []
        except Exception as e:
            self.logger.error(f"Erreur rechercher_entre_dates: {e}")
            return []

    def rechercher_par_services(self, code_session: str, examen=None, chirurgie=None,
                               commandelunette=None, prescription=None) -> list:
        try:
            return self.dao.rechercher_par_services(
                code_session, examen, chirurgie, commandelunette, prescription
            ) or []
        except Exception as e:
            self.logger.error(f"Erreur rechercher_par_services: {e}")
            return []

    def obtenir_consultations_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        try:
            return self.dao.consultations_par_patient_par_mois(code_session, code_patient) or {}
        except Exception as e:
            self.logger.error(f"Erreur obtenir_consultations_par_patient_par_mois: {e}")
            return {}

    def obtenir_nombre_par_mois_filtre(self, code_session: str, examen: str = None,
                                       chirurgie: str = None, commandelunette: str = None,
                                       prescription: str = None) -> dict:
        try:
            return self.dao.nombre_par_mois_filtre(
                code_session, examen, chirurgie, commandelunette, prescription
            ) or {}
        except Exception as e:
            self.logger.error(f"Erreur obtenir_nombre_par_mois_filtre: {e}")
            return {}

    def obtenir_codes_patients_session(self, code_session: str) -> list:
        try:
            return self.dao.codes_patients_session(code_session) or []
        except Exception as e:
            self.logger.error(f"Erreur obtenir_codes_patients_session: {e}")
            return []

    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================

    def _valider_date_import(self, date_val) -> tuple:
        """Valide le format de date pour import — accepte les dates passées."""
        if not date_val or str(date_val).strip() in ("", "nan", "None"):
            return True, datetime.now()
        if isinstance(date_val, datetime):
            return True, date_val
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return True, datetime.strptime(str(date_val), fmt)
            except ValueError:
                continue
        return False, "Format de date invalide (YYYY-MM-DD ou DD/MM/YYYY)"

    def _valider_date_dans_session(self, date_obj: datetime, plage: dict) -> str | None:
        """Retourne un message d'erreur si la date est hors session ou dans le futur, None si OK."""
        aujourd_hui = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        nom = plage.get("nom_session", "session active")
        if date_obj > aujourd_hui:
            return f"Date {date_obj.date()} dans le futur — importation refusée."
        date_debut = plage.get("date_debut")
        date_fin   = plage.get("date_fin")
        if isinstance(date_debut, datetime) and date_obj < date_debut:
            return f"Date {date_obj.date()} antérieure au début de la session '{nom}' ({date_debut.date()})."
        if isinstance(date_fin, datetime) and date_obj > date_fin:
            return f"Date {date_obj.date()} postérieure à la fin de la session '{nom}' ({date_fin.date()})."
        return None

    def _get_session_from_visite(self, code_visite: str) -> str:
        """Récupère le code_session depuis la visite liée."""
        try:
            return self.visite_dao.get_session_from_visite(code_visite)
        except Exception as e:
            self.logger.error(f"Erreur _get_session_from_visite: {e}")
            return None

    def _creer_consultation_import(self, consultation: Consultation) -> tuple:
        """creer_consultation sans restriction de date passée — réservé à l'import.
        code_personne est optionnel pour l'import (pas de visite formulaire).
        """
        try:
            valide, msg = self.valider_texte(consultation.diagnostique, "diagnostique")
            if not valide:
                return False, msg
            valide, msg = self.valider_frais(consultation.frais_consultation)
            if not valide:
                return False, msg
            # Pour l'import : seuls code_visite et code_session sont obligatoires
            if not consultation.code_visite or not consultation.code_session:
                return False, "code_visite et code_session sont obligatoires"
            if self.dao.obtenir_par_visite(consultation.code_visite):
                return False, f"Une consultation existe déjà pour la visite {consultation.code_visite}"
            self._nettoyer_consultation(consultation)
            if self.dao.ajouter(consultation):
                return True, "Consultation créée"
            return False, "Erreur lors de la création"
        except Exception as e:
            err = str(e)
            if "1452" in err or "foreign key" in err.lower():
                return False, "Code visite ou personnel introuvable en base."
            return False, err[:120]

    @staticmethod
    def _get_col(row, *cles):
        for k in cles:
            val = row.get(k, '')
            if val is not None and str(val).strip() not in ('', 'nan', 'None'):
                return str(val).strip()
        return ''

    def obtenir_donnees_pour_export(self) -> list:
        """Retourne toutes les consultations formatées pour aperçu/export."""
        try:
            consultations = self.dao.lister_toutes()
            return [
                {
                    "code":               c.code,
                    "code_visite":        c.code_visite,
                    "code_personnel":     c.code_personne,
                    "diagnostique":       c.diagnostique,
                    "frais_consultation": c.frais_consultation,
                    "statut_facture":     c.statut_facture,
                    "date_consultation":  str(c.date_consultation),
                }
                for c in consultations
            ]
        except Exception as e:
            self.logger.error(f"Erreur obtenir_donnees_pour_export consultation: {e}")
            return []

    def export_to_excel(self, chemin: str) -> tuple:
        """Exporte toutes les consultations vers un fichier Excel."""
        try:
            import pandas as pd
            donnees = self.obtenir_donnees_pour_export()
            if not donnees:
                return False, "Aucune consultation à exporter."
            pd.DataFrame(donnees).to_excel(chemin, index=False)
            return True, f"{len(donnees)} consultation(s) exportée(s) avec succès."
        except Exception as e:
            return False, f"Erreur export : {e}"

    def export_to_csv(self, chemin: str) -> tuple:
        """Exporte toutes les consultations vers un fichier CSV."""
        try:
            import pandas as pd
            donnees = self.obtenir_donnees_pour_export()
            if not donnees:
                return False, "Aucune consultation à exporter."
            pd.DataFrame(donnees).to_csv(chemin, index=False, encoding="utf-8-sig")
            return True, f"{len(donnees)} consultation(s) exportée(s) avec succès."
        except Exception as e:
            return False, f"Erreur export : {e}"

    def import_from_excel(self, chemin: str) -> tuple:
        """
        Importe des consultations depuis un fichier Excel.
        Colonnes requises : code_visite, code_personnel, diagnostique, frais_consultation
        Colonnes optionnelles : date_consultation, statut_facture
        """
        try:
            import pandas as pd
            df = pd.read_excel(chemin)
            df.columns = [c.strip().lower() for c in df.columns]
            df = df.fillna("")
            return self._traiter_import(df)
        except Exception as e:
            return False, f"Erreur lecture fichier : {e}"

    def import_from_csv(self, chemin: str) -> tuple:
        """
        Importe des consultations depuis un fichier CSV.
        Colonnes requises : code_visite, code_personnel, diagnostique, frais_consultation
        Colonnes optionnelles : date_consultation, statut_facture
        """
        try:
            import pandas as pd
            df = pd.read_csv(chemin, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip().lower() for c in df.columns]
            df = df.fillna("")
            return self._traiter_import(df)
        except Exception as e:
            return False, f"Erreur lecture fichier : {e}"

    def _traiter_import(self, df) -> tuple:
        """Logique commune d'import Excel/CSV."""
        colonnes_requises = ["code_visite", "diagnostique", "frais_consultation"]
        for col in colonnes_requises:
            if col not in df.columns:
                return False, f"Colonne manquante dans le fichier : '{col}'"

        succes_count = 0
        erreurs = []
        _cache_plages: dict = {}  # code_session → {nom_session, date_debut, date_fin}

        for index, row in df.iterrows():
            ligne = index + 2
            try:
                g = self._get_col
                code_visite    = g(row, "code_visite")
                code_personnel = g(row, "code_personnel", "code_personne", "personnel")
                diagnostique   = g(row, "diagnostique", "diagnostic")
                frais_raw      = row.get("frais_consultation", 0)
                date_raw       = row.get("date_consultation", "")
                statut         = g(row, "statut_facture", "statut") or "attente payement"

                if not code_visite:
                    erreurs.append(f"Ligne {ligne} : code_visite vide")
                    continue

                # Récupérer code_session depuis la visite
                code_session = self._get_session_from_visite(code_visite)
                if not code_session:
                    erreurs.append(f"Ligne {ligne} : visite '{code_visite}' introuvable")
                    continue

                if code_session not in _cache_plages:
                    plage = self.visite_dao.get_plage_session(code_session)
                    if plage:
                        _cache_plages[code_session] = plage

                try:
                    frais = float(frais_raw) if frais_raw != "" else 0.0
                except (ValueError, TypeError):
                    erreurs.append(f"Ligne {ligne} : frais_consultation invalide")
                    continue

                ok_date, date_obj = self._valider_date_import(date_raw)
                if not ok_date:
                    erreurs.append(f"Ligne {ligne} : {date_obj}")
                    continue

                plage = _cache_plages.get(code_session)
                if plage:
                    err_plage = self._valider_date_dans_session(date_obj, plage)
                    if err_plage:
                        erreurs.append(f"Ligne {ligne} : {err_plage}")
                        continue

                consultation = Consultation(
                    code_visite=code_visite,
                    code_session=code_session,
                    code_personne=code_personnel or None,
                    diagnostique=diagnostique,
                    frais_consultation=frais,
                    statut_facture=statut,
                    date_consultation=date_obj
                )

                ok, msg = self._creer_consultation_import(consultation)
                if ok:
                    succes_count += 1
                else:
                    erreurs.append(f"Ligne {ligne} : {msg}")

            except Exception as e:
                erreurs.append(f"Ligne {ligne} : erreur inattendue — {str(e)[:100]}")

        if succes_count == 0:
            msg = "Aucune consultation importée."
            if erreurs:
                msg += "\nErreurs :\n" + "\n".join(erreurs[:3])
            return False, msg

        msg = f"{succes_count} consultation(s) importée(s) avec succès."
        if erreurs:
            msg += f"\nDétail ({len(erreurs)} erreur(s)) :\n" + "\n".join(
                [e[:120] for e in erreurs[:3]]
            )
            if len(erreurs) > 3:
                msg += f"\n... et {len(erreurs) - 3} autre(s)."
            return False, msg
        return True, msg
