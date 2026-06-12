"""
acte_medicale_service.py
------------------------
Service métier — Gestion des actes médicaux.

Responsabilités :
  - Validation des données d'un acte médical
  - CRUD : création, modification, suppression
  - Workflow : transitions d'états (machine à états)
  - Gestion du choix patient (maintenant / plus_tard / ailleurs)
  - Liaison parent-enfant entre actes

Notes :
  File d'attente  -> FileAttenteService + ActeVisiteDAO
  Durées/Analytics -> ParcoursPatientService
"""

import logging
import re
from datetime import datetime
from typing import Optional

from data.dao_acte_medicale import (
    ActeMedicalDAO, StatutActe, ChoixPatient, TypeActe, ModeRealisation
)
from data.dao_consultation import ConsultationDAO
from data.dao_visite import Visitedao
from data.dao_personnel import PersonnelDAO
from data.dao_rendez_vous import RendezVousDAO
from models.modele_rendez_vous import RendezVous
from models.model_acte_medicale import ActeMedical


class ActeMedicalService:
    """
    Service métier pour la gestion complète des actes médicaux.
    Orchestre validation, workflow, files d'attente, facturation et analytics.
    """

    def __init__(self, dao: ActeMedicalDAO = None, consultation_dao=None,
                 visite_dao=None, personnel_dao=None):
        self.dao              = dao or ActeMedicalDAO()
        self.consultation_dao = consultation_dao or ConsultationDAO()
        self.visite_dao       = visite_dao or Visitedao()
        self.personnel_dao    = personnel_dao or PersonnelDAO()
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # SECTION 1 — VALIDATION (LOGIQUE MÉTIER)
    # =========================================================================

    def valider_type_acte(self, type_acte: str) -> tuple:
        """Valide que le type d'acte appartient aux valeurs autorisées."""
        valeurs = [TypeActe.EXAMEN, TypeActe.CHIRURGIE,
                   TypeActe.LUNETTE, TypeActe.PRESCRIPTION]
        if not type_acte or type_acte not in valeurs:
            return False, f"Type d'acte invalide. Valeurs acceptées : {', '.join(valeurs)}"
        return True, ""

    def valider_decision_medicale(self, decision: str) -> tuple:
        """Valide qu'une décision médicale est renseignée et lisible."""
        if not decision or decision.strip() == "":
            return False, "La décision médicale est obligatoire"
        if len(decision.strip()) < 3:
            return False, "La décision médicale doit contenir au moins 3 caractères"
        if re.search(r'[<>{}[\]\\|`~]', decision):
            return False, "La décision médicale contient des caractères spéciaux interdits"
        return True, ""

    def valider_choix_patient(self, choix: str) -> tuple:
        """Valide que le choix patient est une valeur métier reconnue."""
        valeurs = [ChoixPatient.MAINTENANT, ChoixPatient.PLUS_TARD, ChoixPatient.AILLEURS]
        if choix not in valeurs:
            return False, f"Choix patient invalide. Valeurs acceptées : {', '.join(valeurs)}"
        return True, ""

    def valider_date_rdv(self, date_rdv) -> tuple:
        """Valide qu'une date de rendez-vous est dans le futur."""
        if not date_rdv:
            return False, "La date de rendez-vous est obligatoire"
        try:
            if isinstance(date_rdv, str):
                date_rdv = datetime.strptime(date_rdv, "%Y-%m-%d %H:%M:%S")
            if date_rdv <= datetime.now():
                return False, "La date de rendez-vous doit être dans le futur"
            return True, ""
        except Exception:
            return False, "Format de date invalide (attendu : YYYY-MM-DD HH:MM:SS)"

    def valider_code_consultation(self, code_consultation: str) -> tuple:
        """Valide que le code consultation est renseigné."""
        if not code_consultation or not code_consultation.strip():
            return False, "Le code consultation est obligatoire"
        return True, ""

    def valider_acte(self, acte: ActeMedical) -> tuple:
        """Validation complète d'un objet ActeMedical avant persistance."""
        valide, msg = self.valider_type_acte(acte.type_acte)
        if not valide:
            return False, msg
        valide, msg = self.valider_decision_medicale(acte.decision_medicale)
        if not valide:
            return False, msg
        valide, msg = self.valider_code_consultation(acte.code_consultation)
        if not valide:
            return False, msg
        return True, ""

    def _nettoyer_acte(self, acte: ActeMedical) -> None:
        """Supprime les espaces superflus des champs texte."""
        if acte.decision_medicale:
            acte.decision_medicale = acte.decision_medicale.strip()
        if acte.raison_refus:
            acte.raison_refus = acte.raison_refus.strip()

    # =========================================================================
    # SECTION 2 — CRUD
    # =========================================================================

    def creer_acte(self, acte: ActeMedical) -> tuple:
        """Valide et persiste un nouvel acte médical. Retourne (succès, message, acte_avec_code)."""
        valide, msg = self.valider_acte(acte)
        if not valide:
            return False, msg, None
        self._nettoyer_acte(acte)
        try:
            resultat = self.dao.ajouter(acte)
            if resultat:
                self.logger.info(f"Acte {acte.id_acte} ({acte.type_acte}) créé")
                
                # Créer automatiquement la liaison acte_visite
                # Si choix_patient n'est pas défini, on considère que c'est 'maintenant' par défaut
                if not acte.choix_patient or acte.choix_patient == ChoixPatient.MAINTENANT:
                    self._creer_liaison_acte_visite(acte)
                elif acte.choix_patient == ChoixPatient.PLUS_TARD:
                    # Mettre le patient en "Attente rendez-vous"
                    self._mettre_patient_attente_rdv(acte)
                elif acte.choix_patient == ChoixPatient.AILLEURS:
                    # L'acte sera fait ailleurs (externe) : la consultation est terminée,
                    # le patient peut aller en paiement ou prendre un autre acte
                    self._mettre_patient_consultation_terminee(acte)
                
                return True, "Acte médical créé avec succès", acte
            return False, "Erreur lors de la création de l'acte médical", None
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'acte: {str(e)}")
            return False, str(e), None
    
    def _creer_liaison_acte_visite(self, acte: ActeMedical) -> bool:
        """
        Crée automatiquement la liaison acte_visite pour mettre le patient en file d'attente.
        Récupère le code_visite depuis la consultation et met à jour le statut du patient.
        Toutes les opérations sont faites dans la même transaction.
        """
        from core.connexion_db import DBConnection
        from datetime import datetime
        
        db = DBConnection()
        conn = db.connect()
        if not conn:
            self.logger.warning(f"Impossible de créer liaison acte_visite pour acte {acte.id_acte}: connexion DB échouée")
            return False
        
        try:
            cursor = conn.cursor()
            
            # 1. Récupérer le code_visite depuis la consultation
            cursor.execute(
                "SELECT code_visite FROM consultation WHERE code = %s",
                (acte.code_consultation,)
            )
            row = cursor.fetchone()
            if not row:
                self.logger.warning(f"Code visite introuvable pour consultation {acte.code_consultation}")
                return False
            
            code_visite = row[0] if isinstance(row, tuple) else row.get('code_visite')
            self.logger.info(f"Code visite récupéré: {code_visite} pour consultation {acte.code_consultation}")
            
            # 2. Créer la liaison acte_visite
            cursor.execute("""
                INSERT INTO acte_visite (
                    code_acte, code_visite, role_visite, date_liaison, date_entre
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                acte.id_acte,
                code_visite,
                "execution",
                datetime.now(),
                datetime.now()  # Enregistrer directement l'entrée en file
            ))
            
            self.logger.info(f"Liaison acte_visite créée: acte={acte.id_acte}, visite={code_visite}")
            
            # 3. Mettre à jour le statut du patient
            statut_map = {
                TypeActe.EXAMEN: "Attente examen",
                TypeActe.CHIRURGIE: "Attente chirurgie",
                TypeActe.LUNETTE: "Attente lunette",
                TypeActe.PRESCRIPTION: "Attente pharmacie"
            }
            nouveau_statut = statut_map.get(acte.type_acte, "Attente examen")
            
            # Vérifier le statut actuel
            cursor.execute(
                "SELECT statut_patient FROM visite WHERE code_visite = %s",
                (code_visite,)
            )
            row = cursor.fetchone()
            if row:
                statut_actuel = row[0] if isinstance(row, tuple) else row.get('statut_patient')
                self.logger.info(f"Changement statut: '{statut_actuel}' -> '{nouveau_statut}' pour visite {code_visite}")
            
            cursor.execute(
                "UPDATE visite SET statut_patient = %s WHERE code_visite = %s",
                (nouveau_statut, code_visite)
            )
            
            # 4. Commit de toute la transaction
            conn.commit()
            self.logger.info(f"✅ Transaction complète: acte_visite créé et statut mis à jour pour visite {code_visite}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur _creer_liaison_acte_visite: {e}")
            conn.rollback()
            return False
        finally:
            db.close()

    def _mettre_patient_attente_rdv(self, acte: ActeMedical) -> bool:
        """
        Lors d'un choix 'plus_tard', met le patient en statut 'Attente rendez-vous'
        ET crée la liaison acte_visite(role='origine') pour tracer la prescription.
        """
        from core.connexion_db import DBConnection
        from datetime import datetime
        db = DBConnection()
        conn = db.connect()
        if not conn:
            self.logger.warning(f"Impossible de mettre patient en Attente rendez-vous pour acte {acte.id_acte}")
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT code_visite FROM consultation WHERE code = %s",
                (acte.code_consultation,)
            )
            row = cursor.fetchone()
            if not row:
                return False
            code_visite = row[0] if isinstance(row, tuple) else row.get('code_visite')

            # Mettre le patient en "Attente rendez-vous [type_acte]" :
            # il apparaîtra dans le combo de la vue rendez-vous pour que
            # le secrétaire puisse lui créer un RDV.
            statut_map = {
                TypeActe.EXAMEN: "Attente rendez-vous examen",
                TypeActe.CHIRURGIE: "Attente rendez-vous chirurgie",
                TypeActe.LUNETTE: "Attente rendez-vous lunette",
                TypeActe.PRESCRIPTION: "Attente rendez-vous pharmacie"
            }
            nouveau_statut = statut_map.get(acte.type_acte, "Attente rendez-vous")
            cursor.execute(
                "UPDATE visite SET statut_patient = %s WHERE code_visite = %s",
                (nouveau_statut, code_visite)
            )

            # Créer acte_visite(role='origine') si pas déjà présent
            cursor.execute("""
                SELECT 1 FROM acte_visite
                WHERE code_acte = %s AND code_visite = %s AND role_visite = 'origine'
                LIMIT 1
            """, (acte.id_acte, code_visite))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO acte_visite (code_acte, code_visite, role_visite, date_liaison)
                    VALUES (%s, %s, 'origine', %s)
                """, (acte.id_acte, code_visite, datetime.now()))
                self.logger.info(f"acte_visite(origine) créé: acte={acte.id_acte}, visite={code_visite}")

            conn.commit()
            self.logger.info(f"Patient visite {code_visite} passé en Attente rendez-vous (acte {acte.id_acte})")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur _mettre_patient_attente_rdv: {e}")
            conn.rollback()
            return False
        finally:
            db.close()

    def _mettre_patient_consultation_terminee(self, acte: ActeMedical) -> bool:
        """
        Lors d'un choix 'ailleurs', l'acte sera réalisé en dehors du cabinet.
        La consultation est considérée terminée → le patient peut aller en paiement
        (pour la consultation) ou prescrire un autre acte.
        """
        from core.connexion_db import DBConnection
        db = DBConnection()
        conn = db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT code_visite FROM consultation WHERE code = %s",
                (acte.code_consultation,)
            )
            row = cursor.fetchone()
            if not row:
                return False
            code_visite = row[0] if isinstance(row, tuple) else row.get('code_visite')
            # Si mode externe → aller directement en Attente payement (acte fait hors cabinet)
            if getattr(acte, 'mode_realisation', None) == 'externe':
                nouveau_statut = 'Attente payement'
            else:
                nouveau_statut = 'Consultation terminée'
            cursor.execute(
                "UPDATE visite SET statut_patient = %s WHERE code_visite = %s",
                (nouveau_statut, code_visite,)
            )
            conn.commit()
            self.logger.info(f"Patient visite {code_visite} passé en '{nouveau_statut}' (acte ailleurs {acte.id_acte})")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erreur _mettre_patient_consultation_terminee: {e}")
            conn.rollback()
            return False
        finally:
            db.close()

    def creer_acte_intelligent(self, code_consultation: str,
                                type_acte: str,
                                decision_medicale: str,
                                source_acte: str = "consultation") -> tuple:
        """
        Crée un acte médical via la factory du DAO.
        Valide les paramètres avant délégation.
        """
        valide, msg = self.valider_type_acte(type_acte)
        if not valide:
            return None, msg
        valide, msg = self.valider_decision_medicale(decision_medicale)
        if not valide:
            return None, msg
        valide, msg = self.valider_code_consultation(code_consultation)
        if not valide:
            return None, msg

        acte = self.dao.create_acte(
            code_consultation   = code_consultation,
            type_acte           = type_acte,
            decision_medicale   = decision_medicale,
        )
        if acte:
            self.logger.info(f"Acte intelligent {acte.id_acte} créé ({type_acte})")
            return acte, "Acte créé avec succès"
        return None, "Erreur lors de la création de l'acte"

    def creer_actes_depuis_recommandations(self, code_consultation: str,
                                            recommandations: list) -> tuple:
        """
        Crée plusieurs actes à partir d'une liste de recommandations médicales.
        Format : [{"type_acte": "examen", "decision_medicale": "..."}, ...]
        """
        if not recommandations:
            return [], "Aucune recommandation fournie"
        valide, msg = self.valider_code_consultation(code_consultation)
        if not valide:
            return [], msg

        for reco in recommandations:
            valide, msg = self.valider_type_acte(reco.get("type_acte", ""))
            if not valide:
                return [], f"Recommandation invalide : {msg}"

        crees = self.dao.create_actes_depuis_recommandations(code_consultation, recommandations)
        self.logger.info(f"{len(crees)} acte(s) créés depuis recommandations")
        return crees, f"{len(crees)} acte(s) créé(s) avec succès"

    def modifier_acte(self, acte: ActeMedical) -> tuple:
        """Valide et met à jour un acte médical existant."""
        if not acte.id_acte:
            return False, "L'identifiant de l'acte est obligatoire pour la modification"
        valide, msg = self.valider_acte(acte)
        if not valide:
            return False, msg
        self._nettoyer_acte(acte)
        if self.dao.modifier(acte):
            self.logger.info(f"Acte {acte.id_acte} modifié")
            return True, "Acte médical modifié avec succès"
        return False, "Erreur lors de la modification de l'acte médical"

    def supprimer_acte(self, code_acte: str) -> tuple:
        """Supprime un acte médical. Refuse si l'acte est en cours."""
        if not code_acte:
            return False, "Identifiant d'acte invalide"
        acte = self.dao.obtenir_par_id(code_acte)
        if not acte:
            return False, "Acte introuvable"
        if acte.statut_acte == StatutActe.EN_COURS:
            return False, "Impossible de supprimer un acte en cours d'exécution"
        if self.dao.supprimer(code_acte):
            self.logger.info(f"Acte {code_acte} supprimé")
            return True, "Acte médical supprimé avec succès"
        return False, "Erreur lors de la suppression de l'acte médical"

    def lier_acte_parent(self, code_acte_child: str, code_acte_parent: str) -> tuple:
        """Chaîne deux actes (parent → enfant) avec vérification d'existence."""
        if code_acte_child == code_acte_parent:
            return False, "Un acte ne peut pas être son propre parent"
        if not self.dao.obtenir_par_id(code_acte_parent):
            return False, "L'acte parent est introuvable"
        if not self.dao.obtenir_par_id(code_acte_child):
            return False, "L'acte enfant est introuvable"
        if self.dao.link_acte_parent(code_acte_child, code_acte_parent):
            return True, "Lien parent-enfant établi avec succès"
        return False, "Erreur lors du chaînage des actes"

    # =========================================================================
    # SECTION 3 — RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_id(self, code_acte: str) -> Optional[ActeMedical]:
        return self.dao.obtenir_par_id(code_acte)

    def lister_par_consultation(self, code_consultation: str) -> list:
        return self.dao.lister_par_consultation(code_consultation)
    
    def lister_actes_par_consultation(self, code_consultation: str) -> list:
        """Alias pour lister_par_consultation (compatibilité historique patient)"""
        return self.lister_par_consultation(code_consultation)

    def lister_par_type(self, type_acte: str) -> list:
        return self.dao.lister_par_type(type_acte)

    def lister_par_statut(self, statut: str) -> list:
        return self.dao.lister_par_statut(statut)

    def lister_tous(self, limit: int = 1000) -> list:
        return self.dao.lister_tous(limit)

    # =========================================================================
    # SECTION 4 — WORKFLOW / TRANSITIONS D'ÉTATS
    # =========================================================================

    def passer_en_cours(self, code_acte: str) -> tuple:
        """Démarre l'exécution de l'acte en passant par le service de file d'attente pour synchroniser avec acte_visite."""
        from service_metier.file_attente_service import FileAttenteService
        service_file = FileAttenteService()
        return service_file.demarrer_passage_par_code_acte(code_acte)

    def terminer_acte(self, code_acte: str, raison: str = None) -> tuple:
        """Clôture un acte en cours en passant par le service de file d'attente pour synchroniser avec acte_visite."""
        from service_metier.file_attente_service import FileAttenteService
        service_file = FileAttenteService()
        return service_file.terminer_passage_par_code_acte(code_acte, raison)

    def refuser_acte(self, code_acte: str, raison: str) -> tuple:
        """Refuse ou annule un acte avec raison obligatoire."""
        valide, msg = self.valider_decision_medicale(raison)
        if not valide:
            return False, f"Raison invalide : {msg}"
        if self.dao.refuser(code_acte, raison):
            self.logger.info(f"Acte {code_acte} refusé : {raison}")
            return True, "Acte refusé avec succès"
        return False, "Impossible de refuser l'acte depuis son état actuel"

    def planifier_acte(self, code_acte: str) -> tuple:
        """Planifie un acte (plus_tard) sans date précise."""
        if self.dao.planifier(code_acte):
            self.logger.info(f"Acte {code_acte} planifié")
            return True, "Acte planifié avec succès"
        return False, "Impossible de planifier l'acte depuis son état actuel"

    # =========================================================================
    # SECTION 5 — CHOIX PATIENT
    # =========================================================================

    def enregistrer_choix_patient(self, code_acte: str, choix: str) -> tuple:
        """
        Enregistre le choix du patient et déclenche la cascade workflow :
          maintenant -> en_attente (file d'attente gérée via ActeVisiteDAO)
          plus_tard  -> planifie
          ailleurs   -> refuse + mode_realisation=externe
        """
        valide, msg = self.valider_choix_patient(choix)
        if not valide:
            return False, msg
        if self.dao.enregistrer_choix_patient(code_acte, choix):
            self.logger.info(f"Choix patient '{choix}' enregistré pour acte {code_acte}")
            return True, f"Choix '{choix}' enregistré avec succès"
        return False, "Erreur lors de l'enregistrement du choix patient"

    def patient_choisit_maintenant(self, code_acte: str) -> tuple:
        """Exécution immédiate. L'acte reste en_attente pour la file d'attente."""
        return self.enregistrer_choix_patient(code_acte, ChoixPatient.MAINTENANT)

    def patient_choisit_plus_tard(self, code_acte: str) -> tuple:
        """Report → planifié."""
        return self.enregistrer_choix_patient(code_acte, ChoixPatient.PLUS_TARD)

    def patient_choisit_ailleurs(self, code_acte: str) -> tuple:
        """Réalisation externe → refusé."""
        return self.enregistrer_choix_patient(code_acte, ChoixPatient.AILLEURS)

    # FIN — Les sections file d'attente, temps, facturation, alertes et analytics
    # sont dans FileAttenteService et ParcoursPatientService.

    def planifier_rendez_vous(self, code_acte: str, date_rdv,
                               code_personnel: str = None,
                               code_session: str = None) -> tuple:
        """
        Planifie un RDV pour un acte avec choix_patient='plus_tard'.
        Crée un enregistrement dans la table rendez_vous lié à l'acte.
        Dérive automatiquement code_visite et code_session depuis la consultation
        si non fournis, afin que traiter_rdv_du_jour puisse traiter ce RDV.
        date_rdv : datetime ou str 'YYYY-MM-DD HH:MM:SS'
        """
        acte = self.dao.obtenir_par_id(code_acte)
        if not acte:
            return None, "Acte introuvable"
        if acte.statut_acte not in [StatutActe.EN_ATTENTE, StatutActe.PLANIFIE]:
            return None, f"L'acte doit être en_attente ou planifié (statut actuel: {acte.statut_acte})"

        if isinstance(date_rdv, str):
            try:
                date_rdv = datetime.strptime(date_rdv, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    date_rdv = datetime.strptime(date_rdv, "%Y-%m-%d")
                except ValueError:
                    return None, "Format de date invalide. Utiliser 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS'"

        if date_rdv < datetime.now():
            return None, "La date du rendez-vous ne peut pas être dans le passé"

        # Dériver code_visite et code_session depuis la consultation → visite
        code_visite = None
        if acte.code_consultation:
            try:
                from core.connexion_db import DBConnection
                _db = DBConnection()
                _conn = _db.connect()
                if _conn:
                    try:
                        _cur = _conn.cursor()
                        _cur.execute(
                            "SELECT code_visite FROM consultation WHERE code = %s LIMIT 1",
                            (acte.code_consultation,)
                        )
                        _row = _cur.fetchone()
                        if _row:
                            code_visite = _row.get('code_visite') if isinstance(_row, dict) else _row[0]
                        # Dériver code_session si non fourni
                        if code_visite and not code_session:
                            _cur.execute(
                                "SELECT code_session FROM visite WHERE code_visite = %s LIMIT 1",
                                (code_visite,)
                            )
                            _row2 = _cur.fetchone()
                            if _row2:
                                code_session = _row2.get('code_session') if isinstance(_row2, dict) else _row2[0]
                    finally:
                        _db.close()
            except Exception:
                pass  # code_visite et code_session resteront None si erreur

        dao_rdv = RendezVousDAO()
        rdv = RendezVous(
            code_personnel     = code_personnel,
            code_session       = code_session,
            code_visite        = code_visite,
            date_rendez_vous   = date_rdv,
            statut_rendez_vous = "attente",
            code_acte          = acte.id_acte,
        )
        if not dao_rdv.ajouter(rdv):
            return None, "Erreur lors de la création du rendez-vous"

        # Créer l'acte_visite role='origine' dans la visite d'origine.
        # Cela trace que l'acte a été prescrit et que le patient reviendra.
        # Ne créer que si pas déjà présent (idempotence).
        if code_visite:
            try:
                from data.dao_acte_visite import ActeVisiteDAO
                dao_av = ActeVisiteDAO()
                from core.connexion_db import DBConnection
                _db2 = DBConnection()
                _conn2 = _db2.connect()
                if _conn2:
                    try:
                        _cur2 = _conn2.cursor()
                        _cur2.execute("""
                            SELECT 1 FROM acte_visite
                            WHERE code_acte = %s AND code_visite = %s
                              AND role_visite = 'origine'
                            LIMIT 1
                        """, (acte.id_acte, code_visite))
                        if not _cur2.fetchone():
                            _cur2.execute("""
                                INSERT INTO acte_visite
                                    (code_acte, code_visite, role_visite, date_liaison)
                                VALUES (%s, %s, 'origine', %s)
                            """, (acte.id_acte, code_visite, datetime.now()))
                            _conn2.commit()
                    finally:
                        _db2.close()
            except Exception as e_av:
                self.logger.warning("Impossible de créer acte_visite origine: %s", e_av)

        # Passer l'acte en planifié si ce n'est pas déjà le cas
        if acte.statut_acte == StatutActe.EN_ATTENTE:
            self.dao.planifier(code_acte)

        # Mettre le patient en Attente payement sur la visite d'origine :
        # il doit régler la visite actuelle avant de revenir le jour du RDV.
        if code_visite:
            try:
                from core.connexion_db import DBConnection as _DBPay
                _db_pay = _DBPay()
                _conn_pay = _db_pay.connect()
                if _conn_pay:
                    try:
                        _cur_pay = _conn_pay.cursor()
                        _cur_pay.execute(
                            "UPDATE visite SET statut_patient = 'Attente payement'"
                            " WHERE code_visite = %s",
                            (code_visite,)
                        )
                        _conn_pay.commit()
                        self.logger.info(
                            "Visite %s passée en Attente payement (acte %s planifié)",
                            code_visite, code_acte
                        )
                    finally:
                        _db_pay.close()
            except Exception as e_pay:
                self.logger.warning("Impossible de passer visite en Attente payement: %s", e_pay)

        self.logger.info("RDV planifié pour acte %s le %s", code_acte, date_rdv)
        return rdv, f"Rendez-vous planifié le {date_rdv.strftime('%d/%m/%Y à %H:%M')}"

    # =========================================================================
    # SECTION — DONNÉES FORMULAIRE (listes déroulantes)
    # =========================================================================

    def obtenir_code_visite_par_consultation(self, code_consultation: str):
        """Retourne le code_visite associé à une consultation."""
        try:
            return self.consultation_dao.get_code_visite_par_consultation(code_consultation)
        except Exception as e:
            self.logger.error("obtenir_code_visite_par_consultation: %s", e)
            return None

    def lister_consultations_form(self) -> list:
        """Retourne les consultations actives pour les dropdowns du formulaire."""
        try:
            return self.consultation_dao.lister_pour_formulaire_acte()
        except Exception as e:
            self.logger.error("lister_consultations_form: %s", e)
            return []

    def lister_sessions_form(self) -> list:
        """Retourne les sessions disponibles pour les dropdowns du formulaire."""
        try:
            return self.visite_dao.lister_sessions()
        except Exception as e:
            self.logger.error("lister_sessions_form: %s", e)
            return []

    def lister_personnel_form(self, roles: list = None) -> list:
        """Retourne le personnel pour les dropdowns, filtré par rôles si fournis."""
        try:
            if roles:
                from service_metier.user_service import UserService
                rows = UserService().lister_personnel_par_roles(roles)
                return [{'code': r['code'], 'label': f"{r['nom']} {r['prenom']}"} for r in rows]
            return self.personnel_dao.lister_pour_formulaire()
        except Exception as e:
            self.logger.error("lister_personnel_form: %s", e)
            return []