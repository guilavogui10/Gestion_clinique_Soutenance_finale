import os
import sys
import calendar
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.connexion_db import DBConnection
from models.modele_rendez_vous import RendezVous


class RendezVousDAO:
    """
    DAO de gestion des rendez-vous.
    Toutes les opérations sont majoritairement centrées sur code_session
    afin de faciliter le travail sur la session active.
    """

    STATUTS_ACTIFS = ("attente", "confirme", "en_cours")
    STATUTS_FINAUX = ("termine", "annule", "absent", "reporte")

    def __init__(self):
        self.db = DBConnection()

    # =========================================================================
    # GENERATION DE CODE
    # =========================================================================

    def generate_code_rendez_vous(self) -> str:
        """Genere automatiquement un code rendez-vous unique."""
        conn = self.db.connect()
        if not conn:
            return "RDV001"
        try:
            cursor = conn.cursor()
            return self._generer_code(cursor)
        except Exception:
            return "RDV001"
        finally:
            self.db.close()

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def ajouter(self, rdv: RendezVous) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            rdv.code_rendez_vous = self._generer_code(cursor)
            statut_normalise = self._normaliser_statut(rdv.statut_rendez_vous)

            if self._existe_doublon_visite(cursor, rdv.code_visite):
                return False

            if not self._personnel_est_disponible(
                cursor,
                rdv.code_personnel,
                rdv.date_rendez_vous
            ):
                return False

            query = """
                INSERT INTO rendez_vous (
                    code_rendez_vous,
                    code_visite,
                    code_personnel,
                    code_session,
                    date_rendez_vous,
                    statut_rendez_vous
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                rdv.code_rendez_vous,
                rdv.code_visite,
                rdv.code_personnel,
                rdv.code_session,
                rdv.date_rendez_vous,
                statut_normalise
            ))
            conn.commit()
            rdv.statut_rendez_vous = statut_normalise
            return True
        except Exception as e:
            print(f"[RendezVousDAO] Erreur ajouter: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier(self, rdv: RendezVous) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            statut_normalise = self._normaliser_statut(rdv.statut_rendez_vous)

            if self._existe_doublon_visite(cursor, rdv.code_visite, rdv.code_rendez_vous):
                return False

            if not self._personnel_est_disponible(
                cursor,
                rdv.code_personnel,
                rdv.date_rendez_vous,
                rdv.code_rendez_vous
            ):
                return False

            query = """
                UPDATE rendez_vous SET
                    code_visite = %s,
                    code_personnel = %s,
                    code_session = %s,
                    date_rendez_vous = %s,
                    statut_rendez_vous = %s
                WHERE code_rendez_vous = %s
            """
            cursor.execute(query, (
                rdv.code_visite,
                rdv.code_personnel,
                rdv.code_session,
                rdv.date_rendez_vous,
                statut_normalise,
                rdv.code_rendez_vous
            ))
            conn.commit()
            rdv.statut_rendez_vous = statut_normalise
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[RendezVousDAO] Erreur modifier: {e}")
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
            cursor.execute(
                "DELETE FROM rendez_vous WHERE code_rendez_vous = %s",
                (code,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[RendezVousDAO] Erreur supprimer: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # GESTION DES STATUTS
    # =========================================================================

    def changer_statut_rendez_vous(
        self,
        code_rendez_vous: str,
        nouveau_statut: str,
        code_session: str = None
    ) -> bool:
        """Change le statut d un rendez-vous."""
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            statut_normalise = self._normaliser_statut(nouveau_statut)
            query = """
                UPDATE rendez_vous
                SET statut_rendez_vous = %s
                WHERE code_rendez_vous = %s
            """
            params = [statut_normalise, code_rendez_vous]

            if code_session:
                query += " AND code_session = %s"
                params.append(code_session)

            cursor.execute(query, tuple(params))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[RendezVousDAO] Erreur changer_statut_rendez_vous: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def changer_statut(self, code_rendez_vous: str, nouveau_statut: str, code_session: str = None) -> bool:
        """Alias de compatibilite."""
        return self.changer_statut_rendez_vous(code_rendez_vous, nouveau_statut, code_session)

    def lister_par_statut(self, code_session: str, statut: str) -> list:
        """Liste les rendez-vous d une session pour un statut donne."""
        return self._lister_rendez_vous(
            code_session=code_session,
            statut=statut,
            order_by="r.date_rendez_vous ASC"
        )

    # =========================================================================
    # PLANIFICATION / DISPONIBILITE
    # =========================================================================

    def verifier_doublon_visite(self, code_visite: str, code_rendez_vous_exclu: str = None) -> bool:
        """Verifie si une visite a deja un rendez-vous."""
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            return self._existe_doublon_visite(cursor, code_visite, code_rendez_vous_exclu)
        except Exception as e:
            print(f"[RendezVousDAO] Erreur verifier_doublon_visite: {e}")
            return False
        finally:
            self.db.close()

    def verifier_disponibilite_personnel(
        self,
        code_personnel: str,
        date_rendez_vous,
        code_rendez_vous_exclu: str = None
    ) -> bool:
        """
        Verifie qu un personnel n a pas deja un rendez-vous actif au meme moment.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            return self._personnel_est_disponible(
                cursor,
                code_personnel,
                date_rendez_vous,
                code_rendez_vous_exclu
            )
        except Exception as e:
            print(f"[RendezVousDAO] Erreur verifier_disponibilite_personnel: {e}")
            return False
        finally:
            self.db.close()

    def verifier_chevauchement(
        self,
        code_personnel: str,
        date_rendez_vous,
        code_rendez_vous_exclu: str = None,
        marge_minutes: int = 30
    ) -> bool:
        """
        Verifie s il existe un rendez-vous trop proche pour un meme personnel.
        Retourne True si un chevauchement est detecte.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            statut_clause, statut_params = self._build_status_clause(
                "r.statut_rendez_vous",
                self.STATUTS_ACTIFS
            )
            query = f"""
                SELECT COUNT(*) AS total
                FROM rendez_vous r
                WHERE r.code_personnel = %s
                  AND ABS(TIMESTAMPDIFF(MINUTE, r.date_rendez_vous, %s)) < %s
                  AND {statut_clause}
            """
            params = [code_personnel, date_rendez_vous, marge_minutes] + statut_params

            if code_rendez_vous_exclu:
                query += " AND r.code_rendez_vous <> %s"
                params.append(code_rendez_vous_exclu)

            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            return (row or {}).get("total", 0) > 0
        except Exception as e:
            print(f"[RendezVousDAO] Erreur verifier_chevauchement: {e}")
            return False
        finally:
            self.db.close()

    def verifier_surcharge_personnel(
        self,
        code_personnel: str,
        code_session: str,
        date_reference=None,
        seuil_journalier: int = 12
    ) -> dict:
        """
        Mesure la charge d un agent sur une journee et indique s il est surcharge.
        """
        date_reference = date_reference or datetime.now()
        conn = self.db.connect()
        if not conn:
            return {"surcharge": False, "total": 0, "seuil": seuil_journalier}
        try:
            cursor = conn.cursor()
            statut_clause, statut_params = self._build_status_clause(
                "statut_rendez_vous",
                ("attente", "confirme", "en_cours", "termine")
            )
            query = f"""
                SELECT COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                  AND code_personnel = %s
                  AND DATE(date_rendez_vous) = DATE(%s)
                  AND {statut_clause}
            """
            params = (code_session, code_personnel, date_reference, *statut_params)
            cursor.execute(query, params)
            row = cursor.fetchone() or {}
            total = row.get("total", 0)
            return {
                "surcharge": total >= seuil_journalier,
                "total": total,
                "seuil": seuil_journalier,
                "code_personnel": code_personnel,
                "date_reference": date_reference
            }
        except Exception as e:
            print(f"[RendezVousDAO] Erreur verifier_surcharge_personnel: {e}")
            return {"surcharge": False, "total": 0, "seuil": seuil_journalier}
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
            query = f"""
                {self._base_select_query()}
                WHERE r.code_rendez_vous = %s
            """
            cursor.execute(query, (code,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[RendezVousDAO] Erreur obtenir_par_code: {e}")
            return None
        finally:
            self.db.close()

    def obtenir_par_visite(self, code_visite: str):
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            query = f"""
                {self._base_select_query()}
                WHERE r.code_visite = %s
                ORDER BY r.date_rendez_vous DESC
                LIMIT 1
            """
            cursor.execute(query, (code_visite,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[RendezVousDAO] Erreur obtenir_par_visite: {e}")
            return None
        finally:
            self.db.close()

    def lister_par_session(self, code_session: str) -> list:
        return self._lister_rendez_vous(
            code_session=code_session,
            order_by="r.date_rendez_vous DESC"
        )

    def rechercher_par_critere(self, critere: str, code_session: str) -> list:
        """Recherche transversale par code, statut, patient, personnel et date."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            like_critere = f"%{critere}%"
            query = f"""
                {self._base_select_query()}
                WHERE r.code_session = %s
                  AND (
                      r.code_rendez_vous LIKE %s
                      OR r.code_visite LIKE %s
                      OR LOWER(r.statut_rendez_vous) LIKE LOWER(%s)
                      OR p.code_patient LIKE %s
                      OR p.nom LIKE %s
                      OR p.prenom LIKE %s
                      OR CONCAT(COALESCE(p.nom, ''), ' ', COALESCE(p.prenom, '')) LIKE %s
                      OR per.code LIKE %s
                      OR per.nom LIKE %s
                      OR per.prenom LIKE %s
                      OR CONCAT(COALESCE(per.nom, ''), ' ', COALESCE(per.prenom, '')) LIKE %s
                      OR DATE_FORMAT(r.date_rendez_vous, '%%d/%%m/%%Y %%H:%%i') LIKE %s
                      OR DATE_FORMAT(r.date_rendez_vous, '%%Y-%%m-%%d') LIKE %s
                  )
                ORDER BY r.date_rendez_vous DESC
            """
            params = (
                code_session,
                like_critere, like_critere, like_critere,
                like_critere, like_critere, like_critere, like_critere,
                like_critere, like_critere, like_critere, like_critere,
                like_critere, like_critere
            )
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[RendezVousDAO] Erreur rechercher_par_critere: {e}")
            return []
        finally:
            self.db.close()

    def rechercher_par_statut(self, code_session: str, statut: str) -> list:
        return self._lister_rendez_vous(
            code_session=code_session,
            statut=statut,
            order_by="r.date_rendez_vous DESC"
        )

    def rechercher_par_patient(self, code_session: str, patient: str) -> list:
        return self._lister_rendez_vous(
            code_session=code_session,
            patient=patient,
            order_by="r.date_rendez_vous DESC"
        )

    def rechercher_par_personnel(self, code_session: str, personnel: str) -> list:
        return self._lister_rendez_vous(
            code_session=code_session,
            personnel=personnel,
            order_by="r.date_rendez_vous DESC"
        )

    def rechercher_par_date(self, code_session: str, date_rendez_vous) -> list:
        return self._lister_rendez_vous(
            code_session=code_session,
            date_exacte=date_rendez_vous,
            order_by="r.date_rendez_vous ASC"
        )

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        return self._lister_rendez_vous(
            code_session=code_session,
            date_debut=date_debut,
            date_fin=date_fin,
            order_by="r.date_rendez_vous ASC"
        )

    def lister_avec_filtres(
        self,
        code_session: str,
        statut: str = None,
        patient: str = None,
        personnel: str = None,
        date_debut=None,
        date_fin=None
    ) -> list:
        return self._lister_rendez_vous(
            code_session=code_session,
            statut=statut,
            patient=patient,
            personnel=personnel,
            date_debut=date_debut,
            date_fin=date_fin,
            order_by="r.date_rendez_vous ASC"
        )

    def rendez_vous_complet(self, code_rdv: str):
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            query = f"""
                {self._base_select_query()}
                WHERE r.code_rendez_vous = %s
            """
            cursor.execute(query, (code_rdv,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[RendezVousDAO] Erreur rendez_vous_complet: {e}")
            return None
        finally:
            self.db.close()

    # =========================================================================
    # SURVEILLANCE / MONITORING
    # =========================================================================

    def suivi_temps_reel(self, code_session: str) -> dict:
        """Vue synthese temps reel pour un tableau de bord."""
        stats_statuts = self.rendez_vous_par_statut(code_session)
        return {
            "date_generation": datetime.now(),
            "total": self.nombre_total_par_session(code_session),
            "aujourd_hui": self.nombre_rdv_aujourd_hui(code_session),
            "en_retard": self.nombre_rdv_en_retard(code_session),
            "taux_presence": self.taux_presence(code_session),
            "taux_conversion": self.taux_conversion_presence_absence(code_session),
            "par_statut": stats_statuts,
            "proches": self.rendez_vous_proches(code_session, delai_minutes=60),
            "oublies": self.rendez_vous_oublies(code_session, marge_minutes=30)
        }

    def nombre_total_par_session(self, code_session: str) -> int:
        return self._count_simple(
            """
            SELECT COUNT(*) AS total
            FROM rendez_vous
            WHERE code_session = %s
            """,
            (code_session,)
        )

    def nombre_par_statut(self, code_session: str, statut: str) -> int:
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            statut_clause, statut_params = self._build_status_clause("statut_rendez_vous", statut)
            query = f"""
                SELECT COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                  AND {statut_clause}
            """
            cursor.execute(query, (code_session, *statut_params))
            row = cursor.fetchone()
            return (row or {}).get("total", 0)
        except Exception as e:
            print(f"[RendezVousDAO] Erreur nombre_par_statut: {e}")
            return 0
        finally:
            self.db.close()

    def rendez_vous_par_statut(self, code_session: str) -> dict:
        """Retourne le nombre de rendez-vous par statut normalise."""
        conn = self.db.connect()
        resultat = {
            "attente": 0,
            "confirme": 0,
            "en_cours": 0,
            "termine": 0,
            "annule": 0,
            "absent": 0,
            "reporte": 0,
            "autre": 0
        }
        if not conn:
            return resultat
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT statut_rendez_vous, COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                GROUP BY statut_rendez_vous
            """, (code_session,))
            for row in cursor.fetchall():
                cle = self._normaliser_statut(row.get("statut_rendez_vous"))
                resultat[cle] = resultat.get(cle, 0) + row.get("total", 0)
            return resultat
        except Exception as e:
            print(f"[RendezVousDAO] Erreur rendez_vous_par_statut: {e}")
            return resultat
        finally:
            self.db.close()

    def nombre_rdv_aujourd_hui(self, code_session: str) -> int:
        return self._count_simple(
            """
            SELECT COUNT(*) AS total
            FROM rendez_vous
            WHERE code_session = %s
              AND DATE(date_rendez_vous) = CURDATE()
            """,
            (code_session,)
        )

    def nombre_rdv_en_attente(self, code_session: str) -> int:
        return self.nombre_par_statut(code_session, "attente")

    def nombre_rdv_confirmes(self, code_session: str) -> int:
        return self.nombre_par_statut(code_session, "confirme")

    def nombre_rdv_termines(self, code_session: str) -> int:
        return self.nombre_par_statut(code_session, "termine")

    def nombre_rdv_annules(self, code_session: str) -> int:
        return self.nombre_par_statut(code_session, "annule")

    def nombre_rdv_reportes(self, code_session: str) -> int:
        return self.nombre_par_statut(code_session, "reporte")

    def nombre_rdv_absents(self, code_session: str) -> int:
        return self.nombre_par_statut(code_session, "absent")

    def nombre_rdv_en_retard(self, code_session: str) -> int:
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            statut_clause, statut_params = self._build_status_clause(
                "statut_rendez_vous",
                ("attente", "confirme", "en_cours")
            )
            query = f"""
                SELECT COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                  AND date_rendez_vous < NOW()
                  AND {statut_clause}
            """
            cursor.execute(query, (code_session, *statut_params))
            row = cursor.fetchone()
            return (row or {}).get("total", 0)
        except Exception as e:
            print(f"[RendezVousDAO] Erreur nombre_rdv_en_retard: {e}")
            return 0
        finally:
            self.db.close()

    def taux_conversion_presence_absence(self, code_session: str) -> float:
        """
        % de patients venus par rapport aux rendez-vous conclus (venus + absents).
        Venus = termine ou en_cours.
        """
        venus = self.nombre_par_statut(code_session, "termine") + self.nombre_par_statut(code_session, "en_cours")
        absents = self.nombre_par_statut(code_session, "absent")
        total_conclus = venus + absents
        if total_conclus == 0:
            return 0.0
        return round((venus / total_conclus) * 100, 2)

    def taux_presence(self, code_session: str) -> float:
        """
        Taux de presence sur les rendez-vous deja echus et non annules/reportes.
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            statut_clause, statut_params = self._build_status_clause(
                "statut_rendez_vous",
                ("attente", "confirme", "en_cours", "termine", "absent")
            )
            query = f"""
                SELECT
                    SUM(CASE WHEN {self._status_case_sql('statut_rendez_vous', 'termine', 'en_cours')} THEN 1 ELSE 0 END) AS venus,
                    SUM(CASE WHEN {self._status_case_sql('statut_rendez_vous', 'absent')} THEN 1 ELSE 0 END) AS absents
                FROM rendez_vous
                WHERE code_session = %s
                  AND date_rendez_vous <= NOW()
                  AND {statut_clause}
            """
            cursor.execute(query, (code_session, *statut_params))
            row = cursor.fetchone() or {}
            venus = row.get("venus", 0) or 0
            absents = row.get("absents", 0) or 0
            total = venus + absents
            if total == 0:
                return 0.0
            return round((venus / total) * 100, 2)
        except Exception as e:
            print(f"[RendezVousDAO] Erreur taux_presence: {e}")
            return 0.0
        finally:
            self.db.close()

    # =========================================================================
    # CHARGE DU PERSONNEL
    # =========================================================================

    def charge_par_personnel(self, code_session: str, date_debut=None, date_fin=None) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            conditions = ["r.code_session = %s"]
            params = [code_session]

            if date_debut:
                conditions.append("DATE(r.date_rendez_vous) >= DATE(%s)")
                params.append(date_debut)
            if date_fin:
                conditions.append("DATE(r.date_rendez_vous) <= DATE(%s)")
                params.append(date_fin)

            query = f"""
                SELECT
                    r.code_personnel,
                    per.nom,
                    per.prenom,
                    per.fonction,
                    COUNT(*) AS nombre_rendez_vous,
                    SUM(CASE WHEN {self._status_case_sql('r.statut_rendez_vous', 'attente')} THEN 1 ELSE 0 END) AS attente,
                    SUM(CASE WHEN {self._status_case_sql('r.statut_rendez_vous', 'confirme')} THEN 1 ELSE 0 END) AS confirme,
                    SUM(CASE WHEN {self._status_case_sql('r.statut_rendez_vous', 'termine')} THEN 1 ELSE 0 END) AS termine,
                    SUM(CASE WHEN {self._status_case_sql('r.statut_rendez_vous', 'annule')} THEN 1 ELSE 0 END) AS annule,
                    SUM(CASE WHEN {self._status_case_sql('r.statut_rendez_vous', 'absent')} THEN 1 ELSE 0 END) AS absent,
                    SUM(CASE WHEN {self._status_case_sql('r.statut_rendez_vous', 'reporte')} THEN 1 ELSE 0 END) AS reporte
                FROM rendez_vous r
                LEFT JOIN personnel per ON r.code_personnel = per.code
                WHERE {' AND '.join(conditions)}
                GROUP BY r.code_personnel, per.nom, per.prenom, per.fonction
                ORDER BY nombre_rendez_vous DESC, per.nom ASC
            """
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
        except Exception as e:
            print(f"[RendezVousDAO] Erreur charge_par_personnel: {e}")
            return []
        finally:
            self.db.close()

    def rdv_par_personnel(self, code_session: str) -> list:
        """Alias pour les graphes / compatibilite existante."""
        return self.charge_par_personnel(code_session)

    # =========================================================================
    # ANALYSES TEMPORELLES
    # =========================================================================

    def nombre_par_mois(self, code_session: str) -> dict:
        stats = {
            "Jan": 0, "Fev": 0, "Mar": 0, "Avr": 0, "Mai": 0, "Juin": 0,
            "Juil": 0, "Aout": 0, "Sep": 0, "Oct": 0, "Nov": 0, "Dec": 0
        }
        mois_mapping = {
            1: "Jan", 2: "Fev", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Juin",
            7: "Juil", 8: "Aout", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MONTH(date_rendez_vous) AS num_mois, COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                GROUP BY MONTH(date_rendez_vous)
                ORDER BY num_mois
            """, (code_session,))
            for row in cursor.fetchall():
                num_mois = row.get("num_mois")
                if num_mois in mois_mapping:
                    stats[mois_mapping[num_mois]] = row.get("total", 0)
            return stats
        except Exception as e:
            print(f"[RendezVousDAO] Erreur nombre_par_mois: {e}")
            return stats
        finally:
            self.db.close()

    def nombre_par_semaine(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    YEAR(date_rendez_vous) AS annee,
                    WEEK(date_rendez_vous, 1) AS numero_semaine,
                    COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                GROUP BY YEAR(date_rendez_vous), WEEK(date_rendez_vous, 1)
                ORDER BY annee, numero_semaine
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[RendezVousDAO] Erreur nombre_par_semaine: {e}")
            return []
        finally:
            self.db.close()

    def nombre_par_jour(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    DATE(date_rendez_vous) AS jour,
                    COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                GROUP BY DATE(date_rendez_vous)
                ORDER BY jour ASC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[RendezVousDAO] Erreur nombre_par_jour: {e}")
            return []
        finally:
            self.db.close()

    def nombre_par_heure(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    HOUR(date_rendez_vous) AS heure,
                    COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                GROUP BY HOUR(date_rendez_vous)
                ORDER BY heure ASC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[RendezVousDAO] Erreur nombre_par_heure: {e}")
            return []
        finally:
            self.db.close()

    def jours_plus_charges(self, code_session: str, limite: int = 7) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    DAYOFWEEK(date_rendez_vous) AS numero_jour,
                    COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                GROUP BY DAYOFWEEK(date_rendez_vous)
                ORDER BY total DESC
                LIMIT %s
            """, (code_session, limite))
            rows = cursor.fetchall()
            resultat = []
            jours_fr = {
                1: "Dimanche",
                2: "Lundi",
                3: "Mardi",
                4: "Mercredi",
                5: "Jeudi",
                6: "Vendredi",
                7: "Samedi"
            }
            for row in rows:
                resultat.append({
                    "numero_jour": row.get("numero_jour"),
                    "jour": jours_fr.get(row.get("numero_jour"), "Inconnu"),
                    "total": row.get("total", 0)
                })
            return resultat
        except Exception as e:
            print(f"[RendezVousDAO] Erreur jours_plus_charges: {e}")
            return []
        finally:
            self.db.close()

    def heures_plus_chargees(self, code_session: str, limite: int = 10) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    HOUR(date_rendez_vous) AS heure,
                    COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                GROUP BY HOUR(date_rendez_vous)
                ORDER BY total DESC, heure ASC
                LIMIT %s
            """, (code_session, limite))
            return cursor.fetchall()
        except Exception as e:
            print(f"[RendezVousDAO] Erreur heures_plus_chargees: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # ALERTES
    # =========================================================================

    def rendez_vous_proches(self, code_session: str, delai_minutes: int = 60) -> list:
        """Rendez-vous a venir tres prochainement."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            statut_clause, statut_params = self._build_status_clause(
                "r.statut_rendez_vous",
                ("attente", "confirme")
            )
            query = f"""
                {self._base_select_query()}
                WHERE r.code_session = %s
                  AND r.date_rendez_vous BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL %s MINUTE)
                  AND {statut_clause}
                ORDER BY r.date_rendez_vous ASC
            """
            cursor.execute(query, (code_session, delai_minutes, *statut_params))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[RendezVousDAO] Erreur rendez_vous_proches: {e}")
            return []
        finally:
            self.db.close()

    def rendez_vous_oublies(self, code_session: str, marge_minutes: int = 30) -> list:
        """
        Rendez-vous depasses dont le statut est encore actif.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            statut_clause, statut_params = self._build_status_clause(
                "r.statut_rendez_vous",
                ("attente", "confirme", "en_cours")
            )
            query = f"""
                {self._base_select_query()}
                WHERE r.code_session = %s
                  AND r.date_rendez_vous < DATE_SUB(NOW(), INTERVAL %s MINUTE)
                  AND {statut_clause}
                ORDER BY r.date_rendez_vous ASC
            """
            cursor.execute(query, (code_session, marge_minutes, *statut_params))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[RendezVousDAO] Erreur rendez_vous_oublies: {e}")
            return []
        finally:
            self.db.close()

    def alerte_surcharge_personnel(self, code_session: str, seuil_journalier: int = 12) -> list:
        """Retourne les agents dont la charge du jour depasse le seuil."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            statut_clause, statut_params = self._build_status_clause(
                "r.statut_rendez_vous",
                ("attente", "confirme", "en_cours", "termine")
            )
            query = f"""
                SELECT
                    r.code_personnel,
                    per.nom,
                    per.prenom,
                    per.fonction,
                    DATE(r.date_rendez_vous) AS jour,
                    COUNT(*) AS total
                FROM rendez_vous r
                LEFT JOIN personnel per ON r.code_personnel = per.code
                WHERE r.code_session = %s
                  AND DATE(r.date_rendez_vous) = CURDATE()
                  AND {statut_clause}
                GROUP BY r.code_personnel, per.nom, per.prenom, per.fonction, DATE(r.date_rendez_vous)
                HAVING COUNT(*) >= %s
                ORDER BY total DESC
            """
            cursor.execute(query, (code_session, *statut_params, seuil_journalier))
            return cursor.fetchall()
        except Exception as e:
            print(f"[RendezVousDAO] Erreur alerte_surcharge_personnel: {e}")
            return []
        finally:
            self.db.close()

    def alertes_rendez_vous(self, code_session: str, delai_minutes: int = 60, seuil_journalier: int = 12) -> dict:
        return {
            "proches": self.rendez_vous_proches(code_session, delai_minutes),
            "oublies": self.rendez_vous_oublies(code_session),
            "surcharge_personnel": self.alerte_surcharge_personnel(code_session, seuil_journalier)
        }

    # =========================================================================
    # STATISTIQUES / GRAPHES
    # =========================================================================

    def statistiques_generales(self, code_session: str) -> dict:
        return {
            "total": self.nombre_total_par_session(code_session),
            "attente": self.nombre_rdv_en_attente(code_session),
            "confirme": self.nombre_rdv_confirmes(code_session),
            "termine": self.nombre_rdv_termines(code_session),
            "annule": self.nombre_rdv_annules(code_session),
            "absent": self.nombre_rdv_absents(code_session),
            "reporte": self.nombre_rdv_reportes(code_session),
            "en_retard": self.nombre_rdv_en_retard(code_session),
            "aujourd_hui": self.nombre_rdv_aujourd_hui(code_session),
            "taux_presence": self.taux_presence(code_session)
        }

    def repartition_par_statut(self, code_session: str) -> list:
        """Format listable pour camembert / bar chart."""
        par_statut = self.rendez_vous_par_statut(code_session)
        return [
            {"statut": statut, "total": total}
            for statut, total in par_statut.items()
        ]

    def top_statuts(self, code_session: str, limite: int = 10) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    statut_rendez_vous AS statut,
                    COUNT(*) AS total
                FROM rendez_vous
                WHERE code_session = %s
                GROUP BY statut_rendez_vous
                ORDER BY total DESC
                LIMIT %s
            """, (code_session, limite))
            return cursor.fetchall()
        except Exception as e:
            print(f"[RendezVousDAO] Erreur top_statuts: {e}")
            return []
        finally:
            self.db.close()

    def revenu_total(self, code_session: str, date_debut=None, date_fin=None) -> float:
        """
        La table rendez_vous ne contient pas de montant.
        Methode fournie pour compatibilite avec le service/controleur existants.
        """
        return 0.0

    # =========================================================================
    # TABLEAUX / LISTES
    # =========================================================================

    def rendez_vous_du_jour(self, code_session: str) -> list:
        return self._lister_rendez_vous(
            code_session=code_session,
            date_exacte=datetime.now(),
            order_by="r.date_rendez_vous ASC"
        )

    def rendez_vous_en_retard(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            statut_clause, statut_params = self._build_status_clause(
                "r.statut_rendez_vous",
                ("attente", "confirme", "en_cours")
            )
            query = f"""
                {self._base_select_query()}
                WHERE r.code_session = %s
                  AND r.date_rendez_vous < NOW()
                  AND {statut_clause}
                ORDER BY r.date_rendez_vous ASC
            """
            cursor.execute(query, (code_session, *statut_params))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[RendezVousDAO] Erreur rendez_vous_en_retard: {e}")
            return []
        finally:
            self.db.close()

    def lister_rdv_en_attente(self, code_session: str) -> list:
        return self.lister_par_statut(code_session, "attente")

    # =========================================================================
    # PATIENTS / PERSONNEL
    # =========================================================================

    def patients_en_attente_rdv(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    v.code_visite,
                    v.date_visite,
                    v.statut_patient,
                    v.type_visite,
                    v.urgent,
                    p.code_patient,
                    p.nom,
                    p.prenom,
                    p.telephone
                FROM visite v
                INNER JOIN patients p ON v.code_patient = p.code_patient
                LEFT JOIN rendez_vous r ON v.code_visite = r.code_visite
                WHERE v.code_session = %s
                  AND v.statut_patient = 'Attente rendez-vous'
                  AND r.code_rendez_vous IS NULL
                ORDER BY v.urgent DESC, v.date_visite ASC
            """
            cursor.execute(query, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[RendezVousDAO] Erreur patients_en_attente_rdv: {e}")
            return []
        finally:
            self.db.close()

    def historique_patient(self, code_patient: str) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = f"""
                {self._base_select_query()}
                WHERE p.code_patient = %s
                ORDER BY r.date_rendez_vous DESC
            """
            cursor.execute(query, (code_patient,))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[RendezVousDAO] Erreur historique_patient: {e}")
            return []
        finally:
            self.db.close()

    def lister_personnel(self) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT code, nom, prenom, fonction
                FROM personnel
                ORDER BY nom ASC, prenom ASC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"[RendezVousDAO] Erreur lister_personnel: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # PREDICTIONS
    # =========================================================================

    def predire_affluence(self, code_session: str, horizon_jours: int = 7) -> list:
        """
        Prediction simple basee sur la moyenne historique par jour de semaine.
        """
        historique = self._moyenne_historique_par_jour_semaine(code_session)
        predictions = []
        date_depart = datetime.now().date()

        for offset in range(1, horizon_jours + 1):
            date_cible = date_depart + timedelta(days=offset)
            numero_jour = date_cible.weekday()
            stats = historique.get(numero_jour, {"moyenne_total": 0.0, "moyenne_absent": 0.0})
            total_prevu = round(stats["moyenne_total"])
            absents_prevus = round(stats["moyenne_absent"])
            taux_absence = round((absents_prevus / total_prevu) * 100, 2) if total_prevu else 0.0

            predictions.append({
                "date": date_cible,
                "jour": calendar.day_name[numero_jour],
                "rendez_vous_prevus": total_prevu,
                "absents_prevus": absents_prevus,
                "taux_absence_prevu": taux_absence
            })
        return predictions

    def predire_absence(self, code_session: str, horizon_jours: int = 7) -> list:
        """Alias cible absence, utile si la vue veut une methode dediee."""
        predictions = self.predire_affluence(code_session, horizon_jours)
        return [
            {
                "date": item["date"],
                "jour": item["jour"],
                "absents_prevus": item["absents_prevus"],
                "taux_absence_prevu": item["taux_absence_prevu"]
            }
            for item in predictions
        ]

    # =========================================================================
    # METHODES PRIVEES
    # =========================================================================

    def _generer_code(self, cursor) -> str:
        try:
            cursor.execute("""
                SELECT code_rendez_vous
                FROM rendez_vous
                ORDER BY code_rendez_vous DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if not row:
                return "RDV001"

            last_code = row.get("code_rendez_vous", "")
            last_num = int(last_code[3:]) if last_code.startswith("RDV") else 0
            return f"RDV{last_num + 1:03d}"
        except Exception:
            return "RDV" + datetime.now().strftime("%H%M%S")

    def _row_to_object(self, row) -> RendezVous:
        obj = RendezVous(
            code_rendez_vous=row.get("code_rendez_vous"),
            code_visite=row.get("code_visite"),
            code_personnel=row.get("code_personnel"),
            code_session=row.get("code_session"),
            date_rendez_vous=row.get("date_rendez_vous"),
            statut_rendez_vous=row.get("statut_rendez_vous")
        )

        # Champs enrichis pratiques pour les vues / tableaux.
        obj.patient_nom = row.get("patient_nom", "")
        obj.patient_prenom = row.get("patient_prenom", "")
        obj.code_patient = row.get("code_patient", "")
        obj.personnel_nom = row.get("personnel_nom", "")
        obj.personnel_prenom = row.get("personnel_prenom", "")
        obj.personnel_fonction = row.get("personnel_fonction", "")
        obj.statut_patient = row.get("statut_patient", "")
        obj.type_visite = row.get("type_visite", "")
        obj.urgent = row.get("urgent", "")
        return obj

    def _base_select_query(self) -> str:
        return """
            SELECT
                r.*,
                v.code_patient,
                v.type_visite,
                v.statut_patient,
                v.urgent,
                p.nom AS patient_nom,
                p.prenom AS patient_prenom,
                p.telephone AS patient_telephone,
                p.adresse AS patient_adresse,
                p.naissance AS patient_date_naissance,
                per.nom AS personnel_nom,
                per.prenom AS personnel_prenom,
                per.fonction AS personnel_fonction
            FROM rendez_vous r
            LEFT JOIN visite v ON r.code_visite = v.code_visite
            LEFT JOIN patients p ON v.code_patient = p.code_patient
            LEFT JOIN personnel per ON r.code_personnel = per.code
        """

    def _lister_rendez_vous(
        self,
        code_session: str = None,
        statut: str = None,
        patient: str = None,
        personnel: str = None,
        date_exacte=None,
        date_debut=None,
        date_fin=None,
        order_by: str = "r.date_rendez_vous DESC"
    ) -> list:
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            conditions = []
            params = []

            if code_session:
                conditions.append("r.code_session = %s")
                params.append(code_session)

            if statut:
                statut_clause, statut_params = self._build_status_clause("r.statut_rendez_vous", statut)
                conditions.append(statut_clause)
                params.extend(statut_params)

            if patient:
                like_patient = f"%{patient}%"
                conditions.append("""
                    (
                        p.code_patient LIKE %s
                        OR p.nom LIKE %s
                        OR p.prenom LIKE %s
                        OR CONCAT(COALESCE(p.nom, ''), ' ', COALESCE(p.prenom, '')) LIKE %s
                    )
                """)
                params.extend([like_patient, like_patient, like_patient, like_patient])

            if personnel:
                like_personnel = f"%{personnel}%"
                conditions.append("""
                    (
                        per.code LIKE %s
                        OR per.nom LIKE %s
                        OR per.prenom LIKE %s
                        OR CONCAT(COALESCE(per.nom, ''), ' ', COALESCE(per.prenom, '')) LIKE %s
                    )
                """)
                params.extend([like_personnel, like_personnel, like_personnel, like_personnel])

            if date_exacte:
                conditions.append("DATE(r.date_rendez_vous) = DATE(%s)")
                params.append(date_exacte)

            if date_debut:
                conditions.append("DATE(r.date_rendez_vous) >= DATE(%s)")
                params.append(date_debut)

            if date_fin:
                conditions.append("DATE(r.date_rendez_vous) <= DATE(%s)")
                params.append(date_fin)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"""
                {self._base_select_query()}
                {where_clause}
                ORDER BY {order_by}
            """
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[RendezVousDAO] Erreur _lister_rendez_vous: {e}")
            return []
        finally:
            self.db.close()

    def _normaliser_statut(self, statut: str) -> str:
        statut = (statut or "").strip().lower()
        mapping = {
            "attente": "attente",
            "en attente": "attente",
            "confirme": "confirme",
            "confirmé": "confirme",
            "confirmee": "confirme",
            "confirmée": "confirme",
            "en cours": "en_cours",
            "encours": "en_cours",
            "en_cours": "en_cours",
            "termine": "termine",
            "terminé": "termine",
            "terminee": "termine",
            "terminée": "termine",
            "annule": "annule",
            "annulé": "annule",
            "annulee": "annule",
            "annulée": "annule",
            "absent": "absent",
            "absente": "absent",
            "reporte": "reporte",
            "reporté": "reporte",
            "reportee": "reporte",
            "reportée": "reporte"
        }
        return mapping.get(statut, "autre")

    def _status_variants(self, statut) -> list:
        if isinstance(statut, (list, tuple, set)):
            variants = []
            for item in statut:
                variants.extend(self._status_variants(item))
            return variants

        canonical = self._normaliser_statut(statut)
        mapping = {
            "attente": ["attente", "en attente"],
            "confirme": ["confirme", "confirmé", "confirmée"],
            "en_cours": ["en cours", "en_cours", "encours"],
            "termine": ["termine", "terminé", "terminée"],
            "annule": ["annule", "annulé", "annulée"],
            "absent": ["absent", "absente"],
            "reporte": ["reporte", "reporté", "reportée"],
            "autre": ["autre"]
        }
        return mapping.get(canonical, [str(statut).strip().lower()])

    def _build_status_clause(self, field: str, statut) -> tuple:
        variants = self._status_variants(statut)
        placeholders = ", ".join(["%s"] * len(variants))
        return f"LOWER({field}) IN ({placeholders})", variants

    def _status_case_sql(self, field: str, *statuts: str) -> str:
        variants = self._status_variants(statuts)
        placeholders = ", ".join([f"'{variant}'" for variant in variants])
        return f"LOWER({field}) IN ({placeholders})"

    def _existe_doublon_visite(self, cursor, code_visite: str, code_rendez_vous_exclu: str = None) -> bool:
        query = """
            SELECT COUNT(*) AS total
            FROM rendez_vous
            WHERE code_visite = %s
        """
        params = [code_visite]
        if code_rendez_vous_exclu:
            query += " AND code_rendez_vous <> %s"
            params.append(code_rendez_vous_exclu)
        cursor.execute(query, tuple(params))
        row = cursor.fetchone() or {}
        return row.get("total", 0) > 0

    def _personnel_est_disponible(
        self,
        cursor,
        code_personnel: str,
        date_rendez_vous,
        code_rendez_vous_exclu: str = None
    ) -> bool:
        statut_clause, statut_params = self._build_status_clause(
            "statut_rendez_vous",
            ("attente", "confirme", "en_cours")
        )
        query = f"""
            SELECT COUNT(*) AS total
            FROM rendez_vous
            WHERE code_personnel = %s
              AND date_rendez_vous = %s
              AND {statut_clause}
        """
        params = [code_personnel, date_rendez_vous] + statut_params
        if code_rendez_vous_exclu:
            query += " AND code_rendez_vous <> %s"
            params.append(code_rendez_vous_exclu)
        cursor.execute(query, tuple(params))
        row = cursor.fetchone() or {}
        return row.get("total", 0) == 0

    def _count_simple(self, query: str, params: tuple) -> int:
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return (row or {}).get("total", 0)
        except Exception as e:
            print(f"[RendezVousDAO] Erreur _count_simple: {e}")
            return 0
        finally:
            self.db.close()

    def _moyenne_historique_par_jour_semaine(self, code_session: str) -> dict:
        conn = self.db.connect()
        if not conn:
            return {}
        try:
            cursor = conn.cursor()
            query = f"""
                SELECT
                    DAYOFWEEK(date_rendez_vous) AS numero_jour_mysql,
                    COUNT(*) / NULLIF(COUNT(DISTINCT DATE(date_rendez_vous)), 0) AS moyenne_total,
                    SUM(CASE WHEN {self._status_case_sql('statut_rendez_vous', 'absent')} THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(DISTINCT DATE(date_rendez_vous)), 0) AS moyenne_absent
                FROM rendez_vous
                WHERE code_session = %s
                  AND date_rendez_vous < NOW()
                GROUP BY DAYOFWEEK(date_rendez_vous)
            """
            cursor.execute(query, (code_session,))
            resultat = {}
            for row in cursor.fetchall():
                numero_mysql = row.get("numero_jour_mysql")
                # MySQL: 1=dimanche, 2=lundi ... 7=samedi
                numero_python = (numero_mysql + 5) % 7
                resultat[numero_python] = {
                    "moyenne_total": float(row.get("moyenne_total") or 0.0),
                    "moyenne_absent": float(row.get("moyenne_absent") or 0.0)
                }
            return resultat
        except Exception as e:
            print(f"[RendezVousDAO] Erreur _moyenne_historique_par_jour_semaine: {e}")
            return {}
        finally:
            self.db.close()
