import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
import calendar
from core.connexion_db import DBConnection
from models.modeles_examen import Examen
from datetime import datetime
DictCursor = pymysql.cursors.DictCursor


class ExamenDAO:
    """
    Classe DAO pour la gestion des examens.
    Architecture MVC : acces aux donnees uniquement.
    """

    def __init__(self):
        self.db = DBConnection()

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def ajouter(self, examen: Examen) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            examen.code = self._generer_code(cursor)
            query = """
                INSERT INTO examen (
                    code, libelle_examen, frais_examen,
                    statut_facture, date_examen,
                    code_session, code_personnel, code_acte,
                    interpreter_par, date_interpretation, conclusion_medicale
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                examen.code,
                examen.libelle_examen,
                examen.frais_examen,
                examen.statut_facture,
                examen.date_examen,
                examen.code_session,
                examen.code_personnel,
                examen.code_acte,
                examen.interpreter_par,
                examen.date_interpretation,
                examen.conclusion_medicale
            ))

            # Mise à jour du statut_patient dans visite vers le service suivant
            nouveau_statut, code_visite = self._determiner_statut_et_visite(cursor, examen.code_acte)
            if nouveau_statut and code_visite:
                cursor.execute(
                    "UPDATE visite SET statut_patient=%s WHERE code_visite=%s",
                    (nouveau_statut, code_visite)
                )
            
            conn.commit()
            return True
        except Exception as e:
            print(f"[ExamenDAO] Erreur ajouter: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier(self, examen: Examen) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            query = """
                UPDATE examen SET
                    libelle_examen=%s, frais_examen=%s,
                    statut_facture=%s, date_examen=%s,
                    code_session=%s, code_personnel=%s,
                    code_acte=%s, interpreter_par=%s,
                    date_interpretation=%s, conclusion_medicale=%s
                WHERE code=%s
            """
            cursor.execute(query, (
                examen.libelle_examen,
                examen.frais_examen,
                examen.statut_facture,
                examen.date_examen,
                examen.code_session,
                examen.code_personnel,
                examen.code_acte,
                examen.interpreter_par,
                examen.date_interpretation,
                examen.conclusion_medicale,
                examen.code
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ExamenDAO] Erreur modifier: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def supprimer(self, code: str) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM examen WHERE code=%s", (code,))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ExamenDAO] Erreur supprimer: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            # On ajoute la jointure ici aussi pour que l'objet soit complet
            query = """
                SELECT e.*, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM examen e
                LEFT JOIN acte_medical am ON e.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE e.code=%s
            """
            cursor.execute(query, (code,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ExamenDAO] Erreur obtenir_par_code: {e}")
            return None
        finally:
            self.db.close()

    def obtenir_par_acte(self, code_acte: str):
        """Retourne l examen lie a un acte medical."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM examen WHERE code_acte=%s", (code_acte,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ExamenDAO] Erreur obtenir_par_acte: {e}")
            return None
        finally:
            self.db.close()

    def obtenir_par_visite(self, code_visite: str):
        """Retourne l examen lie a une visite (via acte_medical → consultation)."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            query = """
                SELECT e.* FROM examen e
                INNER JOIN acte_medical am ON e.code_acte = am.code_acte
                INNER JOIN consultation c  ON am.code_consultation = c.code
                WHERE c.code_visite = %s
            """
            cursor.execute(query, (code_visite,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ExamenDAO] Erreur obtenir_par_visite: {e}")
            return None
        finally:
            self.db.close()

    def lister_par_session(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn: return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT e.*,
                       p.nom AS patient_nom, p.prenom AS patient_prenom,
                       p.telephone AS patient_telephone,
                       per.nom AS personnel_nom, per.prenom AS personnel_prenom,
                       per.fonction AS personnel_fonction
                FROM examen e
                LEFT JOIN acte_medical am ON e.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                LEFT JOIN personnel per   ON e.code_personnel = per.code
                WHERE e.code_session=%s 
                ORDER BY e.date_examen DESC
            """
            cursor.execute(query, (code_session,))
            rows = cursor.fetchall()
            # On passe la ligne entière à _row_to_object
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[ExamenDAO] Erreur lister_par_session: {e}")
            return []
        finally:
            self.db.close()

    def rechercher_par_critere(self, critere: str, code_session: str) -> list:
        conn = self.db.connect()
        if not conn: return []
        try:
            cursor = conn.cursor()
            critere_like = f"%{critere}%"
            query = """
                SELECT e.*, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM examen e
                LEFT JOIN acte_medical am ON e.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE e.code_session=%s
                AND (
                    e.code LIKE %s OR 
                    e.libelle_examen LIKE %s OR 
                    p.nom LIKE %s OR 
                    p.prenom LIKE %s
                )
                ORDER BY e.date_examen DESC
            """
            cursor.execute(query, (code_session, critere_like, critere_like, critere_like, critere_like))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[ExamenDAO] Erreur rechercher_par_critere: {e}")
            return []
        finally:
            self.db.close()

    def examen_complet(self, code_examen: str):
        """Retourne un examen avec infos patient et personnel (JOIN)."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    e.*,
                    p.nom           AS patient_nom,
                    p.prenom        AS patient_prenom,
                    p.telephone     AS patient_telephone,
                    p.adresse       AS patient_adresse,
                    p.naissance     AS patient_date_naissance,
                    per.nom         AS personnel_nom,
                    per.prenom      AS personnel_prenom,
                    per.fonction    AS personnel_fonction
                FROM examen e
                LEFT JOIN acte_medical am ON e.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                LEFT JOIN personnel per   ON e.code_personnel = per.code
                WHERE e.code = %s
            """
            cursor.execute(query, (code_examen,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[ExamenDAO] Erreur examen_complet: {e}")
            return None
        finally:
            self.db.close()

    def consultation_complete(self, code_examen: str):
        """
        Alias de compatibilite avec les interfaces construites sur consultation.
        """
        return self.examen_complet(code_examen)

    def services_lies(self, code_examen: str) -> dict:
        """
        Retourne les services lies a un examen via sa consultation associee.
        """
        conn = self.db.connect()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT code_acte FROM examen WHERE code=%s", (code_examen,))
            row = cursor.fetchone()
            if not row:
                return {}
            code_acte = row.get('code_acte') if isinstance(row, dict) else row[0]
            if not code_acte:
                return {}

            services = {}
            cursor.execute("SELECT * FROM examen WHERE code_acte=%s", (code_acte,))
            services['examens'] = cursor.fetchall()
            cursor.execute("SELECT * FROM chiururgie WHERE code_acte=%s", (code_acte,))
            services['chirurgies'] = cursor.fetchall()
            cursor.execute("SELECT * FROM lunette WHERE code_acte=%s", (code_acte,))
            services['lunettes'] = cursor.fetchall()
            cursor.execute("SELECT * FROM prescription_produit WHERE code_acte=%s", (code_acte,))
            services['prescriptions'] = cursor.fetchall()
            return services
        except Exception as e:
            print(f"[ExamenDAO] Erreur services_lies: {e}")
            return {}
        finally:
            self.db.close()

    # =========================================================================
    # METHODES STATISTIQUES CARDS (COUNT SQL)
    # =========================================================================

    def nombre_examens_aujourd_hui(self, code_session: str) -> int:
        """Card 'Examens du Jour' : COUNT SQL avec CURDATE()."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM examen
                WHERE code_session = %s
                  AND DATE(date_examen) = CURDATE()
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[ExamenDAO] Erreur nombre_examens_aujourd_hui: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_total_par_session(self, code_session: str) -> int:
        """Card 'Total Session' : COUNT SQL de tous les examens de la session."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM examen
                WHERE code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[ExamenDAO] Erreur nombre_total_par_session: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_examens_en_attente(self, code_session: str) -> int:
        """
        Card 'Examens en Attente' :
        Compte les visites avec statut_patient = 'Attente examen'
        et sans encore d'enregistrement dans la table examen.
        COUNT SQL sur la table visite — même logique que le DAO visite.
        """
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT v.code_visite) AS total
                FROM visite v
                INNER JOIN acte_visite av  ON av.code_visite = v.code_visite
                INNER JOIN acte_medical am ON am.code_acte   = av.code_acte
                                          AND am.type_acte   = 'examen'
                LEFT JOIN  examen e        ON e.code_acte    = am.code_acte
                WHERE v.code_session = %s
                AND v.statut_patient = 'Attente examen'
                AND e.code IS NULL
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[ExamenDAO] Erreur nombre_examens_en_attente: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_patients_en_attente(self, code_session: str) -> int:
        """Alias de compatibilite avec consultation."""
        return self.nombre_examens_en_attente(code_session)

    # =========================================================================
    # METHODES STATISTIQUES & GRAPHES
    # =========================================================================

    @staticmethod
    def _stats_mensuels_int() -> dict:
        return {
            'Jan': 0, 'Fév': 0, 'Mar': 0, 'Avr': 0, 'Mai': 0, 'Juin': 0,
            'Juil': 0, 'Août': 0, 'Sep': 0, 'Oct': 0, 'Nov': 0, 'Déc': 0
        }

    @staticmethod
    def _stats_mensuels_float() -> dict:
        return {
            'Jan': 0.0, 'Fév': 0.0, 'Mar': 0.0, 'Avr': 0.0, 'Mai': 0.0, 'Juin': 0.0,
            'Juil': 0.0, 'Août': 0.0, 'Sep': 0.0, 'Oct': 0.0, 'Nov': 0.0, 'Déc': 0.0
        }

    @staticmethod
    def _mois_mapping() -> dict:
        return {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Juin',
            7: 'Juil', 8: 'Août', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

    @staticmethod
    def _jours_a_considerer_pour_moyenne(annee: int, mois: int, today) -> int:
        if annee == today.year and mois == today.month:
            return today.day
        return calendar.monthrange(annee, mois)[1]

    def nombre_par_mois(self, code_session: str) -> dict:
        stats = self._stats_mensuels_int()
        mois_mapping = self._mois_mapping()
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MONTH(date_examen) AS num_mois, COUNT(*) AS total
                FROM examen WHERE code_session=%s
                GROUP BY MONTH(date_examen)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = row['total']
            return stats
        except Exception as e:
            print(f"[ExamenDAO] Erreur nombre_par_mois: {e}")
            return stats
        finally:
            self.db.close()

    def montant_examens_aujourd_hui(self, code_session: str) -> float:
        """Card 'Montant du Jour' : SUM SQL des frais examens d'aujourd'hui."""
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(frais_examen) AS total
                FROM examen
                WHERE code_session = %s
                  AND DATE(date_examen) = CURDATE()
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[ExamenDAO] Erreur montant_examens_aujourd_hui: {e}")
            return 0.0
        finally:
            self.db.close()

    def montant_examens_session(self, code_session: str) -> float:
        """Card 'Montant Session' : SUM SQL des frais examens de toute la session."""
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(frais_examen) AS total
                FROM examen
                WHERE code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[ExamenDAO] Erreur montant_examens_session: {e}")
            return 0.0
        finally:
            self.db.close()

    def montant_par_mois(self, code_session: str) -> dict:
        """Graphe 'Montant des examens par mois'."""
        stats = self._stats_mensuels_float()
        mois_mapping = self._mois_mapping()
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MONTH(date_examen) AS num_mois, 
                       SUM(frais_examen) AS total
                FROM examen 
                WHERE code_session=%s
                GROUP BY MONTH(date_examen)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = float(row['total']) if row['total'] else 0.0
            return stats
        except Exception as e:
            print(f"[ExamenDAO] Erreur montant_par_mois: {e}")
            return stats
        finally:
            self.db.close()

    def nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """
        Retourne le nombre d'examens par jour pour un mois donné.
        Jours sans activité inclus avec 0.
        """
        today = datetime.now().date()
        annee = annee or today.year
        mois = mois or today.month

        nb_jours_mois = calendar.monthrange(annee, mois)[1]
        dernier_jour = today.day if (annee == today.year and mois == today.month) else nb_jours_mois
        stats = {f"{j:02d}": 0 for j in range(1, dernier_jour + 1)}

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DAY(date_examen) AS num_jour, COUNT(*) AS total
                FROM examen
                WHERE code_session=%s
                  AND YEAR(date_examen)=%s
                  AND MONTH(date_examen)=%s
                GROUP BY DAY(date_examen)
            """, (code_session, annee, mois))
            for row in cursor.fetchall():
                j = int(row['num_jour'])
                if 1 <= j <= dernier_jour:
                    stats[f"{j:02d}"] = int(row['total']) if row['total'] else 0
            return stats
        except Exception as e:
            print(f"[ExamenDAO] Erreur nombre_par_jour: {e}")
            return stats
        finally:
            self.db.close()

    def montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """
        Retourne le montant des examens par jour pour un mois donné.
        Jours sans activité inclus avec 0.0.
        """
        today = datetime.now().date()
        annee = annee or today.year
        mois = mois or today.month

        nb_jours_mois = calendar.monthrange(annee, mois)[1]
        dernier_jour = today.day if (annee == today.year and mois == today.month) else nb_jours_mois
        stats = {f"{j:02d}": 0.0 for j in range(1, dernier_jour + 1)}

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DAY(date_examen) AS num_jour, SUM(frais_examen) AS total
                FROM examen
                WHERE code_session=%s
                  AND YEAR(date_examen)=%s
                  AND MONTH(date_examen)=%s
                GROUP BY DAY(date_examen)
            """, (code_session, annee, mois))
            for row in cursor.fetchall():
                j = int(row['num_jour'])
                if 1 <= j <= dernier_jour:
                    stats[f"{j:02d}"] = float(row['total']) if row['total'] else 0.0
            return stats
        except Exception as e:
            print(f"[ExamenDAO] Erreur montant_par_jour: {e}")
            return stats
        finally:
            self.db.close()

    def moyenne_examens_journaliers_mois(self, code_session: str) -> dict:
        """
        Moyenne journalière du nombre d'examens par mois.
        Mois courant : division par jours écoulés (1..aujourd'hui).
        Mois passés : division par nombre total de jours du mois.
        """
        stats = self._stats_mensuels_float()
        mois_mapping = self._mois_mapping()
        today = datetime.now().date()

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT YEAR(date_examen) AS annee,
                       MONTH(date_examen) AS num_mois,
                       COUNT(*) AS total_mois
                FROM examen
                WHERE code_session=%s
                GROUP BY YEAR(date_examen), MONTH(date_examen)
            """, (code_session,))

            for row in cursor.fetchall():
                num_mois = int(row['num_mois'])
                annee = int(row['annee'])
                if num_mois not in mois_mapping:
                    continue

                jours = self._jours_a_considerer_pour_moyenne(annee, num_mois, today)
                total_mois = int(row['total_mois']) if row['total_mois'] else 0
                stats[mois_mapping[num_mois]] = (float(total_mois) / jours) if jours > 0 else 0.0

            return stats
        except Exception as e:
            print(f"[ExamenDAO] Erreur moyenne_examens_journaliers_mois: {e}")
            return stats
        finally:
            self.db.close()

    def moyenne_examens_par_mois(self, code_session: str) -> dict:
        """Alias pour compatibilité."""
        return self.moyenne_examens_journaliers_mois(code_session)

    def moyenne_consultations_journalieres_mois(self, code_session: str) -> dict:
        """Alias de compatibilite (moyenne journaliere du nombre)."""
        return self.moyenne_examens_journaliers_mois(code_session)

    def moyenne_consultations_par_mois(self, code_session: str) -> dict:
        """Alias de compatibilite (moyenne journaliere du nombre)."""
        return self.moyenne_examens_par_mois(code_session)

    def moyenne_montant_journalier_mois(self, code_session: str) -> dict:
        """
        Moyenne journalière des montants d'examens par mois.
        Mois courant : division par jours écoulés.
        Mois passés : division par nombre total de jours du mois.
        """
        stats = self._stats_mensuels_float()
        mois_mapping = self._mois_mapping()
        today = datetime.now().date()

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT YEAR(date_examen) AS annee,
                       MONTH(date_examen) AS num_mois,
                       SUM(frais_examen) AS total_mois
                FROM examen
                WHERE code_session=%s
                GROUP BY YEAR(date_examen), MONTH(date_examen)
            """, (code_session,))

            for row in cursor.fetchall():
                num_mois = int(row['num_mois'])
                annee = int(row['annee'])
                if num_mois not in mois_mapping:
                    continue

                jours = self._jours_a_considerer_pour_moyenne(annee, num_mois, today)
                total_mois = float(row['total_mois']) if row['total_mois'] else 0.0
                stats[mois_mapping[num_mois]] = (total_mois / jours) if jours > 0 else 0.0

            return stats
        except Exception as e:
            print(f"[ExamenDAO] Erreur moyenne_montant_journalier_mois: {e}")
            return stats
        finally:
            self.db.close()

    def revenu_moyen_par_mois(self, code_session: str) -> dict:
        """Alias conservé pour compatibilité."""
        return self.moyenne_montant_journalier_mois(code_session)

    def resume_session(self, code_session: str) -> dict:
        return {
            'total_examens':       self.nombre_total_par_session(code_session),
            'examens_du_jour':     self.nombre_examens_aujourd_hui(code_session),
            'examens_en_attente':  self.nombre_examens_en_attente(code_session),
            'revenu_total':        self.revenu_total(code_session),
            'par_mois':            self.nombre_par_mois(code_session),
        }

    def revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        """Total des frais d examens pour une session, avec filtre date optionnel."""
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            if date_debut and date_fin:
                cursor.execute("""
                    SELECT SUM(frais_examen) AS total FROM examen
                    WHERE code_session=%s AND DATE(date_examen) BETWEEN %s AND %s
                """, (code_session, date_debut, date_fin))
            else:
                cursor.execute("""
                    SELECT SUM(frais_examen) AS total FROM examen
                    WHERE code_session=%s
                """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[ExamenDAO] Erreur revenu_total: {e}")
            return 0.0
        finally:
            self.db.close()

    def top_libelles(self, code_session: str, limite: int = 10) -> list:
        """Retourne les libelles d examens les plus frequents pour une session."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT libelle_examen, COUNT(*) AS nombre
                FROM examen
                WHERE code_session=%s AND libelle_examen IS NOT NULL
                GROUP BY libelle_examen
                ORDER BY nombre DESC LIMIT %s
            """, (code_session, limite))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ExamenDAO] Erreur top_libelles: {e}")
            return []
        finally:
            self.db.close()

    def top_diagnostics(self, code_session: str, limite: int = 10) -> list:
        """Alias de compatibilite consultation."""
        return self.top_libelles(code_session, limite)

    def examens_par_personnel(self, code_session: str) -> list:
        """Nombre d examens groupes par personnel."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT per.nom, per.prenom, COUNT(*) AS nombre,
                       SUM(e.frais_examen) AS total_frais
                FROM examen e
                INNER JOIN personnel per ON e.code_personnel = per.code
                WHERE e.code_session=%s
                GROUP BY per.code, per.nom, per.prenom
                ORDER BY nombre DESC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ExamenDAO] Erreur examens_par_personnel: {e}")
            return []
        finally:
            self.db.close()

    def consultations_par_personnel(self, code_session: str) -> list:
        """Alias de compatibilite consultation."""
        return self.examens_par_personnel(code_session)

    # =========================================================================
    # METHODES DE RECHERCHE AVANCEE & FILTRAGE
    # =========================================================================

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        """
        Recherche les examens entre deux dates (incluses).
        Retourne une liste d'objets Examen.
        """
        if not code_session:
            return []

        if hasattr(date_debut, 'strftime'):
            date_debut = date_debut.strftime('%Y-%m-%d')
        if hasattr(date_fin, 'strftime'):
            date_fin = date_fin.strftime('%Y-%m-%d')

        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT e.*, v.code_patient, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM examen e
                LEFT JOIN acte_medical am ON e.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                INNER JOIN patients p     ON v.code_patient = p.code_patient
                WHERE e.code_session=%s AND DATE(e.date_examen) BETWEEN %s AND %s
                ORDER BY e.date_examen DESC
            """
            cursor.execute(query, (code_session, date_debut, date_fin))
            result = cursor.fetchall()
            return [self._row_to_object(row) for row in result]
        except Exception as e:
            print(f"[ExamenDAO] Erreur rechercher_entre_dates: {e}")
            return []
        finally:
            self.db.close()

    def rechercher_par_libelle(self, code_session: str, libelle: str = None) -> list:
        """
        Recherche les examens selon le libellé d'examen.
        libelle peut être None (tous), ou une chaîne pour filtrer.
        Retourne une liste d'objets Examen.
        """
        if not code_session:
            return []

        conditions = ["e.code_session=%s"]
        params = [code_session]

        if libelle is not None:
            conditions.append("e.libelle_examen LIKE %s")
            params.append(f"%{libelle}%")

        where_clause = " AND ".join(conditions)

        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = f"""
                SELECT e.*, v.code_patient, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM examen e
                LEFT JOIN acte_medical am ON e.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                INNER JOIN patients p     ON v.code_patient = p.code_patient
                WHERE {where_clause}
                ORDER BY e.date_examen DESC
            """
            cursor.execute(query, tuple(params))
            result = cursor.fetchall()
            return [self._row_to_object(row) for row in result]
        except Exception as e:
            print(f"[ExamenDAO] Erreur rechercher_par_libelle: {e}")
            return []
        finally:
            self.db.close()

    def nombre_par_mois_filtre(self, code_session: str, libelle: str = None) -> dict:
        """
        Retourne le nombre d'examens par mois avec filtre optionnel sur le libellé.
        Format : { "Jan": 5, "Fév": 3, ... }
        """
        stats = self._stats_mensuels_int()
        mois_mapping = self._mois_mapping()

        conditions = ["e.code_session=%s"]
        params = [code_session]

        if libelle is not None:
            conditions.append("e.libelle_examen LIKE %s")
            params.append(f"%{libelle}%")

        where_clause = " AND ".join(conditions)

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor(DictCursor)
            query = f"""
                SELECT MONTH(e.date_examen) AS num_mois, COUNT(*) AS total
                FROM examen e
                WHERE {where_clause}
                GROUP BY MONTH(e.date_examen)
            """
            cursor.execute(query, tuple(params))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = row['total']
            return stats
        except Exception as e:
            print(f"[ExamenDAO] Erreur nombre_par_mois_filtre: {e}")
            return stats
        finally:
            self.db.close()

    def examens_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        """
        Retourne le nombre d'examens par mois pour un patient (ou tous).
        Si code_patient fourni : { "Jan": 2, "Fév": 1, ... }
        Sinon : { "Jan": { "P001": 2, ... }, ... }
        """
        stats = self._stats_mensuels_int()
        mois_mapping = self._mois_mapping()

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor(DictCursor)

            if code_patient:
                query = """
                    SELECT MONTH(e.date_examen) AS num_mois, COUNT(*) AS total
                    FROM examen e
                    LEFT JOIN acte_medical am ON e.code_acte = am.code_acte
                    LEFT JOIN consultation c  ON am.code_consultation = c.code
                    LEFT JOIN visite v        ON c.code_visite = v.code_visite
                    WHERE e.code_session=%s AND v.code_patient=%s
                    GROUP BY MONTH(e.date_examen)
                """
                cursor.execute(query, (code_session, code_patient))
                for row in cursor.fetchall():
                    m = row['num_mois']
                    if m in mois_mapping:
                        stats[mois_mapping[m]] = row['total']
            else:
                query = """
                    SELECT MONTH(e.date_examen) AS num_mois,
                           v.code_patient,
                           COUNT(*) AS total
                    FROM examen e
                    LEFT JOIN acte_medical am ON e.code_acte = am.code_acte
                    LEFT JOIN consultation c  ON am.code_consultation = c.code
                    LEFT JOIN visite v        ON c.code_visite = v.code_visite
                    WHERE e.code_session=%s
                    GROUP BY MONTH(e.date_examen), v.code_patient
                """
                cursor.execute(query, (code_session,))

                stats_by_patient = {}
                for row in cursor.fetchall():
                    m = row['num_mois']
                    if m in mois_mapping:
                        mois_label = mois_mapping[m]
                        if mois_label not in stats_by_patient:
                            stats_by_patient[mois_label] = {}
                        stats_by_patient[mois_label][row['code_patient']] = row['total']

                # Retourner stats_by_patient même s'il est vide (cohérence avec chirurgie)
                stats = stats_by_patient

            return stats
        except Exception as e:
            print(f"[ExamenDAO] Erreur examens_par_patient_par_mois: {e}")
            return stats
        finally:
            self.db.close()

    def consultations_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        """Alias de compatibilite consultation."""
        return self.examens_par_patient_par_mois(code_session, code_patient)

    def codes_patients_session(self, code_session: str) -> list:
        """
        Retourne la liste de tous les patients.
        Le champ a_eu_examen indique s'ils ont déjà un examen dans la session.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT p.code_patient, p.nom, p.prenom,
                       CASE WHEN EXISTS(
                           SELECT 1
                           FROM examen ex
                           INNER JOIN acte_medical am2 ON ex.code_acte = am2.code_acte
                           INNER JOIN consultation c2  ON am2.code_consultation = c2.code
                           INNER JOIN visite v2        ON c2.code_visite = v2.code_visite
                           WHERE v2.code_patient = p.code_patient AND v2.code_session = %s
                       ) THEN 1 ELSE 0 END AS a_eu_examen
                FROM patients p
                ORDER BY p.nom ASC, p.prenom ASC
            """
            cursor.execute(query, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ExamenDAO] Erreur codes_patients_session: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # METHODES PATIENTS
    # =========================================================================

    def patients_en_attente_examen(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT DISTINCT
                    v.code_visite,
                    v.date_visite,
                    v.type_visite,
                    v.urgent,
                    v.statut_patient,
                    c.code          AS code_consultation,
                    c.date_consultation,
                    c.diagnostique,
                    am.code_acte    AS code_acte,
                    p.code_patient,
                    p.nom,
                    p.prenom,
                    p.telephone
                FROM visite v
                INNER JOIN patients p       ON v.code_patient = p.code_patient
                INNER JOIN acte_visite av   ON av.code_visite = v.code_visite
                INNER JOIN acte_medical am  ON am.code_acte   = av.code_acte
                                           AND am.type_acte   = 'examen'
                LEFT JOIN  consultation c   ON c.code          = am.code_consultation
                WHERE v.code_session = %s
                AND v.statut_patient IN ('Attente examen', 'En examen')
                AND NOT EXISTS (
                    SELECT 1 FROM examen ex WHERE ex.code_acte = am.code_acte
                )
                ORDER BY v.urgent DESC, v.date_visite ASC
            """
            cursor.execute(query, (code_session,))
            rows = cursor.fetchall()
            print(f"[ExamenDAO] patients_en_attente_examen({code_session}): {len(rows)} résultat(s)")
            return rows
        except Exception as e:
            print(f"[ExamenDAO] ERREUR patients_en_attente_examen: {e}")
            import traceback; traceback.print_exc()
            return []
        finally:
            self.db.close()

    def patients_en_attente(self, code_session: str) -> list:
        """Alias de compatibilite consultation."""
        return self.patients_en_attente_examen(code_session)

    def patients_pour_examen(self, code_session: str) -> list:
        return self.patients_en_attente_examen(code_session)

    def historique_patient(self, code_patient: str) -> list:
        """Retourne l historique complet des examens d un patient."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT e.*, per.nom AS personnel_nom, per.prenom AS personnel_prenom
                FROM examen e
                LEFT JOIN acte_medical am ON e.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN personnel per   ON e.code_personnel = per.code
                WHERE v.code_patient = %s
                ORDER BY e.date_examen DESC
            """
            cursor.execute(query, (code_patient,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ExamenDAO] Erreur historique_patient: {e}")
            return []
        finally:
            self.db.close()

    def lister_personnel(self) -> list:
        """Retourne la liste de tout le personnel medical."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT code, nom, prenom, fonction
                FROM personnel
                ORDER BY nom ASC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"[ExamenDAO] Erreur lister_personnel: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # METHODES PRIVEES
    # =========================================================================

    def _generer_code(self, cursor) -> str:
        """Genere un code unique (ex: EXM001)."""
        try:
            cursor.execute("SELECT code FROM examen ORDER BY code DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                last_code = row['code'] if isinstance(row, dict) else row[0]
                last_num  = int(last_code[3:])
                return f"EXM{last_num + 1:03d}"
            else:
                return "EXM001"
        except Exception as e:
            print(f"Erreur generation code examen: {e}")
            return "EXM" + datetime.now().strftime("%H%M%S")

    def _row_to_object(self, row) -> Examen:
        obj = Examen(
            code                 = row['code'],
            libelle_examen       = row['libelle_examen'],
            frais_examen         = row['frais_examen'],
            statut_facture       = row['statut_facture'],
            date_examen          = row['date_examen'],
            code_session         = row['code_session'],
            code_personnel       = row['code_personnel'],
            code_acte            = row['code_acte'],
            interpreter_par      = row.get('interpreter_par'),
            date_interpretation  = row.get('date_interpretation'),
            conclusion_medicale  = row.get('conclusion_medicale')
        )
        # Infos patient ajoutées dynamiquement si présentes dans la ligne
        obj.patient_nom       = row.get('patient_nom', "")
        obj.patient_prenom    = row.get('patient_prenom', "")
        obj.patient_telephone = row.get('patient_telephone', "")
        obj.personnel_nom     = row.get('personnel_nom', "")
        obj.personnel_prenom  = row.get('personnel_prenom', "")
        obj.personnel_fonction= row.get('personnel_fonction', "")
        return obj
    
    def _determiner_statut_et_visite(self, cursor, code_acte: str) -> tuple:
        """Récupère le code_visite d'exécution via acte_visite (role='execution').
        Retourne toujours 'Examen terminé' : le médecin décide ensuite de la suite
        (nouvel acte ou paiement) depuis la vue acte_médical.
        
        IMPORTANT : On met à jour UNIQUEMENT la visite d'exécution (role='execution'),
        PAS la visite d'origine (role='origine') pour éviter la duplication dans la file d'attente.
        """
        try:
            # Récupérer le code_visite d'exécution depuis acte_visite avec role='execution'
            cursor.execute(
                "SELECT code_visite FROM acte_visite WHERE code_acte=%s AND role_visite='execution' LIMIT 1",
                (code_acte,)
            )
            row = cursor.fetchone()
            if not row:
                # Si pas de visite d'exécution, récupérer depuis la consultation (cas acte "maintenant")
                cursor.execute(
                    "SELECT code_consultation FROM acte_medical WHERE code_acte=%s",
                    (code_acte,)
                )
                row_cons = cursor.fetchone()
                if not row_cons:
                    return "Examen terminé", None
                code_consultation = row_cons.get('code_consultation') if isinstance(row_cons, dict) else row_cons[0]
                if not code_consultation:
                    return "Examen terminé", None
                cursor.execute(
                    "SELECT code_visite FROM consultation WHERE code=%s",
                    (code_consultation,)
                )
                row_visite = cursor.fetchone()
                if not row_visite:
                    return "Examen terminé", None
                code_visite = row_visite.get('code_visite') if isinstance(row_visite, dict) else row_visite[0]
                return "Examen terminé", code_visite
            
            code_visite = row.get('code_visite') if isinstance(row, dict) else row[0]
            return "Examen terminé", code_visite
        except Exception as e:
            print(f"[ExamenDAO] Erreur _determiner_statut_et_visite: {e}")
            return "Examen terminé", None



