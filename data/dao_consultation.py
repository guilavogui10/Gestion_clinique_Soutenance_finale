import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
import calendar
from core.connexion_db import DBConnection
from models.modele_consultation import Consultation
from datetime import datetime
DictCursor = pymysql.cursors.DictCursor


class ConsultationDAO:
    """
    Classe DAO pour la gestion des consultations.
    Architecture MVC : accès aux données uniquement.
    """

    def __init__(self):
        self.db = DBConnection()

    # =========================================================================
    # MÉTHODES CRUD
    # =========================================================================

    def ajouter(self, consultation: Consultation) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            consultation.code = self._generer_code(cursor)
            query = """
                INSERT INTO consultation (
                    code, diagnostique,
                    frais_consultation, statut_facture, date_consultation,
                    code_visite, code_session, code_personnel
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                consultation.code,
                consultation.diagnostique,
                consultation.frais_consultation,
                consultation.statut_facture,
                consultation.date_consultation,
                consultation.code_visite,
                consultation.code_session,
                consultation.code_personne
            ))
            
            # Mettre à jour le statut du patient : consultation terminée
            cursor.execute(
                "UPDATE visite SET statut_patient = %s WHERE code_visite = %s",
                ('Consultation terminée', consultation.code_visite)
            )
            
            conn.commit()
            return True
        except Exception as e:
            print(f"[ConsultationDAO] Erreur ajouter: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier(self, consultation: Consultation) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            query = """
                UPDATE consultation SET
                    diagnostique=%s,
                    frais_consultation=%s, statut_facture=%s, date_consultation=%s,
                    code_visite=%s, code_session=%s, code_personnel=%s
                WHERE code=%s
            """
            cursor.execute(query, (
                consultation.diagnostique,
                consultation.frais_consultation,
                consultation.statut_facture,
                consultation.date_consultation,
                consultation.code_visite,
                consultation.code_session,
                consultation.code_personne,
                consultation.code
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ConsultationDAO] Erreur modifier: {e}")
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
            cursor.execute("DELETE FROM consultation WHERE code=%s", (code,))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ConsultationDAO] Erreur supprimer: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM consultation WHERE code=%s", (code,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ConsultationDAO] Erreur obtenir_par_code: {e}")
            return None
        finally:
            self.db.close()

    def obtenir_par_visite(self, code_visite: str):
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM consultation WHERE code_visite=%s", (code_visite,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ConsultationDAO] Erreur obtenir_par_visite: {e}")
            return None
        finally:
            self.db.close()

    def lister_par_session(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM consultation WHERE code_session=%s ORDER BY date_consultation DESC",
                (code_session,)
            )
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[ConsultationDAO] Erreur lister_par_session: {e}")
            return []
        finally:
            self.db.close()

    def lister_toutes(self) -> list:
        """Retourne toutes les consultations, triées par date décroissante."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM consultation ORDER BY date_consultation DESC"
            )
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[ConsultationDAO] Erreur lister_toutes: {e}")
            return []
        finally:
            self.db.close()

    def rechercher_par_critere(self, critere: str, code_session: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            critere_like = f"%{critere}%"
            query = """
                SELECT * FROM consultation
                WHERE code_session=%s
                AND (
                    code LIKE %s OR
                    DATE(date_consultation) LIKE %s OR
                    diagnostique LIKE %s
                )
                ORDER BY date_consultation DESC
            """
            cursor.execute(query, (
                code_session, critere_like, critere_like,
                critere_like
            ))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[ConsultationDAO] Erreur rechercher_par_critere: {e}")
            return []
        finally:
            self.db.close()

    def consultation_complete(self, code_consultation: str):
        """Retourne une consultation avec infos patient et personnel (JOIN)."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    c.*,
                    p.nom           AS patient_nom,
                    p.prenom        AS patient_prenom,
                    p.telephone     AS patient_telephone,
                    p.adresse       AS patient_adresse,
                    p.naissance     AS patient_date_naissance,
                    per.nom         AS personnel_nom,
                    per.prenom      AS personnel_prenom,
                    per.fonction    AS personnel_fonction
                FROM consultation c
                LEFT JOIN visite v      ON c.code_visite    = v.code_visite
                LEFT JOIN patients p    ON v.code_patient   = p.code_patient
                LEFT JOIN personnel per ON c.code_personnel = per.code
                WHERE c.code = %s
            """
            cursor.execute(query, (code_consultation,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[ConsultationDAO] Erreur consultation_complete: {e}")
            return None
        finally:
            self.db.close()

    def services_lies(self, code_consultation: str) -> dict:
        """Retourne tous les services liés à une consultation via acte_medical."""
        conn = self.db.connect()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            services = {}

            # Récupérer code_visite de la consultation
            cursor.execute("SELECT code_visite FROM consultation WHERE code=%s", (code_consultation,))
            result = cursor.fetchone()
            if not result:
                return services
            
            code_visite = result['code_visite'] if isinstance(result, dict) else result[0]

            # Examens via acte_medical
            cursor.execute("""
                SELECT e.*, a.decision_medicale, a.choix_patient, a.statu_acte
                FROM examen e
                INNER JOIN acte_medical a ON e.code_acte = a.code_acte
                WHERE a.code_visite_origine = %s
            """, (code_visite,))
            services['examens'] = cursor.fetchall()

            # Chirurgies via acte_medical
            cursor.execute("""
                SELECT c.*, a.decision_medicale, a.choix_patient, a.statu_acte
                FROM chururgie c
                INNER JOIN acte_medical a ON c.code_acte = a.code_acte
                WHERE a.code_visite_origine = %s
            """, (code_visite,))
            services['chirurgies'] = cursor.fetchall()

            # Lunettes via acte_medical
            cursor.execute("""
                SELECT l.*, a.decision_medicale, a.choix_patient, a.statu_acte
                FROM commandeslunettes l
                INNER JOIN acte_medical a ON l.code_acte = a.code_acte
                WHERE a.code_visite_origine = %s
            """, (code_visite,))
            services['lunettes'] = cursor.fetchall()

            # Prescriptions via acte_medical
            cursor.execute("""
                SELECT p.*, a.decision_medicale, a.choix_patient, a.statu_acte
                FROM prescription_produit p
                INNER JOIN acte_medical a ON p.code_acte = a.code_acte
                WHERE a.code_visite_origine = %s
            """, (code_visite,))
            services['prescriptions'] = cursor.fetchall()

            return services
        except Exception as e:
            print(f"[ConsultationDAO] Erreur services_lies: {e}")
            return {}
        finally:
            self.db.close()

    # =========================================================================
    # MÉTHODES STATISTIQUES CARDS (COUNT SQL — pas de comptage Python)
    # =========================================================================

    def nombre_consultations_aujourd_hui(self, code_session: str) -> int:
        """
        Card 'Consultations du Jour' :
        Compte via SQL les consultations créées aujourd'hui dans la session.
        CURDATE() est fourni par MySQL — aucun calcul Python.
        """
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM consultation
                WHERE code_session = %s
                  AND DATE(date_consultation) = CURDATE()
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[ConsultationDAO] Erreur nombre_consultations_aujourd_hui: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_total_par_session(self, code_session: str) -> int:
        """
        Card 'Session en Cours' :
        Compte via SQL toutes les consultations de la session (année entière).
        """
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM consultation
                WHERE code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[ConsultationDAO] Erreur nombre_total_par_session: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_patients_en_attente(self, code_session: str) -> int:
        """
        Card 'Patients en Attente' :
        Compte via SQL les patients ayant une visite SANS consultation encore.
        LEFT JOIN + IS NULL = patients enregistrés non encore consultés.
        Aucun len() Python — le COUNT est fait en base.
        """
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM visite v
                LEFT JOIN consultation c ON v.code_visite = c.code_visite
                WHERE v.code_session = %s
                  AND c.code IS NULL
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[ConsultationDAO] Erreur nombre_patients_en_attente: {e}")
            return 0
        finally:
            self.db.close()

    def montant_consultations_aujourd_hui(self, code_session: str) -> float:
        """
        Card 'Montant du Jour' :
        Retourne le montant total des consultations créées aujourd'hui.
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(frais_consultation) AS total
                FROM consultation
                WHERE code_session = %s
                  AND DATE(date_consultation) = CURDATE()
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[ConsultationDAO] Erreur montant_consultations_aujourd_hui: {e}")
            return 0.0
        finally:
            self.db.close()

    def montant_consultations_session(self, code_session: str) -> float:
        """
        Card 'Montant Session' :
        Retourne le montant total des consultations de toute la session.
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(frais_consultation) AS total
                FROM consultation
                WHERE code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[ConsultationDAO] Erreur montant_consultations_session: {e}")
            return 0.0
        finally:
            self.db.close()

    # =========================================================================
    # MÉTHODES STATISTIQUES & GRAPHES
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
        """
        Règle métier:
        - mois courant: du 1er jusqu'à aujourd'hui (inclus)
        - mois passés / futurs: nombre total de jours du mois
        """
        if annee == today.year and mois == today.month:
            return today.day
        return calendar.monthrange(annee, mois)[1]

    def nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """
        Retourne le nombre de consultations par jour pour un mois donné.
        Les jours sans activité sont inclus avec 0.
        - Si annee/mois non fournis: mois courant.
        - Pour le mois courant: jours 1..aujourd'hui.
        - Pour un autre mois: jours 1..fin du mois.
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
                SELECT DAY(date_consultation) AS num_jour, COUNT(*) AS total
                FROM consultation
                WHERE code_session=%s
                  AND YEAR(date_consultation)=%s
                  AND MONTH(date_consultation)=%s
                GROUP BY DAY(date_consultation)
            """, (code_session, annee, mois))
            for row in cursor.fetchall():
                j = int(row['num_jour'])
                if 1 <= j <= dernier_jour:
                    stats[f"{j:02d}"] = int(row['total']) if row['total'] else 0
            return stats
        except Exception as e:
            print(f"[ConsultationDAO] Erreur nombre_par_jour: {e}")
            return stats
        finally:
            self.db.close()

    def montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """
        Retourne le montant des consultations par jour pour un mois donné.
        Les jours sans activité sont inclus avec 0.
        - Si annee/mois non fournis: mois courant.
        - Pour le mois courant: jours 1..aujourd'hui.
        - Pour un autre mois: jours 1..fin du mois.
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
                SELECT DAY(date_consultation) AS num_jour, SUM(frais_consultation) AS total
                FROM consultation
                WHERE code_session=%s
                  AND YEAR(date_consultation)=%s
                  AND MONTH(date_consultation)=%s
                GROUP BY DAY(date_consultation)
            """, (code_session, annee, mois))
            for row in cursor.fetchall():
                j = int(row['num_jour'])
                if 1 <= j <= dernier_jour:
                    stats[f"{j:02d}"] = float(row['total']) if row['total'] else 0.0
            return stats
        except Exception as e:
            print(f"[ConsultationDAO] Erreur montant_par_jour: {e}")
            return stats
        finally:
            self.db.close()

    def nombre_par_mois(self, code_session: str) -> dict:
        """
        Graphe 'Nombre de consultations par mois' :
        Retourne le nombre de consultations pour chaque mois de l'année.
        """
        stats = self._stats_mensuels_int()
        mois_mapping = self._mois_mapping()
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MONTH(date_consultation) AS num_mois, COUNT(*) AS total
                FROM consultation WHERE code_session=%s
                GROUP BY MONTH(date_consultation)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = row['total']
            return stats
        except Exception as e:
            print(f"[ConsultationDAO] Erreur nombre_par_mois: {e}")
            return stats
        finally:
            self.db.close()

    def montant_par_mois(self, code_session: str) -> dict:
        """
        Graphe 'Montant des consultations par mois' :
        Retourne le montant total des consultations pour chaque mois.
        """
        stats = self._stats_mensuels_float()
        mois_mapping = self._mois_mapping()
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MONTH(date_consultation) AS num_mois, 
                       SUM(frais_consultation) AS total
                FROM consultation 
                WHERE code_session=%s
                GROUP BY MONTH(date_consultation)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = float(row['total']) if row['total'] else 0.0
            return stats
        except Exception as e:
            print(f"[ConsultationDAO] Erreur montant_par_mois: {e}")
            return stats
        finally:
            self.db.close()

    def revenu_moyen_par_mois(self, code_session: str) -> dict:
        """
        Moyenne journalière des montants de consultations par mois.
        Important: on divise par le nombre de jours du mois en incluant
        les jours sans activité.
        - Mois courant: division par le nombre de jours écoulés (1..aujourd'hui)
        - Mois passés: division par le nombre total de jours du mois
        """
        return self.moyenne_montant_journalier_mois(code_session)

    def moyenne_montant_journalier_mois(self, code_session: str) -> dict:
        """
        Retourne la moyenne journalière des montants par mois (jours sans activité inclus).
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
                SELECT YEAR(date_consultation) AS annee,
                       MONTH(date_consultation) AS num_mois,
                       SUM(frais_consultation) AS total_mois
                FROM consultation
                WHERE code_session=%s
                GROUP BY YEAR(date_consultation), MONTH(date_consultation)
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
            print(f"[ConsultationDAO] Erreur moyenne_montant_journalier_mois: {e}")
            return stats
        finally:
            self.db.close()

    def moyenne_consultations_journalieres_mois(self, code_session: str) -> dict:
        """
        Retourne la moyenne journalière du nombre de consultations par mois
        (jours sans activité inclus).
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
                SELECT YEAR(date_consultation) AS annee,
                       MONTH(date_consultation) AS num_mois,
                       COUNT(*) AS total_mois
                FROM consultation
                WHERE code_session=%s
                GROUP BY YEAR(date_consultation), MONTH(date_consultation)
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
            print(f"[ConsultationDAO] Erreur moyenne_consultations_journalieres_mois: {e}")
            return stats
        finally:
            self.db.close()

    def moyenne_consultations_par_mois(self, code_session: str) -> dict:
        """
        Alias conservé pour compatibilité.
        Retourne la moyenne journalière du nombre de consultations par mois.
        """
        return self.moyenne_consultations_journalieres_mois(code_session)

    def resume_session(self, code_session: str) -> dict:
        return {
            'total_consultations':   self.nombre_total_par_session(code_session),
            'consultations_du_jour': self.nombre_consultations_aujourd_hui(code_session),
            'patients_en_attente':   self.nombre_patients_en_attente(code_session),
            'revenu_total':          self.revenu_total(code_session),
            'par_mois':              self.nombre_par_mois(code_session),
            'taux_services':         self.taux_conversion_services(code_session),
        }

    def revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            if date_debut and date_fin:
                cursor.execute("""
                    SELECT SUM(frais_consultation) AS total FROM consultation
                    WHERE code_session=%s AND DATE(date_consultation) BETWEEN %s AND %s
                """, (code_session, date_debut, date_fin))
            else:
                cursor.execute("""
                    SELECT SUM(frais_consultation) AS total FROM consultation
                    WHERE code_session=%s
                """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[ConsultationDAO] Erreur revenu_total: {e}")
            return 0.0
        finally:
            self.db.close()

    def taux_conversion_services(self, code_session: str) -> dict:
        """Calcule le taux de conversion des services via acte_medical."""
        conn = self.db.connect()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) AS total FROM consultation WHERE code_session=%s",
                (code_session,)
            )
            total = cursor.fetchone()['total']
            if total == 0:
                return {'examen': 0.0, 'chirurgie': 0.0, 'lunette': 0.0, 'prescription': 0.0}

            services = {
                'examen': 'examen',
                'chirurgie': 'chirurgie',
                'lunette': 'lunette',
                'prescription': 'prescription'
            }
            taux = {}
            for nom, type_acte in services.items():
                cursor.execute("""
                    SELECT COUNT(DISTINCT c.code) AS nb
                    FROM consultation c
                    INNER JOIN visite v ON c.code_visite = v.code_visite
                    INNER JOIN acte_medical a ON v.code_visite = a.code_visite_origine
                    WHERE c.code_session=%s AND a.type_acte=%s
                """, (code_session, type_acte))
                nb = cursor.fetchone()['nb']
                taux[nom] = round((nb / total) * 100, 2)
            return taux
        except Exception as e:
            print(f"[ConsultationDAO] Erreur taux_conversion_services: {e}")
            return {}
        finally:
            self.db.close()

    def top_diagnostics(self, code_session: str, limite: int = 10) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT diagnostique, COUNT(*) AS nombre
                FROM consultation
                WHERE code_session=%s AND diagnostique IS NOT NULL
                GROUP BY diagnostique
                ORDER BY nombre DESC LIMIT %s
            """, (code_session, limite))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ConsultationDAO] Erreur top_diagnostics: {e}")
            return []
        finally:
            self.db.close()

    def consultations_par_personnel(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT per.nom, per.prenom, COUNT(*) AS nombre,
                       SUM(c.frais_consultation) AS total_frais
                FROM consultation c
                INNER JOIN personnel per ON c.code_personnel = per.code
                WHERE c.code_session=%s
                GROUP BY per.code, per.nom, per.prenom
                ORDER BY nombre DESC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ConsultationDAO] Erreur consultations_par_personnel: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # MÉTHODES PATIENTS (LISTES FILTRÉES)
    # =========================================================================

    def patients_en_attente(self, code_session: str) -> list:
        """Patients ayant une visite mais pas encore de consultation."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    v.code_visite,
                    v.code_session,
                    v.date_visite,
                    v.type_visite,
                    v.statut_patient,
                    v.urgent,
                    ABS(TIMESTAMPDIFF(MINUTE, v.date_visite, NOW())) AS temps_attente_minutes,
                    p.code_patient,
                    p.nom,
                    p.prenom,
                    p.telephone
                FROM visite v
                INNER JOIN patients p       ON v.code_patient  = p.code_patient
                LEFT JOIN  consultation c   ON v.code_visite   = c.code_visite
                WHERE v.code_session=%s
                  AND c.code IS NULL
                  AND v.statut_patient IN ('Attente consultation', 'En consultation')
                ORDER BY v.date_visite ASC
            """
            cursor.execute(query, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ConsultationDAO] Erreur patients_en_attente: {e}")
            return []
        finally:
            self.db.close()

    def patients_pour_examen(self, code_session: str) -> list:
        return self._patients_par_service_acte(code_session, "examen")

    def patients_pour_chirurgie(self, code_session: str) -> list:
        return self._patients_par_service_acte(code_session, "chirurgie")

    def patients_pour_lunette(self, code_session: str) -> list:
        return self._patients_par_service_acte(code_session, "lunette")

    def patients_pour_prescription(self, code_session: str) -> list:
        return self._patients_par_service_acte(code_session, "prescription")

    def historique_patient(self, code_patient: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT c.*, per.nom AS personnel_nom, per.prenom AS personnel_prenom
                FROM consultation c
                INNER JOIN visite v      ON c.code_visite    = v.code_visite
                LEFT JOIN  personnel per ON c.code_personnel = per.code
                WHERE v.code_patient = %s
                ORDER BY c.date_consultation DESC
            """
            cursor.execute(query, (code_patient,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ConsultationDAO] Erreur historique_patient: {e}")
            return []
        finally:
            self.db.close()

    def lister_personnel(self) -> list:
        """Retourne la liste de tout le personnel médical."""
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
            print(f"[ConsultationDAO] Erreur lister_personnel: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # MÉTHODES DE RECHERCHE AVANCÉE & FILTRAGE
    # =========================================================================

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        """
        Recherche les consultations entre deux dates (incluses).
        date_debut et date_fin : objet datetime.date ou str au format YYYY-MM-DD
        Retourne une liste d'objets Consultation.
        """
        if not code_session:
            return []
        
        # Convertir en string si nécessaire
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
                SELECT c.*, v.code_patient, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM consultation c
                INNER JOIN visite v ON c.code_visite = v.code_visite
                INNER JOIN patients p ON v.code_patient = p.code_patient
                WHERE c.code_session=%s AND DATE(c.date_consultation) BETWEEN %s AND %s
                ORDER BY c.date_consultation DESC
            """
            cursor.execute(query, (code_session, date_debut, date_fin))
            result = cursor.fetchall()
            return [self._row_to_object(row) for row in result]
        except Exception as e:
            print(f"[ConsultationDAO] Erreur rechercher_entre_dates: {e}")
            return []
        finally:
            self.db.close()

    def rechercher_par_services(self, code_session: str, examen=None, chirurgie=None, 
                               commandelunette=None, prescription=None) -> list:
        """
        Recherche les consultations selon les services via acte_medical.
        Chaque paramètre peut être True (inclure ce service) ou None (ignorer).
        Si plusieurs filtres sont fournis, ils sont combinés avec AND.
        Retourne une liste d'objets Consultation.
        """
        if not code_session:
            return []

        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            
            # Construction dynamique des filtres
            types_actes = []
            if examen:
                types_actes.append('examen')
            if chirurgie:
                types_actes.append('chirurgie')
            if commandelunette:
                types_actes.append('lunette')
            if prescription:
                types_actes.append('prescription')
            
            if not types_actes:
                # Aucun filtre, retourner toutes les consultations
                query = """
                    SELECT c.*, v.code_patient, p.nom AS patient_nom, p.prenom AS patient_prenom
                    FROM consultation c
                    INNER JOIN visite v ON c.code_visite = v.code_visite
                    INNER JOIN patients p ON v.code_patient = p.code_patient
                    WHERE c.code_session=%s
                    ORDER BY c.date_consultation DESC
                """
                cursor.execute(query, (code_session,))
            else:
                # Filtrer par types d'actes
                placeholders = ','.join(['%s'] * len(types_actes))
                query = f"""
                    SELECT DISTINCT c.*, v.code_patient, p.nom AS patient_nom, p.prenom AS patient_prenom
                    FROM consultation c
                    INNER JOIN visite v ON c.code_visite = v.code_visite
                    INNER JOIN patients p ON v.code_patient = p.code_patient
                    INNER JOIN acte_medical a ON v.code_visite = a.code_visite_origine
                    WHERE c.code_session=%s AND a.type_acte IN ({placeholders})
                    ORDER BY c.date_consultation DESC
                """
                cursor.execute(query, (code_session, *types_actes))
            
            result = cursor.fetchall()
            return [self._row_to_object(row) for row in result]
        except Exception as e:
            print(f"[ConsultationDAO] Erreur rechercher_par_services: {e}")
            return []
        finally:
            self.db.close()

    def consultations_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        """
        Retourne le nombre de consultations par mois pour chaque patient (ou un patient spécifique).
        Format : { "Jan": { "P001": 2, "P002": 1 }, "Fév": { ... }, ... }
        ou si code_patient est spécifié : { "Jan": 2, "Fév": 1, ... }
        """
        stats = self._stats_mensuels_int()
        mois_mapping = self._mois_mapping()
        
        conn = self.db.connect()
        if not conn:
            return stats

        try:
            cursor = conn.cursor(DictCursor)
            
            if code_patient:
                # Une patient spécifique
                query = """
                    SELECT MONTH(c.date_consultation) AS num_mois, COUNT(*) AS total
                    FROM consultation c
                    INNER JOIN visite v ON c.code_visite = v.code_visite
                    WHERE c.code_session=%s AND v.code_patient=%s
                    GROUP BY MONTH(c.date_consultation)
                """
                cursor.execute(query, (code_session, code_patient))
                for row in cursor.fetchall():
                    m = row['num_mois']
                    if m in mois_mapping:
                        stats[mois_mapping[m]] = row['total']
            else:
                # Tous les patients
                query = """
                    SELECT MONTH(c.date_consultation) AS num_mois, 
                           v.code_patient,
                           COUNT(*) AS total
                    FROM consultation c
                    INNER JOIN visite v ON c.code_visite = v.code_visite
                    WHERE c.code_session=%s
                    GROUP BY MONTH(c.date_consultation), v.code_patient
                """
                cursor.execute(query, (code_session,))
                
                # Réorganiser en dict { mois: { patient: count } }
                stats_by_patient = {}
                for row in cursor.fetchall():
                    m = row['num_mois']
                    if m in mois_mapping:
                        mois_label = mois_mapping[m]
                        if mois_label not in stats_by_patient:
                            stats_by_patient[mois_label] = {}
                        stats_by_patient[mois_label][row['code_patient']] = row['total']
                
                stats = stats_by_patient if stats_by_patient else stats
            
            return stats
        except Exception as e:
            print(f"[ConsultationDAO] Erreur consultations_par_patient_par_mois: {e}")
            return {}
        finally:
            self.db.close()

    def nombre_par_mois_filtre(self, code_session: str, examen: bool = None, 
                               chirurgie: bool = None, commandelunette: bool = None, 
                               prescription: bool = None) -> dict:
        """
        Retourne le nombre de consultations par mois avec filtres sur les services via acte_medical.
        Chaque paramètre peut être True (inclure ce service) ou None (ignorer).
        Format retourné : { "Jan": 5, "Fév": 3, ... }
        """
        stats = self._stats_mensuels_int()
        mois_mapping = self._mois_mapping()

        conn = self.db.connect()
        if not conn:
            return stats

        try:
            cursor = conn.cursor(DictCursor)
            
            # Construction dynamique des filtres
            types_actes = []
            if examen:
                types_actes.append('examen')
            if chirurgie:
                types_actes.append('chirurgie')
            if commandelunette:
                types_actes.append('lunette')
            if prescription:
                types_actes.append('prescription')
            
            if not types_actes:
                # Aucun filtre
                query = """
                    SELECT MONTH(c.date_consultation) AS num_mois, COUNT(*) AS total
                    FROM consultation c
                    WHERE c.code_session=%s
                    GROUP BY MONTH(c.date_consultation)
                """
                cursor.execute(query, (code_session,))
            else:
                # Filtrer par types d'actes
                placeholders = ','.join(['%s'] * len(types_actes))
                query = f"""
                    SELECT MONTH(c.date_consultation) AS num_mois, COUNT(DISTINCT c.code) AS total
                    FROM consultation c
                    INNER JOIN visite v ON c.code_visite = v.code_visite
                    INNER JOIN acte_medical a ON v.code_visite = a.code_visite_origine
                    WHERE c.code_session=%s AND a.type_acte IN ({placeholders})
                    GROUP BY MONTH(c.date_consultation)
                """
                cursor.execute(query, (code_session, *types_actes))
            
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = row['total']
            return stats
        except Exception as e:
            print(f"[ConsultationDAO] Erreur nombre_par_mois_filtre: {e}")
            return stats
        finally:
            self.db.close()

    def codes_patients_session(self, code_session: str) -> list:
        """
        Retourne la liste de tous les patients dans la table patients.
        Le champ a_consulte indique s'ils ont déjà une consultation dans la session donnée.
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
                           FROM consultation c
                           INNER JOIN visite v2 ON c.code_visite = v2.code_visite
                           WHERE v2.code_patient = p.code_patient AND v2.code_session = %s
                       ) THEN 1 ELSE 0 END AS a_consulte
                FROM patients p
                ORDER BY p.nom ASC, p.prenom ASC
            """
            cursor.execute(query, (code_session,))
            result = cursor.fetchall()
            return result
        except Exception as e:
            print(f"[ConsultationDAO] Erreur codes_patients_session: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # MÉTHODES PRIVÉES
    # =========================================================================

    def _patients_par_service_acte(self, code_session: str, type_acte: str) -> list:
        """Récupère les patients ayant un acte médical spécifique via acte_medical."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT DISTINCT c.code, c.date_consultation, p.nom, p.prenom, p.telephone
                FROM consultation c
                INNER JOIN visite v ON c.code_visite = v.code_visite
                INNER JOIN patients p ON v.code_patient = p.code_patient
                INNER JOIN acte_medical a ON v.code_visite = a.code_visite_origine
                WHERE c.code_session=%s AND a.type_acte=%s
                ORDER BY c.date_consultation DESC
            """
            cursor.execute(query, (code_session, type_acte))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ConsultationDAO] Erreur _patients_par_service_acte ({type_acte}): {e}")
            return []
        finally:
            self.db.close()

    def _generer_code(self, cursor) -> str:
        """
        Génère automatiquement un code unique (ex: CLS001).
        Utilise le curseur existant pour rester dans la même transaction.
        """
        try:
            cursor.execute("SELECT code FROM consultation ORDER BY code DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                last_code = row['code'] if isinstance(row, dict) else row[0]
                last_num = int(last_code[3:])
                return f"CLS{last_num + 1:03d}"
            else:
                return "CLS001"
        except Exception as e:
            print(f"Erreur génération code: {e}")
            return "CLS" + datetime.now().strftime("%H%M%S")

    def _row_to_object(self, row) -> Consultation:
        """Convertit une ligne DB en objet Consultation."""
        return Consultation(
            code                 = row['code'],
            diagnostique         = row['diagnostique'],
            frais_consultation   = row['frais_consultation'],
            statut_facture       = row['statut_facture'],
            date_consultation    = row['date_consultation'],
            code_visite          = row['code_visite'],
            code_session         = row['code_session'],
            code_personne        = row['code_personnel']
        )
    
