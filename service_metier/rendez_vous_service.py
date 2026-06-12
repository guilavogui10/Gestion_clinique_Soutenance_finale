"""
rendez_vous_service.py
----------------------
Service metier - Gestion des rendez-vous.

Responsabilites :
  - Validation des donnees
  - Planification et controle metier
  - CRUD
  - Recherche / filtrage
  - Monitoring, statistiques, alertes, predictions
  - Informations cabinet
"""

import os
import re
import logging
from datetime import date, datetime
from typing import Dict, Optional

from data.dao_rendez_vous import RendezVousDAO
from models.modele_rendez_vous import RendezVous
from parametre.dao_param import CabinetDAO


class RendezVousService:
    """
    Service metier pour la gestion des rendez-vous.
    Contient la validation, la planification et les appels au DAO.
    """

    STATUTS_AUTORISES = {
        "attente",
        "confirme",
        "en_cours",
        "termine",
        "annule",
        "absent",
        "reporte"
    }

    def __init__(self, dao=None, cabinet_dao=None):
        self.dao = dao or RendezVousDAO()
        self.cabinet_dao = cabinet_dao or CabinetDAO()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 1) -> tuple:
        """Valide qu'un champ texte est non vide et sans caracteres interdits."""
        if texte is None or str(texte).strip() == "":
            return False, f"Le champ {nom_champ} est obligatoire"

        texte = str(texte).strip()
        if len(texte) < min_longueur:
            return False, f"Le champ {nom_champ} est invalide"

        if re.search(r"[<>{}\[\]\\|`~]", texte):
            return False, f"Le champ {nom_champ} contient des caracteres interdits"

        return True, ""

    def _normaliser_statut(self, statut: str) -> str:
        statut = (statut or "").strip().lower()
        mapping = {
            "attente": "attente",
            "en attente": "attente",
            "confirme": "confirme",
            "confirmee": "confirme",
            "confirmé": "confirme",
            "confirmée": "confirme",
            "en cours": "en_cours",
            "encours": "en_cours",
            "en_cours": "en_cours",
            "termine": "termine",
            "terminee": "termine",
            "terminé": "termine",
            "terminée": "termine",
            "annule": "annule",
            "annulee": "annule",
            "annulé": "annule",
            "annulée": "annule",
            "absent": "absent",
            "absente": "absent",
            "reporte": "reporte",
            "reportee": "reporte",
            "reporté": "reporte",
            "reportée": "reporte"
        }
        return mapping.get(statut, statut)

    def valider_statut(self, statut: str) -> tuple:
        """Valide que le statut du rendez-vous est autorise."""
        statut_normalise = self._normaliser_statut(statut)
        if statut_normalise not in self.STATUTS_AUTORISES:
            return False, (
                "Statut invalide. Valeurs autorisees : attente, confirme, "
                "annule, termine, absent, reporte, en_cours"
            )
        return True, ""

    def _parse_datetime(self, valeur):
        """Convertit une valeur en datetime si possible."""
        if valeur is None:
            return None

        if isinstance(valeur, datetime):
            return valeur

        if isinstance(valeur, date):
            return datetime.combine(valeur, datetime.min.time())

        if isinstance(valeur, str):
            texte = valeur.strip()
            formats = [
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y",
                "%Y-%m-%d"
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(texte, fmt)
                except ValueError:
                    continue

        return None

    def valider_date(self, date_rendez_vous) -> tuple:
        """
        Valide qu'une date de rendez-vous est fournie et qu'elle n'est pas dans le passe.
        """
        if not date_rendez_vous:
            return False, "La date du rendez-vous est obligatoire"

        date_obj = self._parse_datetime(date_rendez_vous)
        if not date_obj:
            return False, "Format de date invalide"

        maintenant = datetime.now()

        # Si l'heure est precisee, on bloque le passe complet.
        if isinstance(date_rendez_vous, datetime):
            if date_obj < maintenant:
                return False, "La date et l'heure du rendez-vous ne peuvent pas etre dans le passe"
            return True, ""

        if isinstance(date_rendez_vous, str) and ":" in date_rendez_vous:
            if date_obj < maintenant:
                return False, "La date et l'heure du rendez-vous ne peuvent pas etre dans le passe"
            return True, ""

        # Sinon, verification uniquement sur la date.
        if date_obj.date() < maintenant.date():
            return False, "La date du rendez-vous ne peut pas etre dans le passe"

        return True, ""

    def valider_codes_obligatoires(self, rdv: RendezVous) -> tuple:
        """Valide que les codes essentiels sont renseignes."""
        for nom, valeur in [
            ("code visite", rdv.code_visite),
            ("code session", rdv.code_session),
            ("code personnel", rdv.code_personnel)
        ]:
            valide, msg = self.valider_texte(valeur, nom)
            if not valide:
                return False, msg
        return True, ""

    def valider_rendez_vous(self, rdv: RendezVous) -> tuple:
        """Regroupe toutes les validations metier d'un rendez-vous."""
        if not rdv:
            return False, "Objet rendez-vous invalide"

        valide, msg = self.valider_codes_obligatoires(rdv)
        if not valide:
            return False, msg

        valide, msg = self.valider_date(rdv.date_rendez_vous)
        if not valide:
            return False, msg

        valide, msg = self.valider_statut(rdv.statut_rendez_vous)
        if not valide:
            return False, msg

        return True, ""

    def _nettoyer_rendez_vous(self, rdv: RendezVous) -> None:
        """Nettoie et normalise les champs texte."""
        rdv.code_visite = rdv.code_visite.strip()
        rdv.code_session = rdv.code_session.strip()
        rdv.code_personnel = rdv.code_personnel.strip()
        rdv.statut_rendez_vous = self._normaliser_statut(rdv.statut_rendez_vous)

    def valider_planification_creation(self, rdv: RendezVous) -> tuple:
        """Controle les regles de planification avant creation."""
        if self.dao.verifier_doublon_visite(rdv.code_visite):
            return False, "Un rendez-vous existe deja pour cette visite"

        if not self.dao.verifier_disponibilite_personnel(rdv.code_personnel, rdv.date_rendez_vous):
            return False, "Le personnel selectionne n'est pas disponible a cette date/heure"

        if self.dao.verifier_chevauchement(rdv.code_personnel, rdv.date_rendez_vous):
            return False, "Ce rendez-vous chevauche un autre rendez-vous du personnel"

        return True, ""

    def valider_planification_modification(self, rdv: RendezVous) -> tuple:
        """Controle les regles de planification avant modification."""
        if self.dao.verifier_doublon_visite(rdv.code_visite, rdv.code_rendez_vous):
            return False, "Une autre ligne de rendez-vous existe deja pour cette visite"

        if not self.dao.verifier_disponibilite_personnel(
            rdv.code_personnel,
            rdv.date_rendez_vous,
            rdv.code_rendez_vous
        ):
            return False, "Le personnel selectionne n'est pas disponible a cette date/heure"

        if self.dao.verifier_chevauchement(
            rdv.code_personnel,
            rdv.date_rendez_vous,
            rdv.code_rendez_vous
        ):
            return False, "Ce rendez-vous chevauche un autre rendez-vous du personnel"

        return True, ""

    # =========================================================================
    # CRUD
    # =========================================================================

    def generer_code_rendez_vous(self) -> str:
        return self.dao.generate_code_rendez_vous()

    def creer_rendez_vous(self, rdv: RendezVous) -> tuple:
        """Valide puis cree un rendez-vous."""
        try:
            valide, msg = self.valider_rendez_vous(rdv)
            if not valide:
                return False, msg

            self._nettoyer_rendez_vous(rdv)

            valide, msg = self.valider_planification_creation(rdv)
            if not valide:
                return False, msg

            if self.dao.ajouter(rdv):
                self.logger.info(
                    "Rendez-vous %s cree pour la visite %s",
                    rdv.code_rendez_vous,
                    rdv.code_visite
                )
                return True, "Rendez-vous cree avec succes"

            return False, "Erreur lors de la creation du rendez-vous"
        except Exception as e:
            self.logger.error(f"Erreur creer_rendez_vous: {e}", exc_info=True)
            return False, "Erreur technique lors de la creation du rendez-vous"

    def modifier_rendez_vous(self, rdv: RendezVous) -> tuple:
        """Valide puis modifie un rendez-vous existant."""
        try:
            valide, msg = self.valider_rendez_vous(rdv)
            if not valide:
                return False, msg

            if not rdv.code_rendez_vous:
                return False, "Le code du rendez-vous est obligatoire pour la modification"

            if not self.dao.obtenir_par_code(rdv.code_rendez_vous):
                return False, "Le rendez-vous a modifier est introuvable"

            self._nettoyer_rendez_vous(rdv)

            valide, msg = self.valider_planification_modification(rdv)
            if not valide:
                return False, msg

            if self.dao.modifier(rdv):
                self.logger.info("Rendez-vous %s modifie", rdv.code_rendez_vous)
                return True, "Rendez-vous modifie avec succes"

            return False, "Erreur lors de la modification du rendez-vous"
        except Exception as e:
            self.logger.error(f"Erreur modifier_rendez_vous: {e}", exc_info=True)
            return False, "Erreur technique lors de la modification du rendez-vous"

    def supprimer_rendez_vous(self, code: str) -> tuple:
        """Supprime un rendez-vous par son code."""
        if not code or str(code).strip() == "":
            return False, "Code de rendez-vous invalide"

        try:
            if self.dao.supprimer(code.strip()):
                self.logger.info("Rendez-vous %s supprime", code)
                return True, "Rendez-vous supprime avec succes"
            return False, "Erreur lors de la suppression du rendez-vous"
        except Exception as e:
            self.logger.error(f"Erreur supprimer_rendez_vous: {e}", exc_info=True)
            return False, "Erreur technique lors de la suppression du rendez-vous"

    def changer_statut_rendez_vous(self, code_rendez_vous: str, nouveau_statut: str, code_session: str = None) -> tuple:
        """Change le statut d'un rendez-vous avec validation."""
        if not code_rendez_vous or str(code_rendez_vous).strip() == "":
            return False, "Code de rendez-vous invalide"

        valide, msg = self.valider_statut(nouveau_statut)
        if not valide:
            return False, msg

        try:
            statut_normalise = self._normaliser_statut(nouveau_statut)
            if self.dao.changer_statut_rendez_vous(code_rendez_vous.strip(), statut_normalise, code_session):
                self.logger.info(
                    "Statut rendez-vous %s modifie vers %s",
                    code_rendez_vous,
                    statut_normalise
                )
                return True, "Statut du rendez-vous mis a jour avec succes"
            return False, "Impossible de modifier le statut du rendez-vous"
        except Exception as e:
            self.logger.error(f"Erreur changer_statut_rendez_vous: {e}", exc_info=True)
            return False, "Erreur technique lors du changement de statut"

    def changer_statut(self, code_rendez_vous: str, nouveau_statut: str, code_session: str = None) -> tuple:
        """Alias de compatibilite."""
        return self.changer_statut_rendez_vous(code_rendez_vous, nouveau_statut, code_session)

    # =========================================================================
    # PLANIFICATION
    # =========================================================================

    def verifier_disponibilite_personnel(self, code_personnel: str, date_rendez_vous, code_rendez_vous_exclu: str = None) -> bool:
        try:
            return self.dao.verifier_disponibilite_personnel(
                code_personnel,
                date_rendez_vous,
                code_rendez_vous_exclu
            )
        except Exception as e:
            self.logger.error(f"Erreur verifier_disponibilite_personnel: {e}", exc_info=True)
            return False

    def verifier_doublon_visite(self, code_visite: str, code_rendez_vous_exclu: str = None) -> bool:
        try:
            return self.dao.verifier_doublon_visite(code_visite, code_rendez_vous_exclu)
        except Exception as e:
            self.logger.error(f"Erreur verifier_doublon_visite: {e}", exc_info=True)
            return False

    def verifier_chevauchement(self, code_personnel: str, date_rendez_vous, code_rendez_vous_exclu: str = None) -> bool:
        try:
            return self.dao.verifier_chevauchement(
                code_personnel,
                date_rendez_vous,
                code_rendez_vous_exclu
            )
        except Exception as e:
            self.logger.error(f"Erreur verifier_chevauchement: {e}", exc_info=True)
            return False

    def verifier_surcharge_personnel(
        self,
        code_personnel: str,
        code_session: str,
        date_reference=None,
        seuil_journalier: int = 12
    ) -> dict:
        try:
            return self.dao.verifier_surcharge_personnel(
                code_personnel,
                code_session,
                date_reference,
                seuil_journalier
            )
        except Exception as e:
            self.logger.error(f"Erreur verifier_surcharge_personnel: {e}", exc_info=True)
            return {"surcharge": False, "total": 0, "seuil": seuil_journalier}

    # =========================================================================
    # RECUPERATION / RECHERCHE
    # =========================================================================

    def obtenir_par_code(self, code: str):
        return self.dao.obtenir_par_code(code)

    def obtenir_par_visite(self, code_visite: str):
        return self.dao.obtenir_par_visite(code_visite)

    def obtenir_par_acte(self, code_acte: str):
        """Retourne le RDV le plus recent lie a un acte medical."""
        return self.dao.get_par_acte(code_acte)

    def lister_par_acte(self, code_acte: str) -> list:
        """Retourne tous les RDV lies a un acte medical (historique)."""
        return self.dao.lister_par_acte(code_acte)

    def planifier_rdv_pour_acte(self, rdv: RendezVous) -> tuple:
        """
        Cree un rendez-vous lie a un acte medical (code_acte renseigne).
        Validation identique a creer_rendez_vous mais sans bloquer sur doublon visite
        car un acte peut avoir plusieurs RDV dans le temps.
        """
        if not rdv.code_acte:
            return False, "Le code_acte est obligatoire pour planifier un RDV d'acte"
        return self.creer_rendez_vous(rdv)

    def lister_rendez_vous(self, code_session: str) -> list:
        return self.dao.lister_par_session(code_session)

    def lister_par_statut(self, code_session: str, statut: str) -> list:
        return self.dao.lister_par_statut(code_session, statut)

    def rechercher_rendez_vous(self, critere: str, code_session: str) -> list:
        return self.dao.rechercher_par_critere(critere, code_session)

    def rechercher_par_statut(self, code_session: str, statut: str) -> list:
        return self.dao.rechercher_par_statut(code_session, statut)

    def rechercher_par_patient(self, code_session: str, patient: str) -> list:
        return self.dao.rechercher_par_patient(code_session, patient)

    def rechercher_par_personnel(self, code_session: str, personnel: str) -> list:
        return self.dao.rechercher_par_personnel(code_session, personnel)

    def rechercher_par_date(self, code_session: str, date_rendez_vous) -> list:
        return self.dao.rechercher_par_date(code_session, date_rendez_vous)

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        return self.dao.rechercher_entre_dates(code_session, date_debut, date_fin)

    def lister_avec_filtres(
        self,
        code_session: str,
        statut: str = None,
        patient: str = None,
        personnel: str = None,
        date_debut=None,
        date_fin=None
    ) -> list:
        return self.dao.lister_avec_filtres(
            code_session,
            statut,
            patient,
            personnel,
            date_debut,
            date_fin
        )

    def obtenir_rendez_vous_complet(self, code_rdv: str):
        return self.dao.rendez_vous_complet(code_rdv)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        return self.dao.historique_patient(code_patient)

    # =========================================================================
    # TABLEAUX / LISTES
    # =========================================================================

    def obtenir_patients_attente_rendez_vous(self, code_session: str) -> list:
        return self.dao.patients_en_attente_rdv(code_session)

    def obtenir_rendez_vous_du_jour(self, code_session: str) -> list:
        return self.dao.rendez_vous_du_jour(code_session)

    def obtenir_rendez_vous_en_retard(self, code_session: str) -> list:
        return self.dao.rendez_vous_en_retard(code_session)

    def obtenir_liste_attente(self, code_session: str) -> list:
        return self.dao.lister_rdv_en_attente(code_session)

    # =========================================================================
    # MONITORING / STATISTIQUES
    # =========================================================================

    def obtenir_suivi_temps_reel(self, code_session: str) -> dict:
        return self.dao.suivi_temps_reel(code_session)

    def obtenir_total_rendez_vous_session(self, code_session: str) -> int:
        return self.dao.nombre_total_par_session(code_session)

    def obtenir_rendez_vous_aujourd_hui(self, code_session: str) -> int:
        return self.dao.nombre_rdv_aujourd_hui(code_session)

    def obtenir_rendez_vous_en_attente(self, code_session: str) -> int:
        return self.dao.nombre_rdv_en_attente(code_session)

    def obtenir_rendez_vous_confirmes(self, code_session: str) -> int:
        return self.dao.nombre_rdv_confirmes(code_session)

    def obtenir_rendez_vous_termines(self, code_session: str) -> int:
        return self.dao.nombre_rdv_termines(code_session)

    def obtenir_rendez_vous_annules(self, code_session: str) -> int:
        return self.dao.nombre_rdv_annules(code_session)

    def obtenir_rendez_vous_reportes(self, code_session: str) -> int:
        return self.dao.nombre_rdv_reportes(code_session)

    def obtenir_rendez_vous_absents(self, code_session: str) -> int:
        return self.dao.nombre_rdv_absents(code_session)

    def obtenir_nombre_rendez_vous_en_retard(self, code_session: str) -> int:
        return self.dao.nombre_rdv_en_retard(code_session)

    def obtenir_rendez_vous_par_statut(self, code_session: str) -> dict:
        return self.dao.rendez_vous_par_statut(code_session)

    def obtenir_taux_conversion(self, code_session: str) -> float:
        return self.dao.taux_conversion_presence_absence(code_session)

    def obtenir_taux_presence(self, code_session: str) -> float:
        return self.dao.taux_presence(code_session)

    def obtenir_statistiques_generales(self, code_session: str) -> dict:
        return self.dao.statistiques_generales(code_session)

    def obtenir_top_statuts(self, code_session: str, limite: int = 10) -> list:
        return self.dao.top_statuts(code_session, limite)

    def obtenir_repartition_par_statut(self, code_session: str) -> list:
        return self.dao.repartition_par_statut(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        return self.dao.revenu_total(code_session, date_debut, date_fin)

    # =========================================================================
    # CHARGE DU PERSONNEL
    # =========================================================================

    def obtenir_charge_par_personnel(self, code_session: str, date_debut=None, date_fin=None) -> list:
        return self.dao.charge_par_personnel(code_session, date_debut, date_fin)

    def obtenir_rendez_vous_par_personnel(self, code_session: str) -> list:
        return self.dao.rdv_par_personnel(code_session)

    # =========================================================================
    # ANALYSE TEMPORELLE / GRAPHIQUES
    # =========================================================================

    def obtenir_rendez_vous_par_mois(self, code_session: str) -> dict:
        return self.dao.nombre_par_mois(code_session)

    def obtenir_rendez_vous_par_semaine(self, code_session: str) -> list:
        return self.dao.nombre_par_semaine(code_session)

    def obtenir_rendez_vous_par_jour(self, code_session: str) -> list:
        return self.dao.nombre_par_jour(code_session)

    def obtenir_rendez_vous_par_heure(self, code_session: str) -> list:
        return self.dao.nombre_par_heure(code_session)

    def obtenir_jours_plus_charges(self, code_session: str, limite: int = 7) -> list:
        return self.dao.jours_plus_charges(code_session, limite)

    def obtenir_heures_plus_chargees(self, code_session: str, limite: int = 10) -> list:
        return self.dao.heures_plus_chargees(code_session, limite)

    # =========================================================================
    # ALERTES
    # =========================================================================

    def obtenir_rendez_vous_proches(self, code_session: str, delai_minutes: int = 60) -> list:
        return self.dao.rendez_vous_proches(code_session, delai_minutes)

    def obtenir_rendez_vous_oublies(self, code_session: str, marge_minutes: int = 30) -> list:
        return self.dao.rendez_vous_oublies(code_session, marge_minutes)

    def obtenir_alertes_surcharge_personnel(self, code_session: str, seuil_journalier: int = 12) -> list:
        return self.dao.alerte_surcharge_personnel(code_session, seuil_journalier)

    def obtenir_alertes_rendez_vous(self, code_session: str, delai_minutes: int = 60, seuil_journalier: int = 12) -> dict:
        return self.dao.alertes_rendez_vous(code_session, delai_minutes, seuil_journalier)

    # =========================================================================
    # PREDICTIONS
    # =========================================================================

    def predire_affluence(self, code_session: str, horizon_jours: int = 7) -> list:
        return self.dao.predire_affluence(code_session, horizon_jours)

    def predire_absence(self, code_session: str, horizon_jours: int = 7) -> list:
        return self.dao.predire_absence(code_session, horizon_jours)

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def info_cabinet(self) -> dict:
        return self.cabinet_dao.get_info_cabinet() or {}

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        """Recupere les informations du cabinet avec chemin logo resolu."""
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
            self.logger.error(f"Erreur get_cabinet_info: {e}", exc_info=True)
            return {
                "nom_cabinet": "Cabinet ophtalmologique",
                "adresse_cabinet": "",
                "logo_url": None
            }

    def lister_personnel(self) -> list:
        return self.dao.lister_personnel()

    def lister_personnel_par_roles(self, roles: list) -> list:
        from data.dao_user import UserDAO
        return UserDAO().lister_personnel_par_roles(roles)

    def rdv_du_jour_sans_acte(self, code_session: str) -> list:
        return self.dao.rdv_du_jour_sans_acte(code_session)

    def traiter_rdv_arrive(self, code_rdv: str, action: str, nouvelle_date=None) -> tuple:
        """
        Traite un RDV de première visite (sans acte) selon l'action choisie par le médecin.
        action:
          'consultation' → passe la visite en 'Attente consultation', clôture le RDV
          'annuler'      → supprime le RDV ET la visite associée
          'reporter'     → repousse le RDV à nouvelle_date, statut revient à 'attente'
        """
        rdv = self.dao.obtenir_par_code(code_rdv)
        if not rdv:
            return False, "Rendez-vous introuvable"

        code_visite = rdv.code_visite

        if action == 'consultation':
            ok = self.dao.changer_statut_rendez_vous(code_rdv, 'traite')
            if not ok:
                return False, "Impossible de mettre à jour le statut du RDV"
            from data.dao_visite import Visitedao
            visite_dao = Visitedao()
            conn = visite_dao.db_manager.connect()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE visite SET statut_patient = 'Attente consultation' WHERE code_visite = %s",
                            (code_visite,)
                        )
                        conn.commit()
                finally:
                    conn.close()
            return True, "Patient envoyé en attente de consultation"

        elif action == 'annuler':
            ok, msg = self.supprimer_rendez_vous(code_rdv)
            if not ok:
                return False, msg
            from data.dao_visite import Visitedao
            Visitedao().deleteVisite(code_visite)
            return True, "Rendez-vous annulé et visite supprimée"

        elif action == 'reporter':
            if not nouvelle_date:
                return False, "Nouvelle date requise pour reporter"
            from data.dao_visite import Visitedao
            rdv.date_rendez_vous = nouvelle_date
            rdv.statut_rendez_vous = 'attente'
            ok = self.dao.modifier(rdv)
            if ok:
                return True, "Rendez-vous reporté avec succès"
            return False, "Impossible de reporter le rendez-vous"

        return False, f"Action inconnue : {action}"

    def lister_actes_en_attente_rdv(self, code_session: str) -> list:
        """Retourne les actes médicaux avec choix_patient='plus_tard' pour cette session."""
        try:
            from data.dao_acte_medicale import ActeMedicalDAO
            return ActeMedicalDAO().lister_actes_en_attente_rdv_par_session(code_session)
        except Exception as e:
            self.logger.warning("Erreur lister_actes_en_attente_rdv: %s", e)
            return []
