import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from datetime import datetime
from core.connexion_db import DBConnection
from models.model_acte_visite import ActeVisite

DictCursor = pymysql.cursors.DictCursor


# =============================================================================
# CONSTANTES
# =============================================================================

class StatutPassage:
    EN_ATTENTE = "en_attente"
    EN_COURS   = "en_cours"
    TERMINE    = "termine"


class RoleVisite:
    ORIGINE   = "origine"    # visite de prescription
    EXECUTION = "execution"  # visite d'execution de l'acte
    CONTROLE  = "controle"   # visite de suivi post-acte


# =============================================================================
# DAO acte_visite — file d'attente et suivi temporel
# =============================================================================

class ActeVisiteDAO:
    """
    DAO pour la table acte_visite (table pivot acte_medical <-> visite).
    Gere : liaison, file d'attente, chronometrage des passages.
    """

    def __init__(self):
        self.db = DBConnection()

    # =========================================================================
    # SECTION 1 — LIAISONS
    # =========================================================================

    def ajouter_liaison(self, code_acte: str, code_visite: str,
                         role_visite: str = RoleVisite.EXECUTION) -> ActeVisite | None:
        """
        Cree un lien entre un acte et une visite.
        Retourne l'objet ActeVisite cree (avec id_acte_visite) ou None.
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO acte_visite (
                    code_acte, code_visite, role_visite,
                    date_liaison
                ) VALUES (%s, %s, %s, %s)
            """, (
                code_acte, code_visite, role_visite,
                datetime.now(),
            ))
            id_av = cursor.lastrowid
            conn.commit()
            return self.obtenir_par_id(id_av)
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur ajouter_liaison: {e}")
            conn.rollback()
            return None
        finally:
            self.db.close()

    def enregistrer_entree_file(self, id_acte_visite: int) -> bool:
        """
        Enregistre l'entree du patient dans la file d'attente physique.
        Positionne date_entre = maintenant, statut = en_attente.
        Idempotent : ne met à jour que si date_entre est NULL.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE acte_visite
                SET date_entre=%s
                WHERE id_acte_visite=%s AND date_entre IS NULL
            """, (datetime.now(), id_acte_visite))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur enregistrer_entree_file: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # SECTION 2 — CHRONOMETRAGE DES PASSAGES
    # =========================================================================

    def demarrer_passage(self, code_acte: str, code_visite: str = None) -> bool:
        """
        Démarre l'exécution de l'acte pour ce passage.
        Positionne date_debut_execution = maintenant.
        Si code_visite n'est pas fourni, utilise le passage actif (en attente).
        Idempotent : ne met à jour que si date_debut_execution est NULL.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            if code_visite:
                cursor.execute("""
                    UPDATE acte_visite
                    SET date_debut_execution=%s
                    WHERE code_acte=%s AND code_visite=%s
                      AND date_debut_execution IS NULL
                """, (datetime.now(), code_acte, code_visite))
            else:
                # Utiliser le passage en attente le plus ancien (FIFO)
                cursor.execute("""
                    UPDATE acte_visite
                    SET date_debut_execution=%s
                    WHERE code_acte=%s
                      AND date_sortie IS NULL
                      AND date_debut_execution IS NULL
                    ORDER BY date_entre ASC
                    LIMIT 1
                """, (datetime.now(), code_acte))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur demarrer_passage: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def terminer_passage(self, code_acte: str, code_visite: str = None) -> bool:
        """
        Termine l'exécution d'un passage.
        Positionne date_sortie = maintenant.
        Si code_visite n'est pas fourni, utilise le passage en cours.
        Idempotent : ne met à jour que si date_sortie est NULL.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            if code_visite:
                cursor.execute("""
                    UPDATE acte_visite
                    SET date_sortie=%s
                    WHERE code_acte=%s AND code_visite=%s
                      AND date_sortie IS NULL
                """, (datetime.now(), code_acte, code_visite))
            else:
                # Utiliser le passage en cours (date_debut_execution NOT NULL, date_sortie NULL)
                cursor.execute("""
                    UPDATE acte_visite
                    SET date_sortie=%s
                    WHERE code_acte=%s
                      AND date_sortie IS NULL
                      AND date_debut_execution IS NOT NULL
                    ORDER BY date_debut_execution ASC
                    LIMIT 1
                """, (datetime.now(), code_acte))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur terminer_passage: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # SECTION 3 — LECTURE / FILE D'ATTENTE
    # =========================================================================

    def obtenir_par_id(self, id_acte_visite: int) -> ActeVisite | None:
        """Retourne un ActeVisite par son id."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "SELECT * FROM acte_visite WHERE id_acte_visite=%s",
                (id_acte_visite,)
            )
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur obtenir_par_id: {e}")
            return None
        finally:
            self.db.close()

    def get_passage_actif(self, code_acte: str) -> ActeVisite | None:
        """
        Retourne le passage en cours ou en attente pour un acte donne.
        Utile pour reprendre un passage interrompu ou connaitre l'etat actuel.
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT * FROM acte_visite
                WHERE code_acte=%s
                  AND date_sortie IS NULL
                ORDER BY date_liaison DESC
                LIMIT 1
            """, (code_acte,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur get_passage_actif: {e}")
            return None
        finally:
            self.db.close()

    def get_visites_par_acte(self, code_acte: str) -> list:
        """Retourne tous les passages (toutes visites) lies a un acte."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "SELECT * FROM acte_visite WHERE code_acte=%s ORDER BY date_liaison ASC",
                (code_acte,)
            )
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur get_visites_par_acte: {e}")
            return []
        finally:
            self.db.close()

    def get_actes_en_attente_par_visite(self, code_visite: str) -> list:
        """Retourne tous les passages en attente pour une visite donnee."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT av.*, am.type_acte, am.decision_medicale
                FROM acte_visite av
                JOIN acte_medical am ON am.code_acte = av.code_acte
                WHERE av.code_visite=%s
                  AND av.date_sortie IS NULL
                ORDER BY av.date_entre ASC
            """, (code_visite,))
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur get_actes_en_attente_par_visite: {e}")
            return []
        finally:
            self.db.close()

    def get_file_attente(self, type_acte: str = None) -> list:
        """
        Retourne la file d'attente globale (tous actes en_attente).
        Si type_acte est fourni, filtre par type.
        Tries par date_entree ASC (premier arrive, premier servi).
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            if type_acte:
                cursor.execute("""
                    SELECT av.*, am.type_acte, am.decision_medicale, am.code_consultation
                    FROM acte_visite av
                    JOIN acte_medical am ON am.code_acte = av.code_acte
                    WHERE av.date_sortie IS NULL
                      AND av.date_debut_execution IS NULL
                      AND am.type_acte=%s
                    ORDER BY av.date_entre ASC
                """, (type_acte,))
            else:
                cursor.execute("""
                    SELECT av.*, am.type_acte, am.decision_medicale, am.code_consultation
                    FROM acte_visite av
                    JOIN acte_medical am ON am.code_acte = av.code_acte
                    WHERE av.date_sortie IS NULL
                      AND av.date_debut_execution IS NULL
                    ORDER BY av.date_entre ASC
                """)
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur get_file_attente: {e}")
            return []
        finally:
            self.db.close()

    def get_prochain_en_attente(self, type_acte: str = None) -> ActeVisite | None:
        """
        Retourne le prochain passage a traiter (le plus ancien en file).
        """
        file = self.get_file_attente(type_acte)
        return file[0] if file else None

    def get_en_cours(self, type_acte: str = None) -> list:
        """Retourne tous les passages actuellement en cours d'execution."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            if type_acte:
                cursor.execute("""
                    SELECT av.*, am.type_acte, am.decision_medicale
                    FROM acte_visite av
                    JOIN acte_medical am ON am.code_acte = av.code_acte
                    WHERE av.date_debut_execution IS NOT NULL
                      AND av.date_sortie IS NULL
                      AND am.type_acte=%s
                    ORDER BY av.date_debut_execution ASC
                """, (type_acte,))
            else:
                cursor.execute("""
                    SELECT av.*, am.type_acte, am.decision_medicale
                    FROM acte_visite av
                    JOIN acte_medical am ON am.code_acte = av.code_acte
                    WHERE av.date_debut_execution IS NOT NULL
                      AND av.date_sortie IS NULL
                    ORDER BY av.date_debut_execution ASC
                """)
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur get_en_cours: {e}")
            return []
        finally:
            self.db.close()

    def get_termines_par_visite(self, code_visite: str) -> list:
        """Retourne tous les passages termines pour une visite."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT * FROM acte_visite
                WHERE code_visite=%s AND date_sortie IS NOT NULL
                ORDER BY date_sortie DESC
            """, (code_visite,))
            return [self._row_to_object(r) for r in cursor.fetchall()]
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur get_termines_par_visite: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # SECTION 4 — DUREES (lecture seule, deleguees au modele)
    # =========================================================================

    def get_durees(self, id_acte_visite: int) -> dict:
        """
        Retourne les durees calculees pour un passage.
        Delegue au modele ActeVisite (calcul pur Python, sans DB).
        """
        av = self.obtenir_par_id(id_acte_visite)
        if not av:
            return {}
        return {
            "attente_minutes":   av.duree_attente_minutes(),
            "execution_minutes": av.duree_execution_minutes(),
            "totale_minutes":    av.duree_totale_minutes(),
        }

    # =========================================================================
    # SECTION 5 — DONNÉES ENRICHIES (JOIN acte_medical)
    # =========================================================================

    def get_file_attente_enrichie(self, type_acte: str = None) -> list:
        """
        File d'attente (statut_passage='en_attente') avec colonnes jointes
        depuis acte_medical : type_acte, decision_medicale, code_consultation.
        Retourne des dicts bruts (pas des objets ActeVisite).
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            if type_acte:
                cursor.execute("""
                    SELECT av.*, am.type_acte, am.decision_medicale, am.code_consultation
                    FROM acte_visite av
                    JOIN acte_medical am ON am.code_acte = av.code_acte
                    WHERE av.date_sortie IS NULL
                      AND av.date_debut_execution IS NULL
                      AND am.type_acte = %s
                    ORDER BY av.date_entre ASC
                """, (type_acte,))
            else:
                cursor.execute("""
                    SELECT av.*, am.type_acte, am.decision_medicale, am.code_consultation
                    FROM acte_visite av
                    JOIN acte_medical am ON am.code_acte = av.code_acte
                    WHERE av.date_sortie IS NULL
                      AND av.date_debut_execution IS NULL
                    ORDER BY av.date_entre ASC
                """)
            rows = cursor.fetchall()
            # Normaliser : exposer date_entree et statut_passage calculé
            for r in rows:
                r['date_entree']     = r.get('date_entre')
                r['statut_passage']  = 'en_attente'
            return rows
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur get_file_attente_enrichie: {e}")
            return []
        finally:
            self.db.close()

    def get_en_cours_enrichi(self, type_acte: str = None) -> list:
        """
        Passages en cours (statut_passage='en_cours') avec colonnes jointes.
        Retourne des dicts bruts.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            if type_acte:
                cursor.execute("""
                    SELECT av.*, am.type_acte, am.decision_medicale, am.code_consultation
                    FROM acte_visite av
                    JOIN acte_medical am ON am.code_acte = av.code_acte
                    WHERE av.date_debut_execution IS NOT NULL
                      AND av.date_sortie IS NULL
                      AND am.type_acte = %s
                    ORDER BY av.date_debut_execution ASC
                """, (type_acte,))
            else:
                cursor.execute("""
                    SELECT av.*, am.type_acte, am.decision_medicale, am.code_consultation
                    FROM acte_visite av
                    JOIN acte_medical am ON am.code_acte = av.code_acte
                    WHERE av.date_debut_execution IS NOT NULL
                      AND av.date_sortie IS NULL
                    ORDER BY av.date_debut_execution ASC
                """)
            rows = cursor.fetchall()
            for r in rows:
                r['date_entree']    = r.get('date_entre')
                r['statut_passage'] = 'en_cours'
            return rows
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur get_en_cours_enrichi: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # SECTION 6 — SUIVI PATIENTS ACTIFS (file d'attente temps réel)
    # =========================================================================

    def get_suivi_actifs(self) -> list:
        """
        Retourne tous les patients actifs (non libérés) avec leur progression complète.
        Inclut AUSSI les consultations (patients en attente/en consultation sans actes médicaux).
        Joint: visite → patients + acte_visite → acte_medical.
        Retourne des dicts bruts — un row par (visite, acte). Grouper par code_visite côté UI.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    p.code_patient,
                    p.nom,
                    p.prenom,
                    v.code_visite,
                    v.date_visite,
                    v.statut_patient,
                    v.urgent,
                    am.code_acte,
                    am.type_acte,
                    am.decision_medicale,
                    am.statut_acte,
                    av.date_entre,
                    av.date_debut_execution,
                    av.date_sortie
                FROM visite v
                JOIN patients p ON p.code_patient = v.code_patient
                LEFT JOIN acte_visite av ON av.code_visite = v.code_visite
                LEFT JOIN acte_medical am ON am.code_acte = av.code_acte
                WHERE v.statut_patient IS NOT NULL
                  AND LOWER(v.statut_patient) NOT IN (
                      'terminée', 'terminee',
                      'terminé', 'termine',
                      'payé', 'paye'
                  )
                  AND LOWER(v.statut_patient) NOT LIKE 'attente rendez-vous%'
                ORDER BY v.urgent DESC, v.date_visite ASC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"[ActeVisiteDAO] Erreur get_suivi_actifs: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # SECTION 7 — VISITE DE CONTRÔLE
    # =========================================================================

    def creer_visite_controle(self, code_acte: str, code_session: str) -> tuple:
        """
        Crée une nouvelle visite de contrôle pour un acte déjà exécuté.
        Le patient revient pour le même acte médical — il va directement
        dans le service (Attente examen/chirurgie/etc.), sans passer par
        "Attente consultation".

        Retourne (True, new_code_visite) ou (False, message_erreur).
        """
        _TYPE_TO_STATUT = {
            'examen':       'Attente examen',
            'chirurgie':    'Attente chirurgie',
            'lunette':      'Attente lunette',
            'prescription': 'Attente pharmacie',
        }
        conn = self.db.connect()
        if not conn:
            return False, "Connexion DB échouée"
        try:
            cursor = conn.cursor(DictCursor)
            now = datetime.now()

            # 1. Récupérer type_acte + code_visite d'origine via l'acte_visite le plus récent
            cursor.execute("""
                SELECT av.code_visite, am.type_acte, v.code_patient, v.urgent
                FROM acte_visite av
                JOIN acte_medical am ON am.code_acte = av.code_acte
                JOIN visite v ON v.code_visite = av.code_visite
                WHERE av.code_acte = %s
                ORDER BY av.date_liaison DESC
                LIMIT 1
            """, (code_acte,))
            row = cursor.fetchone()
            if not row:
                return False, "Acte ou visite introuvable"

            type_acte    = (row.get('type_acte') or '').lower()
            code_patient = row.get('code_patient')
            urgent       = row.get('urgent', 0)
            nouveau_statut = _TYPE_TO_STATUT.get(type_acte)
            if not nouveau_statut:
                return False, f"Type d'acte inconnu : {type_acte}"

            # 2. Générer un nouveau code_visite
            cursor.execute(
                "SELECT code_visite FROM visite ORDER BY code_visite DESC LIMIT 1"
            )
            last_row = cursor.fetchone()
            if last_row:
                last_code = last_row.get('code_visite') if isinstance(last_row, dict) else last_row[0]
                if last_code and last_code.startswith('VIST'):
                    try:
                        last_num = int(last_code[4:])
                        new_code_visite = f"VIST{last_num + 1:03d}"
                    except (ValueError, TypeError):
                        # Si parsing échoue, utiliser compteur depuis la base
                        cursor.execute("SELECT COUNT(*) FROM visite")
                        count = cursor.fetchone()
                        total = (count[0] if isinstance(count, tuple) else count.get('COUNT(*)', 0)) + 1
                        new_code_visite = f"VIST{total:03d}"
                else:
                    # Format inattendu, compter les visites
                    cursor.execute("SELECT COUNT(*) FROM visite")
                    count = cursor.fetchone()
                    total = (count[0] if isinstance(count, tuple) else count.get('COUNT(*)', 0)) + 1
                    new_code_visite = f"VIST{total:03d}"
            else:
                new_code_visite = "VIST001"

            # 3. Créer la nouvelle visite de contrôle
            cursor.execute("""
                INSERT INTO visite (
                    code_visite, code_patient, code_session,
                    type_visite, statut_visite, statut_patient,
                    urgent, date_visite
                ) VALUES (%s, %s, %s, 'controle', 'en cours', %s, %s, %s)
            """, (new_code_visite, code_patient, code_session,
                  nouveau_statut, urgent, now))

            # 4. Créer l'acte_visite role='controle' lié à la nouvelle visite
            cursor.execute("""
                INSERT INTO acte_visite
                    (code_acte, code_visite, role_visite, date_liaison, date_entre)
                VALUES (%s, %s, 'controle', %s, %s)
            """, (code_acte, new_code_visite, now, now))

            conn.commit()
            return True, new_code_visite

        except Exception as e:
            conn.rollback()
            print(f"[ActeVisiteDAO] Erreur creer_visite_controle: {e}")
            return False, str(e)
        finally:
            self.db.close()

    # =========================================================================
    # METHODES PRIVEES
    # =========================================================================

    def _row_to_object(self, row: dict) -> ActeVisite:
        """Convertit une ligne DB (dict) en objet ActeVisite.
        Note: La colonne DB est 'date_entre', mappée vers 'date_entree' du modèle.
        """
        return ActeVisite(
            id_acte_visite       = row.get('id_acte_visite'),
            code_acte            = row.get('code_acte'),
            code_visite          = row.get('code_visite'),
            role_visite          = row.get('role_visite'),
            date_liaison         = row.get('date_liaison'),
            date_entree          = row.get('date_entre'),  # Mapping DB -> Modèle
            date_debut_execution = row.get('date_debut_execution'),
            date_sortie          = row.get('date_sortie'),
            statut_passage       = (
                'termine'  if row.get('date_sortie') else
                'en_cours' if row.get('date_debut_execution') else
                'en_attente'
            ),
        )
