"""
file_attente_service.py
-----------------------
Service métier — Gestion de la file d'attente.

Responsabilités :
  - Enregistrement de l'entrée d'un patient dans la file
  - Démarrage et clôture d'un passage
  - Consultation de la file par service (type_acte)
  - Identification du prochain patient
  - Alertes sur attentes longues
  - Transfert d'un acte vers un autre service
"""

import logging
from datetime import datetime, timedelta

from data.dao_acte_medicale import ActeMedicalDAO, StatutActe, TypeActe
from data.dao_acte_visite import ActeVisiteDAO, StatutPassage, RoleVisite
from models.model_acte_visite import ActeVisite


class FileAttenteService:
    """
    Orchestre la file d'attente en coordonnant ActeMedicalDAO et ActeVisiteDAO.
    Un passage = une entrée dans acte_visite avec role_visite='execution'.
    """

    def __init__(self,
                 dao_acte: ActeMedicalDAO = None,
                 dao_visite: ActeVisiteDAO = None):
        self.dao_acte   = dao_acte   or ActeMedicalDAO()
        self.dao_visite = dao_visite or ActeVisiteDAO()
        self.logger     = logging.getLogger(__name__)

    # =========================================================================
    # SECTION 1 — ENTRÉE EN FILE
    # =========================================================================

    def entrer_en_file(self, id_acte: int, code_visite: str) -> tuple:
        """
        Place un acte dans la file d'attente d'exécution.
        Crée un enregistrement acte_visite (role=execution, statut=en_attente)
        et enregistre la date_entree.
        L'acte doit avoir choix_patient='maintenant' et statut='en_attente'.
        """
        acte = self.dao_acte.obtenir_par_id(id_acte)
        if not acte:
            return None, "Acte introuvable"
        if acte.statut_acte != StatutActe.EN_ATTENTE:
            return None, f"L'acte doit être en_attente pour entrer en file (statut actuel: {acte.statut_acte})"

        av = self.dao_visite.ajouter_liaison(
            id_acte, code_visite, RoleVisite.EXECUTION
        )
        if not av:
            return None, "Impossible de créer l'entrée en file"

        ok = self.dao_visite.enregistrer_entree_file(av.id_acte_visite)
        if not ok:
            return None, "Impossible d'enregistrer la date d'entrée"

        self.logger.info(
            "Acte %s entré en file pour visite %s (acte_visite %s)",
            id_acte, code_visite, av.id_acte_visite
        )
        return av, "Patient entré en file avec succès"

    def lier_visite_origine(self, id_acte: int, code_visite: str) -> tuple:
        """
        Enregistre la visite de prescription (role=origine).
        Appelé lors de la création de l'acte depuis une consultation.
        """
        av = self.dao_visite.ajouter_liaison(
            id_acte, code_visite, RoleVisite.ORIGINE
        )
        if not av:
            return None, "Impossible de lier la visite d'origine"
        return av, "Visite d'origine enregistrée"

    # =========================================================================
    # SECTION 2 — GESTION DU PASSAGE
    # =========================================================================

    def demarrer_passage(self, id_acte_visite: int) -> tuple:
        """
        Démarre le passage d'un patient.
        OBSOLÈTE : Utiliser demarrer_passage_par_code_acte à la place.
        Conservé pour compatibilité.
        """
        # Cette méthode est obsolète car id_acte_visite n'existe pas dans la table
        return False, "Méthode obsolète : utiliser demarrer_passage_par_code_acte"
    
    def demarrer_passage_par_code_acte(self, code_acte: int) -> tuple:
        """
        Démarre le passage d'un patient en utilisant le code_acte.
        Récupère le passage actif (en attente) pour cet acte et le démarre.
        """
        from core.connexion_db import DBConnection
        db = DBConnection()
        conn = db.connect()
        if not conn:
            return False, "Erreur de connexion à la base de données"

        try:
            av = self.dao_visite.get_passage_actif(code_acte)
            if not av:
                return False, "Aucun passage actif trouvé pour cet acte"
            
            ok_visite = self.dao_visite.demarrer_passage(code_acte, av.code_visite, ext_conn=conn)
            ok_acte   = self.dao_acte.passer_en_cours(code_acte, ext_conn=conn)
            
            if ok_visite and ok_acte:
                self._mettre_a_jour_statut_patient_demarrage(av.code_visite, code_acte, ext_conn=conn)
                conn.commit()
                self.logger.info("Passage démarré pour acte %s", code_acte)
                return True, "Passage démarré avec succès"
            
            conn.rollback()
            return False, "Erreur lors du démarrage du passage"
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Erreur demarrer_passage_par_code_acte: {e}")
            return False, "Erreur système lors du démarrage du passage"
        finally:
            db.close()
    
    def _mettre_a_jour_statut_patient_demarrage(self, code_visite: str, code_acte: str, ext_conn=None):
        """Met à jour le statut du patient lors du démarrage (Attente X -> En X)."""
        try:
            from core.connexion_db import DBConnection
            
            # Si code_acte est None, c'est la consultation
            if code_acte is None:
                nouveau_statut = "En consultation"
            else:
                # Récupérer le type d'acte
                acte = self.dao_acte.obtenir_par_id(code_acte)
                if not acte:
                    raise ValueError(f"Acte {code_acte} introuvable dans la base de données")
                
                statut_map = {
                    TypeActe.EXAMEN: "En examen",
                    TypeActe.CHIRURGIE: "En chirurgie",
                    TypeActe.LUNETTE: "En lunette",
                    TypeActe.PRESCRIPTION: "En pharmacie"
                }
                
                nouveau_statut = statut_map.get(acte.type_acte)
                if not nouveau_statut:
                    raise ValueError(f"Type d'acte inconnu ou non pris en charge: {acte.type_acte}")
            
            if not ext_conn:
                db = DBConnection()
                conn = db.connect()
            else:
                conn = ext_conn
                db = None
                
            if not conn:
                raise Exception("Impossible de se connecter à la base de données")
            
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE visite SET statut_patient = %s WHERE code_visite = %s",
                    (nouveau_statut, code_visite)
                )
                if not ext_conn:
                    conn.commit()
                self.logger.info(f"Statut patient mis à jour: {nouveau_statut} pour visite {code_visite}")
            finally:
                if not ext_conn and db:
                    db.close()
        except Exception as e:
            self.logger.error(f"Erreur _mettre_a_jour_statut_patient_demarrage: {e}")
            raise
    
    def _mettre_a_jour_statut_patient_terminaison(self, code_visite: str, code_acte: str, ext_conn=None):
        """Met à jour le statut du patient lors de la terminaison (En X -> Attente prochaine étape ou Attente paiement)."""
        try:
            from core.connexion_db import DBConnection
            import pymysql
            
            self.logger.info(f"Début _mettre_a_jour_statut_patient_terminaison pour visite {code_visite}, acte {code_acte}")
            
            if not ext_conn:
                db = DBConnection()
                conn = db.connect()
            else:
                conn = ext_conn
                db = None
                
            if not conn:
                self.logger.error("Impossible de se connecter à la base de données")
                raise Exception("Connexion à la base de données échouée")
            
            try:
                cursor = conn.cursor(pymysql.cursors.DictCursor)

                # Vérifier si le patient est déjà en attente de rendez-vous (acte plus_tard)
                # Si oui, ne pas écraser ce statut — le médecin a déjà prescrit un acte en RDV
                cursor.execute(
                    "SELECT statut_patient FROM visite WHERE code_visite = %s",
                    (code_visite,)
                )
                row_visite = cursor.fetchone()
                statut_courant = row_visite['statut_patient'] if row_visite else None
                if statut_courant and statut_courant.lower().startswith('attente rendez-vous'):
                    self.logger.info(
                        f"Statut '{statut_courant}' déjà positionné (acte plus_tard) — "
                        f"terminaison de {code_acte} n'écrase pas ce statut."
                    )
                    return

                # Récupérer uniquement les actes d'exécution (role='execution') de cette visite.
                # Les enregistrements role='origine' (actes plus_tard prescrits pour un RDV futur)
                # ne sont pas des étapes d'exécution en file d'attente et ne doivent pas
                # influencer le calcul du « prochain acte à faire ».
                cursor.execute("""
                    SELECT am.code_acte, am.type_acte, av.date_sortie
                    FROM acte_visite av
                    JOIN acte_medical am ON am.code_acte = av.code_acte
                    WHERE av.code_visite = %s
                      AND av.role_visite = 'execution'
                    ORDER BY av.date_liaison ASC
                """, (code_visite,))
                actes = cursor.fetchall()

                self.logger.info(f"Actes (execution) trouvés pour visite {code_visite}: {len(actes)}")
                for acte in actes:
                    self.logger.info(f"  - Acte {acte['code_acte']}: type={acte['type_acte']}, date_sortie={acte['date_sortie']}")

                if not actes:
                    nouveau_statut = "Attente payement"
                    self.logger.info("Aucun acte d'exécution trouvé, passage à Attente payement")
                else:
                    # Trouver le prochain acte d'exécution non terminé
                    prochain_acte = None
                    for acte in actes:
                        if acte['date_sortie'] is None:
                            prochain_acte = acte
                            self.logger.info(f"Prochain acte trouvé: {acte['code_acte']} ({acte['type_acte']})")
                            break

                    if prochain_acte:
                        statut_map = {
                            TypeActe.EXAMEN: "Attente examen",
                            TypeActe.CHIRURGIE: "Attente chirurgie",
                            TypeActe.LUNETTE: "Attente lunette",
                            TypeActe.PRESCRIPTION: "Attente pharmacie"
                        }
                        nouveau_statut = statut_map.get(prochain_acte['type_acte'], "Attente payement")
                        self.logger.info(f"Prochain acte détecté: {prochain_acte['type_acte']} -> {nouveau_statut}")
                    else:
                        # Tous les actes d'exécution sont terminés → attente décision médecin
                        cursor.execute(
                            "SELECT type_acte FROM acte_medical WHERE code_acte = %s",
                            (code_acte,)
                        )
                        row_current = cursor.fetchone()
                        type_acte_courant = row_current['type_acte'] if row_current else None
                        terminaison_map = {
                            TypeActe.EXAMEN:       "Examen terminé",
                            TypeActe.CHIRURGIE:    "Chirurgie terminée",
                            TypeActe.LUNETTE:      "Lunette terminée",
                            TypeActe.PRESCRIPTION: "Pharmacie terminée",
                        }
                        nouveau_statut = terminaison_map.get(type_acte_courant, "Examen terminé")
                        self.logger.info(f"Tous les actes d'exécution terminés → {nouveau_statut} (attente décision médecin)")

                self.logger.info(f"Mise à jour du statut patient: {nouveau_statut}")
                cursor.execute(
                    "UPDATE visite SET statut_patient = %s WHERE code_visite = %s",
                    (nouveau_statut, code_visite)
                )
                if not ext_conn:
                    conn.commit()
                self.logger.info(f"Statut patient mis à jour avec succès: {nouveau_statut} pour visite {code_visite}")
            finally:
                if not ext_conn and db:
                    db.close()
        except Exception as e:
            self.logger.error(f"Erreur _mettre_a_jour_statut_patient_terminaison: {e}", exc_info=True)
            raise

    def terminer_passage(self, id_acte_visite: int, raison: str = None) -> tuple:
        """
        Termine le passage d'un patient.
        OBSOLÈTE : Utiliser terminer_passage_par_code_acte à la place.
        Conservé pour compatibilité.
        """
        # Cette méthode est obsolète car id_acte_visite n'existe pas dans la table
        return False, "Méthode obsolète : utiliser terminer_passage_par_code_acte"
    
    def terminer_passage_par_code_acte(self, code_acte: int, raison: str = None) -> tuple:
        """
        Termine le passage d'un patient en utilisant le code_acte.
        Récupère le passage actif (en cours) pour cet acte et le termine.
        """
        self.logger.info(f"Début terminer_passage_par_code_acte pour acte {code_acte}")
        
        from core.connexion_db import DBConnection
        db = DBConnection()
        conn = db.connect()
        if not conn:
            return False, "Erreur de connexion à la base de données"

        try:
            av = self.dao_visite.get_passage_actif(code_acte)
            if not av:
                self.logger.error(f"Aucun passage actif trouvé pour acte {code_acte}")
                return False, "Aucun passage actif trouvé pour cet acte"
            
            self.logger.info(f"Passage actif trouvé: code_visite={av.code_visite}, statut={av.statut_passage}")
            
            ok_visite = self.dao_visite.terminer_passage(code_acte, av.code_visite, ext_conn=conn)
            self.logger.info(f"Résultat terminer_passage DAO: {ok_visite}")
            
            ok_acte = self.dao_acte.terminer(code_acte, raison, ext_conn=conn)
            self.logger.info(f"Résultat terminer acte DAO: {ok_acte}")

            if ok_visite and ok_acte:
                self.logger.info(f"Appel de _mettre_a_jour_statut_patient_terminaison")
                self._mettre_a_jour_statut_patient_terminaison(av.code_visite, code_acte, ext_conn=conn)
                conn.commit()
                self.logger.info("Passage terminé pour acte %s", code_acte)
                return True, "Passage terminé avec succès"
            
            conn.rollback()
            self.logger.error(f"Erreur lors de la terminaison: ok_visite={ok_visite}, ok_acte={ok_acte}")
            return False, "Erreur lors de la clôture du passage"
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Erreur terminer_passage_par_code_acte: {e}")
            return False, "Erreur système lors de la clôture du passage"
        finally:
            db.close()

    # =========================================================================
    # SECTION 3 — CONSULTATION DE LA FILE
    # =========================================================================

    def obtenir_file_attente(self, type_acte: str = None) -> list:
        """
        Retourne la file d'attente globale ou filtrée par type d'acte.
        Triée par date_entree ASC (FIFO).
        """
        return self.dao_visite.get_file_attente(type_acte)

    def obtenir_prochain_patient(self, type_acte: str = None) -> ActeVisite | None:
        """Retourne le prochain passage à traiter (le plus ancien en attente)."""
        return self.dao_visite.get_prochain_en_attente(type_acte)

    def obtenir_en_cours(self, type_acte: str = None) -> list:
        """Retourne tous les passages actuellement en cours d'exécution."""
        return self.dao_visite.get_en_cours(type_acte)

    def obtenir_taille_file(self, type_acte: str = None) -> dict:
        """Retourne le nombre de patients en attente (global ou par service)."""
        if type_acte:
            file = self.dao_visite.get_file_attente(type_acte)
            return {type_acte: len(file)}
        result = {}
        for ta in [TypeActe.EXAMEN, TypeActe.CHIRURGIE,
                   TypeActe.LUNETTE, TypeActe.PRESCRIPTION]:
            result[ta] = len(self.dao_visite.get_file_attente(ta))
        return result

    def obtenir_passage_actif(self, id_acte: int) -> ActeVisite | None:
        """Retourne le passage en cours ou en attente pour un acte donné."""
        return self.dao_visite.get_passage_actif(id_acte)

    def enregistrer_controle(self, code_acte: str, code_session: str) -> tuple:
        """
        Crée une visite de contrôle pour un patient qui revient après
        l'exécution d'un acte médical. Le patient va directement au service
        (Attente examen/chirurgie/etc.) sans passer par la consultation.
        """
        return self.dao_visite.creer_visite_controle(code_acte, code_session)

    def obtenir_suivi_actifs(self) -> list:
        """Retourne tous les patients actifs avec leur progression pour le suivi temps réel."""
        return self.dao_visite.get_suivi_actifs()

    def valider_sejour_patient(self, code_visite: str) -> tuple:
        """
        Passe le statut du patient à 'Attente payement'.
        Appelé quand le médecin décide que la séance est terminée
        (plus d'actes à prescrire pour aujourd'hui).
        """
        from core.connexion_db import DBConnection
        db = DBConnection()
        conn = db.connect()
        if not conn:
            return False, "Connexion DB échouée"
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE visite SET statut_patient = 'Attente payement' WHERE code_visite = %s",
                (code_visite,)
            )
            conn.commit()
            self.logger.info(f"Patient {code_visite} passé en Attente payement")
            return True, "Patient passé en Attente payement"
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Erreur valider_sejour_patient: {e}")
            return False, str(e)
        finally:
            db.close()

    def obtenir_file_attente_enrichie(self, type_acte: str = None) -> list:
        """
        File d'attente (en_attente) avec données acte_medical jointes.
        Retourne des dicts : id_acte_visite, code_acte, code_visite,
        date_entree, statut_passage, type_acte, decision_medicale, code_consultation.
        """
        return self.dao_visite.get_file_attente_enrichie(type_acte)

    def obtenir_en_cours_enrichi(self, type_acte: str = None) -> list:
        """
        Passages en cours (en_cours) avec données acte_medical jointes.
        Retourne des dicts.
        """
        return self.dao_visite.get_en_cours_enrichi(type_acte)

    # =========================================================================
    # SECTION 4 — ALERTES
    # =========================================================================

    def detecter_attentes_longues(self, seuil_minutes: int = 60) -> list:
        """
        Retourne les passages en attente depuis plus de `seuil_minutes`.
        Utilisé pour alerter le personnel de supervision.
        """
        if seuil_minutes <= 0:
            return []
        file = self.dao_visite.get_file_attente()
        seuil = timedelta(minutes=seuil_minutes)
        maintenant = datetime.now()
        alertes = []
        for av in file:
            if av.date_entree and (maintenant - av.date_entree) > seuil:
                attente_min = int((maintenant - av.date_entree).total_seconds() / 60)
                alertes.append({
                    "id_acte_visite":  av.id_acte_visite,
                    "code_acte":       av.code_acte,
                    "code_visite":     av.code_visite,
                    "date_entree":     av.date_entree,
                    "attente_minutes": attente_min,
                })
        return alertes

    def rapport_alerte_service(self, type_acte: str) -> dict:
        """
        Rapport synthétique pour un service :
        taille file, passages en cours, alertes attente longue.
        """
        return {
            "type_acte":     type_acte,
            "taille_file":   len(self.dao_visite.get_file_attente(type_acte)),
            "en_cours":      len(self.dao_visite.get_en_cours(type_acte)),
            "alertes":       self.detecter_attentes_longues(),
            "prochain":      self.obtenir_prochain_patient(type_acte),
            "horodatage":    datetime.now().isoformat(),
        }

    # =========================================================================
    # SECTION 5 — TRANSFERT
    # =========================================================================

    def transferer_acte(self, id_acte: int,
                        code_visite_cible: str,
                        nouveau_type_acte: str) -> tuple:
        """
        Transfère un acte vers un autre service.
        - Annule le passage en file actuel (si présent)
        - Modifie le type_acte de l'acte médical
        - Crée un nouveau passage dans la file cible
        """
        valeurs = [TypeActe.EXAMEN, TypeActe.CHIRURGIE,
                   TypeActe.LUNETTE, TypeActe.PRESCRIPTION]
        if nouveau_type_acte not in valeurs:
            return False, f"Type d'acte cible invalide : {nouveau_type_acte}"

        acte = self.dao_acte.obtenir_par_id(id_acte)
        if not acte:
            return False, "Acte introuvable"
        if acte.statut_acte not in [StatutActe.EN_ATTENTE, StatutActe.PLANIFIE]:
            return False, "Seuls les actes en_attente ou planifie peuvent être transférés"

        # Mettre à jour le type_acte
        acte.type_acte = nouveau_type_acte
        if not self.dao_acte.modifier(acte):
            return False, "Erreur lors de la mise à jour du type d'acte"

        # Créer une nouvelle entrée en file pour la visite cible
        av, msg = self.entrer_en_file(id_acte, code_visite_cible)
        if not av:
            return False, f"Erreur lors du transfert en file : {msg}"

        self.logger.info(
            "Acte %s transféré vers service '%s' (visite %s)",
            id_acte, nouveau_type_acte, code_visite_cible
        )
        return True, f"Acte transféré vers le service '{nouveau_type_acte}'"
