"""
parcours_patient_service.py
----------------------------
Service métier — Analytics et parcours patient.

Responsabilités :
  - Reconstituer le parcours complet d'une visite
  - Calculer les durées (attente, exécution, totale) par acte et par visite
  - Générer un tableau de bord global (KPIs)
  - Détecter les anomalies de parcours
"""

import logging
from datetime import datetime
from typing import Optional

from data.dao_acte_medicale import ActeMedicalDAO, StatutActe
from data.dao_acte_visite import ActeVisiteDAO


class ParcoursPatientService:
    """
    Analytics et suivi du parcours patient.
    Aucune écriture DB — lecture seule depuis acte_medical et acte_visite.
    """

    def __init__(self,
                 dao_acte: ActeMedicalDAO = None,
                 dao_visite: ActeVisiteDAO = None):
        self.dao_acte   = dao_acte   or ActeMedicalDAO()
        self.dao_visite = dao_visite or ActeVisiteDAO()
        self.logger     = logging.getLogger(__name__)

    # =========================================================================
    # SECTION 1 — PARCOURS D'UNE VISITE
    # =========================================================================

    def obtenir_parcours(self, code_consultation: str) -> list:
        """
        Retourne le parcours ordonné d'une consultation :
        liste d'actes avec, pour chaque acte, la liste de ses passages.
        Format : [
          {
            "acte": ActeMedical,
            "passages": [ActeVisite, ...],
            "durees": {"attente_min": ..., "execution_min": ..., "totale_min": ...}
          }, ...
        ]
        """
        actes = self.dao_acte.lister_par_consultation(code_consultation)
        parcours = []
        for acte in actes:
            passages = self.dao_visite.get_visites_par_acte(acte.id_acte)
            durees   = self._calculer_durees_acte(passages)
            parcours.append({
                "acte":     acte,
                "passages": passages,
                "durees":   durees,
            })
        return parcours

    def obtenir_etat_global(self, code_consultation: str) -> dict:
        """
        Vue synthétique d'une consultation :
        - actes par statut
        - durée totale estimée
        - acte en cours (le cas échéant)
        """
        actes = self.dao_acte.lister_par_consultation(code_consultation)
        par_statut = {}
        acte_en_cours = None
        duree_totale_min = 0

        for acte in actes:
            statut = acte.statut_acte
            par_statut.setdefault(statut, []).append(acte)

            if statut == StatutActe.EN_COURS:
                acte_en_cours = acte

            passages = self.dao_visite.get_visites_par_acte(acte.id_acte)
            durees   = self._calculer_durees_acte(passages)
            if durees.get("totale_min") is not None:
                duree_totale_min += durees["totale_min"]

        return {
            "code_consultation": code_consultation,
            "nb_actes":          len(actes),
            "par_statut":        {k: len(v) for k, v in par_statut.items()},
            "acte_en_cours":     acte_en_cours,
            "duree_totale_min":  duree_totale_min,
            "horodatage":        datetime.now().isoformat(),
        }

    # =========================================================================
    # SECTION 2 — DURÉES
    # =========================================================================

    def obtenir_durees_acte(self, id_acte: int) -> dict:
        """Retourne les durées (attente / exécution / totale) pour un acte."""
        passages = self.dao_visite.get_visites_par_acte(id_acte)
        return self._calculer_durees_acte(passages)

    def obtenir_durees_passage(self, id_acte_visite: int) -> dict:
        """Délègue le calcul au DAO (utilise le modèle ActeVisite)."""
        return self.dao_visite.get_durees(id_acte_visite)

    def _calculer_durees_acte(self, passages: list) -> dict:
        """
        Agrège les durées de tous les passages d'un acte.
        Retourne la somme des durées d'attente et d'exécution,
        et la durée totale (de la première entrée à la dernière sortie).
        """
        if not passages:
            return {"attente_min": None, "execution_min": None, "totale_min": None}

        total_attente   = 0
        total_execution = 0
        premiere_entree = None
        derniere_sortie = None

        for av in passages:
            d = av.duree_attente_minutes()
            if d is not None:
                total_attente += d
            d = av.duree_execution_minutes()
            if d is not None:
                total_execution += d

            if av.date_entree:
                if premiere_entree is None or av.date_entree < premiere_entree:
                    premiere_entree = av.date_entree
            if av.date_sortie:
                if derniere_sortie is None or av.date_sortie > derniere_sortie:
                    derniere_sortie = av.date_sortie

        totale = None
        if premiere_entree and derniere_sortie:
            totale = int((derniere_sortie - premiere_entree).total_seconds() / 60)

        return {
            "attente_min":   total_attente   or None,
            "execution_min": total_execution or None,
            "totale_min":    totale,
        }

    # =========================================================================
    # SECTION 3 — TABLEAU DE BORD
    # =========================================================================

    def dashboard_global(self) -> dict:
        """
        KPIs globaux en temps réel :
        - Tailles des files d'attente par service
        - Nombre de passages en cours
        - Nombre d'actes par statut (snapshot)
        - Horodatage
        """
        from data.dao_acte_visite import RoleVisite, StatutPassage

        files = {}
        en_cours_par_service = {}

        from data.dao_acte_medicale import TypeActe
        for ta in [TypeActe.EXAMEN, TypeActe.CHIRURGIE,
                   TypeActe.LUNETTE, TypeActe.PRESCRIPTION]:
            file     = self.dao_visite.get_file_attente(ta)
            en_cours = self.dao_visite.get_en_cours(ta)
            files[ta]               = len(file)
            en_cours_par_service[ta] = len(en_cours)

        nb_actes_par_statut = {}
        for statut in [StatutActe.EN_ATTENTE, StatutActe.PLANIFIE,
                       StatutActe.EN_COURS, StatutActe.TERMINE, StatutActe.REFUSE]:
            actes = self.dao_acte.lister_par_statut(statut)
            nb_actes_par_statut[statut] = len(actes)

        return {
            "files_attente":        files,
            "en_cours_par_service": en_cours_par_service,
            "actes_par_statut":     nb_actes_par_statut,
            "horodatage":           datetime.now().isoformat(),
        }

    # =========================================================================
    # SECTION 4 — DÉTECTION D'ANOMALIES
    # =========================================================================

    def detecter_anomalies(self) -> dict:
        """
        Détecte les incohérences dans les parcours :
        - Actes en_cours sans passage actif dans acte_visite
        - Passages en_cours depuis plus de 3h (blocage probable)
        - Actes planifiés sans aucun passage enregistré
        Retourne un rapport avec le score de santé (0-100).
        """
        anomalies = {
            "actes_en_cours_sans_passage":  [],
            "passages_bloques":             [],
            "actes_planifies_sans_passage": [],
        }

        # Actes en_cours sans passage actif
        actes_en_cours = self.dao_acte.lister_par_statut(StatutActe.EN_COURS)
        for acte in actes_en_cours:
            passage = self.dao_visite.get_passage_actif(acte.id_acte)
            if not passage:
                anomalies["actes_en_cours_sans_passage"].append(acte.id_acte)

        # Passages en_cours depuis plus de 3h
        from datetime import timedelta
        seuil_blocage = timedelta(hours=3)
        maintenant = datetime.now()
        passages_actifs = self.dao_visite.get_en_cours()
        for av in passages_actifs:
            if av.date_debut_execution:
                duree = maintenant - av.date_debut_execution
                if duree > seuil_blocage:
                    anomalies["passages_bloques"].append({
                        "id_acte_visite":   av.id_acte_visite,
                        "code_acte":        av.code_acte,
                        "duree_minutes":    int(duree.total_seconds() / 60),
                    })

        # Actes planifiés sans passage enregistré
        actes_planifies = self.dao_acte.lister_par_statut(StatutActe.PLANIFIE)
        for acte in actes_planifies:
            passages = self.dao_visite.get_visites_par_acte(acte.id_acte)
            if not passages:
                anomalies["actes_planifies_sans_passage"].append(acte.id_acte)

        total_problemes = (
            len(anomalies["actes_en_cours_sans_passage"]) +
            len(anomalies["passages_bloques"]) +
            len(anomalies["actes_planifies_sans_passage"])
        )
        score_sante = max(0, 100 - total_problemes * 10)

        return {
            "anomalies":     anomalies,
            "nb_problemes":  total_problemes,
            "score_sante":   score_sante,
            "horodatage":    datetime.now().isoformat(),
        }
