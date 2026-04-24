"""
panier_facture_dao.py
---------------------
DAO pour la gestion de la table panier_facture.
Architecture MVC : accès aux données uniquement.

Rôle : lignes de détail du corps de la facture patient.
       Chaque ligne correspond à UN service rendu (consultation,
       examen, chirurgie, lunettes, pharmacie agrégée).

Colonnes table panier_facture :
    code_paniere      PK  VARCHAR   généré PAN001+
    designation       VARCHAR       libellé du service
    numero_reference  VARCHAR       code source (CLS001, EXM001, ...)
    quantite_facture  INT
    prix_applique     DECIMAL
    code_facture      FK → facture_patient
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from datetime import datetime
from core.connexion_db import DBConnection
from models.modele_panier_facture import PanierFacture

DictCursor = pymysql.cursors.DictCursor


class PanierFactureDAO:
    """
    Classe DAO pour la gestion des lignes panier_facture.
    Architecture MVC : accès aux données uniquement.
    """

    def __init__(self):
        self.db = DBConnection()

    # =========================================================================
    # MÉTHODES CRUD
    # =========================================================================

    def ajouter(self, ligne: PanierFacture) -> bool:
        """
        Insère une ligne de détail dans panier_facture.

        Args:
            ligne (PanierFacture): Objet ligne à insérer.

        Returns:
            bool: True si succès, False sinon.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)
            ligne.set_code_paniere(self._generer_code(cursor))
            query = """
                INSERT INTO panier_facture (
                    code_paniere, designation, numero_reference,
                    quantite_facture, `prix_appliqué`, code_facture
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                ligne.get_code_paniere(),
                ligne.get_designation(),
                ligne.get_numero_reference(),
                ligne.get_quantite_facture(),
                ligne.get_prix_applique(),
                ligne.get_code_facture(),
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur ajouter: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def ajouter_plusieurs(self, lignes: list, conn=None) -> bool:
        """
        Insère plusieurs lignes panier en une seule transaction.
        Accepte une connexion externe pour s'intégrer dans une
        transaction atomique avec FacturePatientDAO.

        Args:
            lignes (list[PanierFacture]): Lignes à insérer.
            conn: Connexion externe optionnelle.

        Returns:
            bool: True si toutes les lignes ont été insérées.
        """
        gestion_connexion = conn is None
        if gestion_connexion:
            conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)
            for ligne in lignes:
                ligne.set_code_paniere(self._generer_code(cursor))
                cursor.execute("""
                    INSERT INTO panier_facture (
                        code_paniere, designation, numero_reference,
                        quantite_facture, `prix_appliqué`, code_facture
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    ligne.get_code_paniere(),
                    ligne.get_designation(),
                    ligne.get_numero_reference(),
                    ligne.get_quantite_facture(),
                    ligne.get_prix_applique(),
                    ligne.get_code_facture(),
                ))
            if gestion_connexion:
                conn.commit()
            return True
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur ajouter_plusieurs: {e}")
            if gestion_connexion:
                conn.rollback()
            return False
        finally:
            if gestion_connexion:
                self.db.close()

    def modifier(self, ligne: PanierFacture) -> bool:
        """
        Met à jour une ligne panier_facture existante.

        Args:
            ligne (PanierFacture): Objet ligne avec les nouvelles données.

        Returns:
            bool: True si succès, False sinon.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                UPDATE panier_facture SET
                    designation      = %s,
                    numero_reference = %s,
                    quantite_facture = %s,
                    `prix_appliqué`  = %s,
                    code_facture     = %s
                WHERE code_paniere = %s
            """
            cursor.execute(query, (
                ligne.get_designation(),
                ligne.get_numero_reference(),
                ligne.get_quantite_facture(),
                ligne.get_prix_applique(),
                ligne.get_code_facture(),
                ligne.get_code_paniere(),
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur modifier: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def supprimer(self, code_paniere: str) -> bool:
        """
        Supprime une ligne panier par son code.

        Args:
            code_paniere (str): Code de la ligne à supprimer.

        Returns:
            bool: True si succès, False sinon.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "DELETE FROM panier_facture WHERE code_paniere = %s",
                (code_paniere,)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur supprimer: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def supprimer_par_facture(self, code_facture: str) -> bool:
        """
        Supprime TOUTES les lignes panier d'une facture.
        Utilisé lors de l'annulation ou de la régénération d'une facture.

        Args:
            code_facture (str): Code de la facture concernée.

        Returns:
            bool: True si succès, False sinon.
        """
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "DELETE FROM panier_facture WHERE code_facture = %s",
                (code_facture,)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur supprimer_par_facture: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # =========================================================================
    # MÉTHODES DE RÉCUPÉRATION
    # =========================================================================

    def obtenir_par_code(self, code_paniere: str):
        """
        Retourne un objet PanierFacture par son code.

        Args:
            code_paniere (str): Code de la ligne.

        Returns:
            PanierFacture | None
        """
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute(
                "SELECT * FROM panier_facture WHERE code_paniere = %s",
                (code_paniere,)
            )
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur obtenir_par_code: {e}")
            return None
        finally:
            conn.close()

    def lister_par_facture(self, code_facture: str) -> list:
        """
        Retourne toutes les lignes panier d'une facture,
        triées par code_paniere croissant.
        Utilisé pour afficher le détail de la facture dans la vue.

        Args:
            code_facture (str): Code de la facture.

        Returns:
            list[PanierFacture]
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT *
                FROM panier_facture
                WHERE code_facture = %s
                ORDER BY code_paniere ASC
            """, (code_facture,))
            return [self._row_to_object(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur lister_par_facture: {e}")
            return []
        finally:
            conn.close()

    # =========================================================================
    # MÉTHODES STATISTIQUES
    # =========================================================================

    def calculer_total_facture(self, code_facture: str) -> float:
        """
        Calcule le montant total d'une facture en sommant ses lignes panier.
        Calcul SQL (SUM) — aucun calcul Python.

        Args:
            code_facture (str): Code de la facture.

        Returns:
            float: Montant total calculé.
        """
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT COALESCE(SUM(quantite_facture * `prix_appliqué`), 0) AS total
                FROM panier_facture
                WHERE code_facture = %s
            """, (code_facture,))
            row = cursor.fetchone()
            return float(row["total"]) if row else 0.0
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur calculer_total_facture: {e}")
            return 0.0
        finally:
            conn.close()

    def repartition_par_service(self, code_session: str) -> list:
        """
        Agrège les montants par type de service (designation)
        pour toutes les factures payées d'une session.
        Utilisé pour le graphique revenus par service du dashboard.

        Args:
            code_session (str): Code de la session.

        Returns:
            list[dict]: [{'designation', 'nombre', 'total'}, ...]
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    pf.designation,
                    COALESCE(SUM(pf.quantite_facture), 0)          AS nombre,
                    COUNT(*)                                       AS nombre_lignes,
                    COALESCE(SUM(pf.quantite_facture * pf.`prix_appliqué`), 0) AS total
                FROM panier_facture pf
                INNER JOIN facture_patient f ON pf.code_facture = f.code_facture
                WHERE f.code_session   = %s
                  AND f.statut_facture = 'Payé'
                GROUP BY pf.designation
                ORDER BY total DESC
            """, (code_session,))
            rows = cursor.fetchall()
            total_general = sum(float(row.get("total", 0) or 0) for row in rows)

            for row in rows:
                row["nombre"] = int(row.get("nombre", 0) or 0)
                row["nombre_lignes"] = int(row.get("nombre_lignes", 0) or 0)
                row["total"] = float(row.get("total", 0) or 0)
                row["pourcentage"] = round(
                    (row["total"] / total_general) * 100, 1
                ) if total_general > 0 else 0.0

            return rows
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur repartition_par_service: {e}")
            return []
        finally:
            conn.close()

    def resume_economie_session(self, code_session: str) -> dict:
        """
        Retourne les KPI globaux de la vue economie du cabinet
        a partir des lignes panier effectivement payees.

        Retourne :
            chiffre_affaires_total
            nombre_services_factures
            nombre_factures_payees
            panier_moyen_facture
            service_plus_rentable
            montant_service_plus_rentable
        """
        conn = self.db.connect()
        if not conn:
            return self._resume_economie_vide()
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    COALESCE(SUM(pf.quantite_facture * pf.`prix_appliqué`), 0) AS chiffre_affaires_total,
                    COALESCE(SUM(pf.quantite_facture), 0)                        AS nombre_services_factures,
                    COUNT(DISTINCT pf.code_facture)                              AS nombre_factures_payees
                FROM panier_facture pf
                INNER JOIN facture_patient f ON pf.code_facture = f.code_facture
                WHERE f.code_session   = %s
                  AND f.statut_facture = 'Payé'
            """, (code_session,))
            row = cursor.fetchone() or {}

            chiffre_affaires_total = float(row.get("chiffre_affaires_total", 0) or 0)
            nombre_services = int(row.get("nombre_services_factures", 0) or 0)
            nombre_factures = int(row.get("nombre_factures_payees", 0) or 0)
            panier_moyen = round(
                chiffre_affaires_total / nombre_factures, 2
            ) if nombre_factures > 0 else 0.0

            cursor.execute("""
                SELECT
                    pf.designation,
                    COALESCE(SUM(pf.quantite_facture * pf.`prix_appliqué`), 0) AS total
                FROM panier_facture pf
                INNER JOIN facture_patient f ON pf.code_facture = f.code_facture
                WHERE f.code_session   = %s
                  AND f.statut_facture = 'Payé'
                GROUP BY pf.designation
                ORDER BY total DESC
                LIMIT 1
            """, (code_session,))
            top_service = cursor.fetchone() or {}

            return {
                "chiffre_affaires_total": chiffre_affaires_total,
                "nombre_services_factures": nombre_services,
                "nombre_factures_payees": nombre_factures,
                "panier_moyen_facture": panier_moyen,
                "service_plus_rentable": top_service.get("designation") or "",
                "montant_service_plus_rentable": float(top_service.get("total", 0) or 0),
            }
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur resume_economie_session: {e}")
            return self._resume_economie_vide()
        finally:
            conn.close()

    def top_services_par_revenus(self, code_session: str, limite: int = 5) -> list:
        """
        Retourne les services les plus rentables de la session.
        Utilise pour le graphe Top services par revenus.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    pf.designation,
                    COALESCE(SUM(pf.quantite_facture), 0) AS nombre,
                    COALESCE(SUM(pf.quantite_facture * pf.`prix_appliqué`), 0) AS total
                FROM panier_facture pf
                INNER JOIN facture_patient f ON pf.code_facture = f.code_facture
                WHERE f.code_session   = %s
                  AND f.statut_facture = 'Payé'
                GROUP BY pf.designation
                ORDER BY total DESC, nombre DESC, pf.designation ASC
                LIMIT %s
            """, (code_session, max(1, int(limite))))
            rows = cursor.fetchall()
            for row in rows:
                row["nombre"] = int(row.get("nombre", 0) or 0)
                row["total"] = float(row.get("total", 0) or 0)
            return rows
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur top_services_par_revenus: {e}")
            return []
        finally:
            conn.close()

    def volume_vs_revenus_par_service(self, code_session: str) -> list:
        """
        Retourne pour chaque service le volume facture
        et le revenu correspondant.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    pf.designation,
                    COALESCE(SUM(pf.quantite_facture), 0) AS nombre,
                    COALESCE(SUM(pf.quantite_facture * pf.`prix_appliqué`), 0) AS total
                FROM panier_facture pf
                INNER JOIN facture_patient f ON pf.code_facture = f.code_facture
                WHERE f.code_session   = %s
                  AND f.statut_facture = 'Payé'
                GROUP BY pf.designation
                ORDER BY total DESC, nombre DESC, pf.designation ASC
            """, (code_session,))
            rows = cursor.fetchall()
            for row in rows:
                row["nombre"] = int(row.get("nombre", 0) or 0)
                row["total"] = float(row.get("total", 0) or 0)
            return rows
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur volume_vs_revenus_par_service: {e}")
            return []
        finally:
            conn.close()

    def top_services_par_volume(self, code_session: str, limite: int = 10) -> list:
        """
        Retourne les services les plus frequents par volume facture.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    pf.designation,
                    COALESCE(SUM(pf.quantite_facture), 0) AS nombre,
                    COALESCE(SUM(pf.quantite_facture * pf.`prix_appliqué`), 0) AS total
                FROM panier_facture pf
                INNER JOIN facture_patient f ON pf.code_facture = f.code_facture
                WHERE f.code_session   = %s
                  AND f.statut_facture = 'Payé'
                GROUP BY pf.designation
                ORDER BY nombre DESC, total DESC, pf.designation ASC
                LIMIT %s
            """, (code_session, max(1, int(limite))))
            rows = cursor.fetchall()
            total_volume = sum(int(row.get("nombre", 0) or 0) for row in rows)

            for row in rows:
                row["nombre"] = int(row.get("nombre", 0) or 0)
                row["total"] = float(row.get("total", 0) or 0)
                row["pourcentage"] = round(
                    (row["nombre"] / total_volume) * 100, 1
                ) if total_volume > 0 else 0.0

            return rows
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur top_services_par_volume: {e}")
            return []
        finally:
            conn.close()

    def evolution_chiffre_affaires_par_mois(self, code_session: str) -> dict:
        """
        Retourne le chiffre d'affaires mensuel de la session
        a partir des lignes panier payees.

        Format : {'Jan': 0.0, 'Fév': 0.0, ..., 'Déc': 0.0}
        """
        stats = self._stats_mensuelles_vides()
        mois_map = self._mois_map()

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    MONTH(f.date_facture) AS num_mois,
                    COALESCE(SUM(pf.quantite_facture * pf.`prix_appliqué`), 0) AS total
                FROM panier_facture pf
                INNER JOIN facture_patient f ON pf.code_facture = f.code_facture
                WHERE f.code_session   = %s
                  AND f.statut_facture = 'Payé'
                GROUP BY MONTH(f.date_facture)
                ORDER BY MONTH(f.date_facture)
            """, (code_session,))
            for row in cursor.fetchall():
                num_mois = row.get("num_mois")
                if num_mois in mois_map:
                    stats[mois_map[num_mois]] = float(row.get("total", 0) or 0)
            return stats
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur evolution_chiffre_affaires_par_mois: {e}")
            return stats
        finally:
            conn.close()

    def apercu_facture_detail(self, code_facture: str) -> dict:
        """
        Retourne un aperçu detaille d'une facture
        directement base sur les lignes panier.
        """
        conn = self.db.connect()
        if not conn:
            return {"code_facture": code_facture, "lignes": [], "total_facture": 0.0}
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    code_paniere,
                    designation,
                    numero_reference,
                    quantite_facture,
                    `prix_appliqué` AS prix_applique
                FROM panier_facture
                WHERE code_facture = %s
                ORDER BY code_paniere ASC
            """, (code_facture,))

            lignes = []
            total_facture = 0.0

            for row in cursor.fetchall():
                quantite = int(row.get("quantite_facture", 0) or 0)
                prix = float(row.get("prix_applique", 0) or 0)
                total_ligne = round(quantite * prix, 2)
                total_facture += total_ligne
                lignes.append({
                    "code_paniere": row.get("code_paniere", ""),
                    "designation": row.get("designation", ""),
                    "numero_reference": row.get("numero_reference", ""),
                    "quantite_facture": quantite,
                    "prix_applique": prix,
                    "total_ligne": total_ligne,
                })

            return {
                "code_facture": code_facture,
                "lignes": lignes,
                "total_facture": round(total_facture, 2),
            }
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur apercu_facture_detail: {e}")
            return {"code_facture": code_facture, "lignes": [], "total_facture": 0.0}
        finally:
            conn.close()

    def derniere_facture_payee_apercu(self, code_session: str) -> dict:
        """
        Retourne le detail de la facture payee la plus recente
        pour alimenter un tableau d'aperçu.
        """
        conn = self.db.connect()
        if not conn:
            return {"code_facture": "", "lignes": [], "total_facture": 0.0}
        try:
            cursor = conn.cursor(DictCursor)
            cursor.execute("""
                SELECT
                    pf.code_facture,
                    MAX(f.date_facture) AS date_facture,
                    COUNT(pf.code_paniere) AS nb_lignes
                FROM panier_facture pf
                INNER JOIN facture_patient f ON pf.code_facture = f.code_facture
                WHERE f.code_session   = %s
                  AND f.statut_facture = 'Payé'
                GROUP BY pf.code_facture
                HAVING COUNT(pf.code_paniere) > 0
                ORDER BY date_facture DESC, pf.code_facture DESC
                LIMIT 1
            """, (code_session,))
            row = cursor.fetchone()
            if not row:
                return {"code_facture": "", "lignes": [], "total_facture": 0.0}

            code_facture = row["code_facture"]
            cursor.execute("""
                SELECT
                    code_paniere,
                    designation,
                    numero_reference,
                    quantite_facture,
                    `prix_appliqué` AS prix_applique
                FROM panier_facture
                WHERE code_facture = %s
                ORDER BY code_paniere ASC
            """, (code_facture,))

            lignes = []
            total_facture = 0.0
            for ligne in cursor.fetchall():
                quantite = int(ligne.get("quantite_facture", 0) or 0)
                prix = float(ligne.get("prix_applique", 0) or 0)
                total_ligne = round(quantite * prix, 2)
                total_facture += total_ligne
                lignes.append({
                    "code_paniere": ligne.get("code_paniere", ""),
                    "designation": ligne.get("designation", ""),
                    "numero_reference": ligne.get("numero_reference", ""),
                    "quantite_facture": quantite,
                    "prix_applique": prix,
                    "total_ligne": total_ligne,
                })

            return {
                "code_facture": code_facture,
                "lignes": lignes,
                "total_facture": round(total_facture, 2),
            }
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur derniere_facture_payee_apercu: {e}")
            return {"code_facture": "", "lignes": [], "total_facture": 0.0}
        finally:
            conn.close()

    # =========================================================================
    # MÉTHODES PRIVÉES
    # =========================================================================

    def _generer_code(self, cursor) -> str:
        """Génère le prochain code PAN : PAN001, PAN002, ..."""
        try:
            cursor.execute(
                "SELECT code_paniere FROM panier_facture ORDER BY code_paniere DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                last_code = row["code_paniere"] if isinstance(row, dict) else row[0]
                last_num  = int(last_code[3:])
                return f"PAN{last_num + 1:03d}"
            return "PAN001"
        except Exception as e:
            print(f"[PanierFactureDAO] Erreur _generer_code: {e}")
            return "PAN" + datetime.now().strftime("%H%M%S")

    def _row_to_object(self, row) -> PanierFacture:
        """Convertit une ligne DictCursor en objet PanierFacture."""
        return PanierFacture(
            code_paniere      = row["code_paniere"],
            designation       = row["designation"],
            numero_reference  = row["numero_reference"],
            quantite_facture  = int(row["quantite_facture"]),
            prix_applique     = float(
                row["prix_applique"] if "prix_applique" in row else row.get("prix_appliqué", 0)
            ),
            code_facture      = row["code_facture"],
        )

    @staticmethod
    def _resume_economie_vide() -> dict:
        """Retourne un résumé vide pour la vue economie."""
        return {
            "chiffre_affaires_total": 0.0,
            "nombre_services_factures": 0,
            "nombre_factures_payees": 0,
            "panier_moyen_facture": 0.0,
            "service_plus_rentable": "",
            "montant_service_plus_rentable": 0.0,
        }

    @staticmethod
    def _stats_mensuelles_vides() -> dict:
        """Retourne la structure mensuelle vide pour les graphes."""
        return {
            "Jan": 0.0, "Fév": 0.0, "Mar": 0.0, "Avr": 0.0,
            "Mai": 0.0, "Juin": 0.0, "Juil": 0.0, "Août": 0.0,
            "Sep": 0.0, "Oct": 0.0, "Nov": 0.0, "Déc": 0.0,
        }

    @staticmethod
    def _mois_map() -> dict:
        """Associe numero de mois et libellé court français."""
        return {
            1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr",
            5: "Mai", 6: "Juin", 7: "Juil", 8: "Août",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Déc",
        }
