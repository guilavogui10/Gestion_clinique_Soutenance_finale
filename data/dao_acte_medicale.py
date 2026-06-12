import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from datetime import datetime
from core.connexion_db import DBConnection
from models.model_acte_medicale import ActeMedical

DictCursor = pymysql.cursors.DictCursor


# =============================================================================
# CONSTANTES METIER
# =============================================================================

class StatutActe:
    EN_ATTENTE = "en_attente"   # acte prescrit, patient n a pas encore choisi
    PLANIFIE   = "planifie"     # patient choisit plus_tard -> RDV a venir
    EN_COURS   = "en_cours"     # en cours d execution dans le service
    TERMINE    = "termine"      # acte finalise
    REFUSE     = "refuse"       # patient choisit ailleurs OU annulation


class ChoixPatient:
    MAINTENANT = "maintenant"   # execution immediate -> mise en file
    PLUS_TARD  = "plus_tard"    # report -> RDV planifie
    AILLEURS   = "ailleurs"     # execution externe -> statut refuse


class TypeActe:
    EXAMEN       = "examen"
    CHIRURGIE    = "chirurgie"
    LUNETTE      = "lunette"
    PRESCRIPTION = "prescription"


class ModeRealisation:
    INTERNE = "interne"
    EXTERNE = "externe"


# Machine a etats : transitions autorisees pour statut_acte
TRANSITIONS_VALIDES = {
    StatutActe.EN_ATTENTE: [StatutActe.PLANIFIE, StatutActe.EN_COURS, StatutActe.REFUSE],
    StatutActe.PLANIFIE:   [StatutActe.EN_COURS, StatutActe.REFUSE],
    StatutActe.EN_COURS:   [StatutActe.TERMINE,  StatutActe.REFUSE],
    StatutActe.TERMINE:    [],
    StatutActe.REFUSE:     [],
}


# =============================================================================
# DAO -- CRUD + MACHINE A ETATS
# =============================================================================

class ActeMedicalDAO:
    """
    DAO pour la table acte_medical.
    Responsabilite unique : CRUD et transitions d etats de la prescription.
    La file d attente et les durees sont gerees par ActeVisiteDAO.
    """

    def __init__(self):
        self.db = DBConnection()

    # =========================================================================
    # SECTION 1 -- CRUD
    # =========================================================================

    def ajouter(self, acte: ActeMedical) -> bool:
        """Insere un nouvel acte medical."""
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)
            
            # Vérifier que la consultation existe (Intégrité de la clé étrangère)
            cursor.execute("SELECT 1 FROM consultation WHERE code = %s", (acte.code_consultation,))
            if not cursor.fetchone():
                raise ValueError(f"Erreur d'intégrité : La consultation '{acte.code_consultation}' est introuvable.")
                
            acte.id_acte = self._generer_code_acte(cursor)
            
            # Vérifier que le code généré est valide
            if not acte.id_acte or not isinstance(acte.id_acte, str) or acte.id_acte.strip() == "":
                raise ValueError("Erreur interne : Génération du code acte échouée.")
            
            cursor.execute("""
                INSERT INTO acte_medical (
                    code_acte, code_consultation, type_acte, decision_medicale,
                    choix_patient, mode_realisation, statut_acte,
                    raison_refus
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                acte.id_acte,
                acte.code_consultation, acte.type_acte,   acte.decision_medicale,
                acte.choix_patient or "",     acte.mode_realisation or "interne", acte.statut_acte or "en_attente",
                acte.raison_refus or "",
            ))
            conn.commit()
            return True
        except ValueError as ve:
            print(f"[ActeMedicalDAO] Erreur de validation ajouter: {ve}")
            conn.rollback()
            raise ve
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur système ajouter: {e}")
            conn.rollback()
            raise Exception(f"Erreur lors de la création de l'acte en base de données: {str(e)}")
        finally:
            self.db.close()

    def modifier(self, acte: ActeMedical) -> bool:
        """Met a jour un acte medical existant."""
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE acte_medical SET
                    code_consultation=%s, type_acte=%s, decision_medicale=%s,
                    choix_patient=%s, mode_realisation=%s, statut_acte=%s,
                    raison_refus=%s
                WHERE code_acte=%s
            """, (
                acte.code_consultation, acte.type_acte,   acte.decision_medicale,
                acte.choix_patient,     acte.mode_realisation, acte.statut_acte,
                acte.raison_refus,
                acte.id_acte,
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur modifier: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def supprimer(self, code_acte: str) -> bool:
        """Supprime un acte medical par son code."""
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM acte_medical WHERE code_acte=%s", (code_acte,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur supprimer: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def obtenir_par_id(self, code_acte: str):
        """Retourne un ActeMedical par son code."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("SELECT * FROM acte_medical WHERE code_acte=%s", (code_acte,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur obtenir_par_id: {e}")
            return None
        finally:
            self.db.close()

    def lister_par_consultation(self, code_consultation: str) -> list:
        """Retourne tous les actes lies a une consultation."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "SELECT * FROM acte_medical WHERE code_consultation=%s ORDER BY code_acte ASC",
                (code_consultation,)
            )
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur lister_par_consultation: {e}")
            return []
        finally:
            self.db.close()

    def lister_par_type(self, type_acte: str) -> list:
        """Retourne tous les actes d un type donne."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "SELECT * FROM acte_medical WHERE type_acte=%s ORDER BY code_acte DESC",
                (type_acte,)
            )
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur lister_par_type: {e}")
            return []
        finally:
            self.db.close()

    def lister_par_statut(self, statut: str) -> list:
        """Retourne tous les actes dans un statut donne."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "SELECT * FROM acte_medical WHERE statut_acte=%s ORDER BY code_acte DESC",
                (statut,)
            )
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur lister_par_statut: {e}")
            return []
        finally:
            self.db.close()

    def lister_tous(self, limit: int = 1000) -> list:
        """Retourne tous les actes, limité pour la performance globale."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "SELECT * FROM acte_medical ORDER BY code_acte DESC LIMIT %s",
                (limit,)
            )
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur lister_tous: {e}")
            return []
        finally:
            self.db.close()

    def lister_actes_en_attente_rdv_par_session(self, code_session: str) -> list:
        """
        Retourne les actes avec choix_patient='plus_tard' pour une session donnée.
        Ces actes sont ceux pour lesquels un rendez-vous doit être créé.
        Jointure acte_medical -> consultation pour filtrer par session.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT a.code_acte, a.type_acte, a.decision_medicale,
                       a.statut_acte, a.code_consultation
                FROM acte_medical a
                JOIN consultation c ON a.code_consultation = c.code
                WHERE c.code_session = %s
                  AND a.choix_patient = 'plus_tard'
                  AND a.statut_acte IN ('en_attente', 'planifie')
                ORDER BY a.code_acte DESC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur lister_actes_en_attente_rdv_par_session: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # SECTION 2 -- MACHINE A ETATS
    # =========================================================================

    def _changer_statut(self, code_acte: str, nouveau_statut: str,
                        champs_extras: dict = None, ext_conn=None) -> bool:
        """
        Noyau du workflow : verifie la transition puis applique.
        champs_extras : colonnes supplementaires a mettre a jour simultanement.
        """
        conn = ext_conn if ext_conn else self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "SELECT statut_acte FROM acte_medical WHERE code_acte=%s", (code_acte,)
            )
            row = cursor.fetchone()
            if not row:
                print(f"[ActeMedicalDAO] Acte {code_acte} introuvable.")
                return False

            statut_actuel = row['statut_acte']

            # Transition idempotente : déjà dans le bon état, rien à faire
            if nouveau_statut == statut_actuel:
                return True

            if nouveau_statut not in TRANSITIONS_VALIDES.get(statut_actuel, []):
                print(
                    f"[ActeMedicalDAO] Transition invalide : "
                    f"{statut_actuel} -> {nouveau_statut} pour acte {code_acte}"
                )
                return False

            set_clauses = ["statut_acte=%s"]
            params      = [nouveau_statut]
            if champs_extras:
                for col, val in champs_extras.items():
                    set_clauses.append(f"{col}=%s")
                    params.append(val)
            params.append(code_acte)

            cursor.execute(
                f"UPDATE acte_medical SET {', '.join(set_clauses)} WHERE code_acte=%s",
                params
            )
            
            if not ext_conn:
                conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur _changer_statut: {e}")
            if not ext_conn:
                conn.rollback()
            return False
        finally:
            if not ext_conn:
                self.db.close()

    def planifier(self, code_acte: str) -> bool:
        """Cas plus_tard : passe l acte en statut planifie."""
        return self._changer_statut(code_acte, StatutActe.PLANIFIE)

    def passer_en_cours(self, code_acte: str, ext_conn=None) -> bool:
        """Debute l execution de l acte (en_attente ou planifie -> en_cours)."""
        return self._changer_statut(code_acte, StatutActe.EN_COURS, ext_conn=ext_conn)

    def terminer(self, code_acte: str, raison: str = None, ext_conn=None) -> bool:
        """Cloture un acte en cours. Enregistre un commentaire optionnel."""
        extras = {"raison_refus": raison} if raison else None
        return self._changer_statut(code_acte, StatutActe.TERMINE, extras, ext_conn=ext_conn)

    def refuser(self, code_acte: str, raison: str,
                mode_realisation: str = None) -> bool:
        """
        Refuse ou annule un acte.
        Si mode_realisation='externe', met aussi a jour ce champ.
        """
        extras = {"raison_refus": raison}
        if mode_realisation:
            extras["mode_realisation"] = mode_realisation
        return self._changer_statut(code_acte, StatutActe.REFUSE, extras)

    def enregistrer_choix_patient(self, code_acte: str, choix: str) -> bool:
        """
        Enregistre le choix du patient et declenche la transition metier :
          maintenant -> statut reste en_attente (sera mis en file via acte_visite)
          plus_tard  -> planifie
          ailleurs   -> refuse + mode_realisation=externe
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE acte_medical SET choix_patient=%s WHERE code_acte=%s",
                (choix, code_acte)
            )
            conn.commit()
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur enregistrer_choix_patient: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

        if choix == ChoixPatient.PLUS_TARD:
            return self.planifier(code_acte)
        if choix == ChoixPatient.AILLEURS:
            return self.refuser(code_acte, "Patient choisit realisation ailleurs",
                                mode_realisation=ModeRealisation.EXTERNE)
        return True

    # =========================================================================
    # SECTION 3 -- FACTORY DE CREATION
    # =========================================================================

    def create_acte(self, code_consultation: str, type_acte: str,
                    decision_medicale: str,
                    source_acte: str = "consultation"):
        """
        Cree et persiste un acte avec les valeurs par defaut metier.
        Retourne l objet cree (avec id_acte assigne) ou None si echec.
        """
        acte = ActeMedical(
            code_consultation = code_consultation,
            type_acte         = type_acte,
            decision_medicale = decision_medicale,
            statut_acte       = StatutActe.EN_ATTENTE,
            mode_realisation  = ModeRealisation.INTERNE,
        )
        return acte if self.ajouter(acte) else None

    def create_actes_depuis_recommandations(self, code_consultation: str,
                                             recommandations: list) -> list:
        """
        Cree plusieurs actes a partir d une liste de recommandations.
        Format : [{"type_acte": "examen", "decision_medicale": "..."}, ...]
        Retourne la liste des objets crees.
        """
        crees = []
        for reco in recommandations:
            type_acte = reco.get("type_acte")
            decision  = reco.get("decision_medicale", "")
            if not type_acte:
                continue
            acte = self.create_acte(code_consultation, type_acte, decision,
                                    source_acte="recommandation")
            if acte:
                crees.append(acte)
        return crees

    def link_acte_parent(self, code_acte_child: str, code_acte_parent: str) -> bool:
        """Stub — colonne id_acte_parent absente de la table réelle."""
        return True

    def _inserer_import(self, cursor, code_consultation: str, type_acte: str,
                        decision_medicale: str) -> str:
        """
        INSERT acte_medical en mode import (statut=termine, choix=maintenant).
        Reçoit un curseur externe — pas de gestion de connexion ni de commit.
        Lève ValueError si la consultation est introuvable.
        Retourne le code_acte généré.
        """
        cursor.execute(
            "SELECT code_visite FROM consultation WHERE code = %s LIMIT 1",
            (code_consultation,)
        )
        if not cursor.fetchone():
            raise ValueError(f"Consultation '{code_consultation}' introuvable")
        code_acte = self._generer_code_acte(cursor)
        cursor.execute("""
            INSERT INTO acte_medical (
                code_acte, code_consultation, type_acte, decision_medicale,
                choix_patient, mode_realisation, statut_acte, raison_refus
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (code_acte, code_consultation, type_acte,
              decision_medicale or type_acte,
              'maintenant', 'interne', 'termine', ''))
        return code_acte

    # =========================================================================
    # METHODES PRIVEES
    # =========================================================================

    def _generer_code_acte(self, cursor) -> str:
        """Genere un code unique pour acte_medical (ex: ACT001)."""
        try:
            cursor.execute(
                "SELECT code_acte FROM acte_medical ORDER BY code_acte DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                last_code = row['code_acte'] if isinstance(row, dict) else row[0]
                # Vérifier que last_code est valide
                if not last_code or not isinstance(last_code, str) or last_code.strip() == "":
                    return "ACT001"
                # Vérifier le format ACTxxx
                if not last_code.startswith('ACT'):
                    # Format inattendu, compter les actes
                    cursor.execute("SELECT COUNT(*) FROM acte_medical")
                    count = cursor.fetchone()
                    total = (count[0] if isinstance(count, tuple) else count.get('COUNT(*)', 0)) + 1
                    return f"ACT{total:03d}"
                # Extraire la partie numérique
                num_part = last_code[3:]  # Tout après 'ACT'
                if num_part.isdigit():
                    last_num = int(num_part)
                    return f"ACT{last_num + 1:03d}"
                else:
                    # Partie numérique invalide, compter les actes
                    cursor.execute("SELECT COUNT(*) FROM acte_medical")
                    count = cursor.fetchone()
                    total = (count[0] if isinstance(count, tuple) else count.get('COUNT(*)', 0)) + 1
                    return f"ACT{total:03d}"
            return "ACT001"
        except Exception as e:
            print(f"[ActeMedicalDAO] Erreur _generer_code_acte: {e}")
            # En cas d'erreur, lever une exception plutôt que retourner un code invalide
            raise RuntimeError(f"Impossible de générer un code_acte: {e}")

    def _row_to_object(self, row: dict) -> ActeMedical:
        """Convertit une ligne DB (dict) en objet ActeMedical."""
        return ActeMedical(
            id_acte           = row.get('code_acte') or row.get('id_acte'),
            code_consultation = row.get('code_consultation'),
            type_acte         = row.get('type_acte'),
            decision_medicale = row.get('decision_medicale'),
            choix_patient     = row.get('choix_patient'),
            mode_realisation  = row.get('mode_realisation'),
            statut_acte       = row.get('statut_acte'),
            raison_refus      = row.get('raison_refus'),
        )

