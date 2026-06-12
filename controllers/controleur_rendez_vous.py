import sys
import os
import logging
from typing import Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.modele_rendez_vous import RendezVous
from service_metier.rendez_vous_service import RendezVousService


class RendezVousControleur:
    """
    Controleur MVC pour la gestion des rendez-vous.
    Fait le lien entre les vues et le service metier.
    """

    def __init__(self, service=None):
        self.service = service or RendezVousService()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def valider_texte(self, texte: str, nom_champ: str, min_longueur: int = 1) -> tuple:
        return self.service.valider_texte(texte, nom_champ, min_longueur)

    def valider_statut(self, statut: str) -> tuple:
        return self.service.valider_statut(statut)

    def valider_date(self, date_rendez_vous) -> tuple:
        return self.service.valider_date(date_rendez_vous)

    def valider_codes_obligatoires(self, rdv: RendezVous) -> tuple:
        return self.service.valider_codes_obligatoires(rdv)

    def valider_rendez_vous(self, rdv: RendezVous) -> tuple:
        return self.service.valider_rendez_vous(rdv)

    # =========================================================================
    # CRUD
    # =========================================================================

    def generer_code_rendez_vous(self) -> str:
        return self.service.generer_code_rendez_vous()

    def creer_rendez_vous(self, rdv: RendezVous) -> tuple:
        return self.service.creer_rendez_vous(rdv)

    def modifier_rendez_vous(self, rdv: RendezVous) -> tuple:
        return self.service.modifier_rendez_vous(rdv)

    def supprimer_rendez_vous(self, code: str) -> tuple:
        return self.service.supprimer_rendez_vous(code)

    def changer_statut_rendez_vous(self, code_rendez_vous: str, nouveau_statut: str, code_session: str = None) -> tuple:
        return self.service.changer_statut_rendez_vous(code_rendez_vous, nouveau_statut, code_session)

    def changer_statut(self, code_rendez_vous: str, nouveau_statut: str, code_session: str = None) -> tuple:
        return self.service.changer_statut(code_rendez_vous, nouveau_statut, code_session)

    # =========================================================================
    # PLANIFICATION
    # =========================================================================

    def verifier_disponibilite_personnel(self, code_personnel: str, date_rendez_vous, code_rendez_vous_exclu: str = None) -> bool:
        return self.service.verifier_disponibilite_personnel(
            code_personnel,
            date_rendez_vous,
            code_rendez_vous_exclu
        )

    def verifier_doublon_visite(self, code_visite: str, code_rendez_vous_exclu: str = None) -> bool:
        return self.service.verifier_doublon_visite(code_visite, code_rendez_vous_exclu)

    def verifier_chevauchement(self, code_personnel: str, date_rendez_vous, code_rendez_vous_exclu: str = None) -> bool:
        return self.service.verifier_chevauchement(
            code_personnel,
            date_rendez_vous,
            code_rendez_vous_exclu
        )

    def verifier_surcharge_personnel(
        self,
        code_personnel: str,
        code_session: str,
        date_reference=None,
        seuil_journalier: int = 12
    ) -> dict:
        return self.service.verifier_surcharge_personnel(
            code_personnel,
            code_session,
            date_reference,
            seuil_journalier
        )

    # =========================================================================
    # RECUPERATION / RECHERCHE
    # =========================================================================

    def obtenir_par_code(self, code: str):
        return self.service.obtenir_par_code(code)

    def obtenir_par_visite(self, code_visite: str):
        return self.service.obtenir_par_visite(code_visite)

    def obtenir_par_acte(self, code_acte: str):
        """Retourne le RDV le plus recent lie a un acte medical."""
        return self.service.obtenir_par_acte(code_acte)

    def lister_par_acte(self, code_acte: str) -> list:
        """Retourne tous les RDV lies a un acte medical (historique)."""
        return self.service.lister_par_acte(code_acte)

    def planifier_rdv_pour_acte(self, rdv) -> tuple:
        """Cree un RDV lie a un acte medical."""
        return self.service.planifier_rdv_pour_acte(rdv)

    def traiter_rdv_du_jour(self, code_session: str) -> int:
        """Place automatiquement en file d'attente les patients dont le RDV est arrivé."""
        return self.service.dao.traiter_rdv_du_jour(code_session)

    def lister_rdv_en_cours(self, code_session: str) -> list:
        """Retourne les RDV actifs (attente/confirme/en_cours) enrichis avec type_acte."""
        return self.service.dao.lister_en_cours(code_session)

    def lister_rendez_vous(self, code_session: str) -> list:
        return self.service.lister_rendez_vous(code_session)

    def lister_par_statut(self, code_session: str, statut: str) -> list:
        return self.service.lister_par_statut(code_session, statut)

    def rechercher_rendez_vous(self, critere: str, code_session: str) -> list:
        return self.service.rechercher_rendez_vous(critere, code_session)

    def rechercher_par_statut(self, code_session: str, statut: str) -> list:
        return self.service.rechercher_par_statut(code_session, statut)

    def rechercher_par_patient(self, code_session: str, patient: str) -> list:
        return self.service.rechercher_par_patient(code_session, patient)

    def rechercher_par_personnel(self, code_session: str, personnel: str) -> list:
        return self.service.rechercher_par_personnel(code_session, personnel)

    def rechercher_par_date(self, code_session: str, date_rendez_vous) -> list:
        return self.service.rechercher_par_date(code_session, date_rendez_vous)

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        return self.service.rechercher_entre_dates(code_session, date_debut, date_fin)

    def lister_avec_filtres(
        self,
        code_session: str,
        statut: str = None,
        patient: str = None,
        personnel: str = None,
        date_debut=None,
        date_fin=None
    ) -> list:
        return self.service.lister_avec_filtres(
            code_session,
            statut,
            patient,
            personnel,
            date_debut,
            date_fin
        )

    def obtenir_rendez_vous_complet(self, code_rdv: str):
        return self.service.obtenir_rendez_vous_complet(code_rdv)

    def obtenir_historique_patient(self, code_patient: str) -> list:
        return self.service.obtenir_historique_patient(code_patient)

    # =========================================================================
    # TABLEAUX / LISTES
    # =========================================================================

    def obtenir_patients_attente_rendez_vous(self, code_session: str) -> list:
        return self.service.obtenir_patients_attente_rendez_vous(code_session)

    def obtenir_rendez_vous_du_jour(self, code_session: str) -> list:
        return self.service.obtenir_rendez_vous_du_jour(code_session)

    def obtenir_rendez_vous_en_retard(self, code_session: str) -> list:
        return self.service.obtenir_rendez_vous_en_retard(code_session)

    def obtenir_liste_attente(self, code_session: str) -> list:
        return self.service.obtenir_liste_attente(code_session)

    # =========================================================================
    # MONITORING / STATISTIQUES
    # =========================================================================

    def obtenir_suivi_temps_reel(self, code_session: str) -> dict:
        return self.service.obtenir_suivi_temps_reel(code_session)

    def obtenir_total_rendez_vous_session(self, code_session: str) -> int:
        return self.service.obtenir_total_rendez_vous_session(code_session)

    def obtenir_rendez_vous_aujourd_hui(self, code_session: str) -> int:
        return self.service.obtenir_rendez_vous_aujourd_hui(code_session)

    def obtenir_rendez_vous_en_attente(self, code_session: str) -> int:
        return self.service.obtenir_rendez_vous_en_attente(code_session)

    def obtenir_rendez_vous_confirmes(self, code_session: str) -> int:
        return self.service.obtenir_rendez_vous_confirmes(code_session)

    def obtenir_rendez_vous_termines(self, code_session: str) -> int:
        return self.service.obtenir_rendez_vous_termines(code_session)

    def obtenir_rendez_vous_annules(self, code_session: str) -> int:
        return self.service.obtenir_rendez_vous_annules(code_session)

    def obtenir_rendez_vous_reportes(self, code_session: str) -> int:
        return self.service.obtenir_rendez_vous_reportes(code_session)

    def obtenir_rendez_vous_absents(self, code_session: str) -> int:
        return self.service.obtenir_rendez_vous_absents(code_session)

    def obtenir_nombre_rendez_vous_en_retard(self, code_session: str) -> int:
        return self.service.obtenir_nombre_rendez_vous_en_retard(code_session)

    def obtenir_rendez_vous_par_statut(self, code_session: str) -> dict:
        return self.service.obtenir_rendez_vous_par_statut(code_session)

    def obtenir_taux_conversion(self, code_session: str) -> float:
        return self.service.obtenir_taux_conversion(code_session)

    def obtenir_taux_presence(self, code_session: str) -> float:
        return self.service.obtenir_taux_presence(code_session)

    def obtenir_statistiques_generales(self, code_session: str) -> dict:
        return self.service.obtenir_statistiques_generales(code_session)

    def obtenir_top_statuts(self, code_session: str, limite: int = 10) -> list:
        return self.service.obtenir_top_statuts(code_session, limite)

    def obtenir_repartition_par_statut(self, code_session: str) -> list:
        return self.service.obtenir_repartition_par_statut(code_session)

    def obtenir_revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        return self.service.obtenir_revenu_total(code_session, date_debut, date_fin)

    # =========================================================================
    # CHARGE DU PERSONNEL
    # =========================================================================

    def obtenir_charge_par_personnel(self, code_session: str, date_debut=None, date_fin=None) -> list:
        return self.service.obtenir_charge_par_personnel(code_session, date_debut, date_fin)

    def obtenir_rendez_vous_par_personnel(self, code_session: str) -> list:
        return self.service.obtenir_rendez_vous_par_personnel(code_session)

    # =========================================================================
    # ANALYSE TEMPORELLE / GRAPHIQUES
    # =========================================================================

    def obtenir_rendez_vous_par_mois(self, code_session: str) -> dict:
        return self.service.obtenir_rendez_vous_par_mois(code_session)

    def obtenir_rendez_vous_par_semaine(self, code_session: str) -> list:
        return self.service.obtenir_rendez_vous_par_semaine(code_session)

    def obtenir_rendez_vous_par_jour(self, code_session: str) -> list:
        return self.service.obtenir_rendez_vous_par_jour(code_session)

    def obtenir_rendez_vous_par_heure(self, code_session: str) -> list:
        return self.service.obtenir_rendez_vous_par_heure(code_session)

    def obtenir_jours_plus_charges(self, code_session: str, limite: int = 7) -> list:
        return self.service.obtenir_jours_plus_charges(code_session, limite)

    def obtenir_heures_plus_chargees(self, code_session: str, limite: int = 10) -> list:
        return self.service.obtenir_heures_plus_chargees(code_session, limite)

    # =========================================================================
    # ALERTES
    # =========================================================================

    def obtenir_rendez_vous_proches(self, code_session: str, delai_minutes: int = 60) -> list:
        return self.service.obtenir_rendez_vous_proches(code_session, delai_minutes)

    def obtenir_rendez_vous_oublies(self, code_session: str, marge_minutes: int = 30) -> list:
        return self.service.obtenir_rendez_vous_oublies(code_session, marge_minutes)

    def obtenir_alertes_surcharge_personnel(self, code_session: str, seuil_journalier: int = 12) -> list:
        return self.service.obtenir_alertes_surcharge_personnel(code_session, seuil_journalier)

    def obtenir_alertes_rendez_vous(self, code_session: str, delai_minutes: int = 60, seuil_journalier: int = 12) -> dict:
        return self.service.obtenir_alertes_rendez_vous(code_session, delai_minutes, seuil_journalier)

    # =========================================================================
    # PREDICTIONS
    # =========================================================================

    def predire_affluence(self, code_session: str, horizon_jours: int = 7) -> list:
        return self.service.predire_affluence(code_session, horizon_jours)

    def predire_absence(self, code_session: str, horizon_jours: int = 7) -> list:
        return self.service.predire_absence(code_session, horizon_jours)

    # =========================================================================
    # INFORMATIONS CABINET
    # =========================================================================

    def info_cabinet(self) -> dict:
        return self.service.info_cabinet()

    def get_cabinet_info(self) -> Dict[str, Optional[str]]:
        return self.service.get_cabinet_info()

    def lister_personnel(self) -> list:
        return self.service.lister_personnel()

    def lister_personnel_par_roles(self, roles: list) -> list:
        return self.service.lister_personnel_par_roles(roles)

    def rdv_du_jour_sans_acte(self, code_session: str) -> list:
        return self.service.rdv_du_jour_sans_acte(code_session)

    def traiter_rdv_arrive(self, code_rdv: str, action: str, nouvelle_date=None) -> tuple:
        return self.service.traiter_rdv_arrive(code_rdv, action, nouvelle_date)

    def lister_actes_en_attente_rdv(self, code_session: str) -> list:
        """Retourne les actes médicaux avec choix_patient='plus_tard' pour cette session."""
        return self.service.lister_actes_en_attente_rdv(code_session)
