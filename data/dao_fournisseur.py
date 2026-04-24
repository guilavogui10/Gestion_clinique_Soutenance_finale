import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
from core.connexion_db import DBConnection
from models.modele_fournisseur import Fournisseur

DictCursor = pymysql.cursors.DictCursor


class FournisseurDAO:
    """
    DAO pour la gestion des fournisseurs.
    Responsabilite: CRUD sur la table fournisseur.
    """

    def __init__(self):
        self.db = DBConnection()

    def lister_fournisseurs(self, code_session: str = None) -> list:
        """
        Retourne la liste de tous les fournisseurs actifs.
        Note: Les fournisseurs sont globaux (pas de code_session dans la table).
        Le parametre code_session est garde pour compatibilite mais non utilise.
        """
        print(f"[FournisseurDAO] Debut lister_fournisseurs")
        conn = self.db.connect()
        if not conn:
            print(f"[FournisseurDAO] Echec connexion")
            return []
        try:
            cursor = conn.cursor()
            print(f"[FournisseurDAO] Execution requete SQL")
            cursor.execute("""
                SELECT email_fournisseur, nom_entreprise, telephone, adresse
                FROM fournisseurs
                ORDER BY nom_entreprise ASC
            """)
            results = cursor.fetchall()
            print(f"[FournisseurDAO] Nombre de fournisseurs: {len(results)}")
            if results:
                print(f"[FournisseurDAO] Premier fournisseur: {results[0]}")
            return results
        except Exception as e:
            print(f"[FournisseurDAO] ERREUR: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            self.db.close()

    def obtenir_par_code(self, code_fournisseur: str):
        """Retourne un fournisseur par son code."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM fournisseurs
                WHERE email_fournisseur = %s
            """, (code_fournisseur,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[FournisseurDAO] Erreur obtenir_par_code: {e}")
            return None
        finally:
            self.db.close()

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------
    def add_fournisseur(self, fournisseur: Fournisseur):
        conn = self.db.connect()
        if not conn:
            return False, "Echec connexion BD."

        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO fournisseurs (email_fournisseur, nom_entreprise, telephone, adresse)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (
                fournisseur.get_mail_fournisseur(),
                fournisseur.get_nom(),
                fournisseur.get_telephone(),
                fournisseur.get_adresse()
            ))
            conn.commit()
            return True, "Fournisseur ajoute avec succes."
        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur ajout fournisseur : {e}"
        finally:
            self.db.close()

    # --------------------------------------------------------
    # READ - Recherche par critere (email OU telephone)
    # --------------------------------------------------------
    def search_fournisseur(self, critere):
        """
        Recherche generique :
        - email_fournisseur LIKE %critere%
        - telephone LIKE %critere%
        """
        conn = self.db.connect()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            sql = """
                SELECT email_fournisseur, nom_entreprise, telephone, adresse
                FROM fournisseurs
                WHERE email_fournisseur LIKE %s OR telephone LIKE %s
            """
            crit = f"%{critere}%"
            cursor.execute(sql, (crit, crit))
            return cursor.fetchall()
        except pymysql.MySQLError as e:
            print("Erreur recherche fournisseur :", e)
            return []
        finally:
            self.db.close()

    # --------------------------------------------------------
    # READ - Recherche par email (identifiant)
    # --------------------------------------------------------
    def get_fournisseur_by_mail(self, mail):
        conn = self.db.connect()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            sql = """
                SELECT email_fournisseur, nom_entreprise, telephone, adresse
                FROM fournisseurs WHERE email_fournisseur = %s
            """
            cursor.execute(sql, (mail,))
            return cursor.fetchone()
        except pymysql.MySQLError as e:
            print("Erreur get_fournisseur_by_mail :", e)
            return None
        finally:
            self.db.close()

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------
    def update_fournisseur(self, fournisseur_modifie: Fournisseur):
        conn = self.db.connect()
        if not conn:
            return False, "Erreur connexion BD."

        try:
            cursor = conn.cursor()
            sql = """
                UPDATE fournisseurs
                SET nom_entreprise = %s,
                    telephone = %s,
                    adresse = %s
                WHERE email_fournisseur = %s
            """
            cursor.execute(sql, (
                fournisseur_modifie.get_nom(),
                fournisseur_modifie.get_telephone(),
                fournisseur_modifie.get_adresse(),
                fournisseur_modifie.get_mail_fournisseur()
            ))
            conn.commit()
            return True, "Mise a jour reussie."
        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur modification fournisseur : {e}"
        finally:
            self.db.close()

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------
    def delete_fournisseur(self, mail):
        conn = self.db.connect()
        if not conn:
            return False, "Erreur connexion BD."

        try:
            cursor = conn.cursor()
            sql = "DELETE FROM fournisseurs WHERE email_fournisseur = %s"
            cursor.execute(sql, (mail,))
            conn.commit()
            return True, "Fournisseur supprime."
        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur suppression : {e}"
        finally:
            self.db.close()

    # --------------------------------------------------------
    # READ - Fournisseurs actifs (facture recente)
    # --------------------------------------------------------
    def get_fournisseurs_actifs(self, code_session: str = None):
        conn = self.db.connect()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            sql = """
                SELECT DISTINCT f.code_fournisseur
                FROM facture_fournisseur f
                WHERE f.date_facture_four >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
            """
            params = []
            if code_session:
                sql += " AND f.code_session = %s"
                params.append(code_session)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [r.get("code_fournisseur") for r in rows]
        except pymysql.MySQLError as e:
            print("Erreur get_fournisseurs_actifs :", e)
            return []
        finally:
            self.db.close()

    # --------------------------------------------------------
    # STATISTIQUES : total / actifs / inactifs
    # --------------------------------------------------------
    def get_fournisseur_stats(self, code_session: str = None):
        """
        Retourne un dict :
        {
            'total': X,
            'actifs': Y,
            'inactifs': Z
        }

        Actif = fournisseur ayant une facture dans les 3 derniers mois
        Table factures : facture_fournisseur.code_fournisseur
        """

        stats = {'total': 0, 'actifs': 0, 'inactifs': 0}
        conn = self.db.connect()
        if not conn:
            return stats

        try:
            cursor = conn.cursor()

            # 1) Total des fournisseurs
            cursor.execute("SELECT COUNT(*) AS total FROM fournisseurs")
            stats['total'] = cursor.fetchone()['total']

            # 2) Actifs dans les 3 derniers mois (filtre session si fourni)
            sql_actifs = """
                SELECT COUNT(DISTINCT f.code_fournisseur) AS actifs
                FROM facture_fournisseur f
                WHERE f.date_facture_four >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
            """
            params = []
            if code_session:
                sql_actifs += " AND f.code_session = %s"
                params.append(code_session)
            cursor.execute(sql_actifs, params)
            stats['actifs'] = cursor.fetchone()['actifs']

            # 3) Inactifs = total - actifs
            stats['inactifs'] = stats['total'] - stats['actifs']

            return stats

        except pymysql.MySQLError as e:
            print("Erreur get_fournisseur_stats :", e)
            return stats
        finally:
            self.db.close()

    def get_stats_fournisseur_detail(self, mail_fournisseur, code_session: str = None):
        data = {
            'nom': None,
            'nb_produits': 0,
            'quantite_totale': 0,
            'dernier_quantite': 0,
            'produits': [],
            'dernier_mouvement': None
        }

        conn = self.db.connect()
        if not conn:
            return data

        try:
            cursor = conn.cursor()
            # Nom du fournisseur
            cursor.execute(
                "SELECT nom_entreprise FROM fournisseurs WHERE email_fournisseur = %s",
                (mail_fournisseur,)
            )
            row = cursor.fetchone()
            if row:
                data['nom'] = row['nom_entreprise']

            # Liste des produits fournis avec quantite totale
            sql_produits = """
                SELECT p.code_produit, p.Designation, SUM(p.quantite_four) AS quantite
                FROM panier_facture_four p
                JOIN facture_fournisseur f ON f.code_facture_four = p.code_facture_four
                WHERE f.code_fournisseur = %s
                GROUP BY p.code_produit, p.Designation
            """
            params = [mail_fournisseur]
            if code_session:
                sql_produits = sql_produits.replace("WHERE f.code_fournisseur = %s",
                                                    "WHERE f.code_fournisseur = %s AND f.code_session = %s")
                params.append(code_session)
            cursor.execute(sql_produits, params)
            produits = cursor.fetchall()
            data['produits'] = [
                {
                    'nom': p.get('Designation') or p.get('code_produit', ''),
                    'code_produit': p.get('code_produit', ''),
                    'quantite': p.get('quantite', 0)
                }
                for p in produits
            ]
            data['nb_produits'] = len(produits)
            data['quantite_totale'] = sum(p['quantite'] for p in produits) if produits else 0

            # Dernier mouvement (derniere ligne de panier liee a la derniere facture)
            sql_last = """
                SELECT p.code_produit, p.Designation, p.quantite_four, f.date_facture_four
                FROM panier_facture_four p
                JOIN facture_fournisseur f ON f.code_facture_four = p.code_facture_four
                WHERE f.code_fournisseur = %s
                ORDER BY f.date_facture_four DESC
                LIMIT 1
            """
            params = [mail_fournisseur]
            if code_session:
                sql_last = sql_last.replace("WHERE f.code_fournisseur = %s",
                                            "WHERE f.code_fournisseur = %s AND f.code_session = %s")
                params.append(code_session)
            cursor.execute(sql_last, params)
            last = cursor.fetchone()
            if last:
                data['dernier_quantite'] = last.get('quantite_four', 0)
                data['dernier_mouvement'] = last

            return data

        except pymysql.MySQLError as e:
            print("Erreur get_stats_fournisseur_detail :", e)
            return data
        finally:
            self.db.close()

    def get_fournisseurs_recents(self, code_session: str = None):
        """
        Affiche :
        - les fournisseurs ayant une facture dans les 30 derniers jours
        - sinon les 5 fournisseurs les plus recents par facture
        """

        data = []
        conn = self.db.connect()
        if conn is None:
            return data

        try:
            cursor = conn.cursor()

            # 1) Verifier s'il existe des fournisseurs recents
            sql_check = """
                SELECT COUNT(DISTINCT f.code_fournisseur) AS total
                FROM facture_fournisseur f
                WHERE f.date_facture_four >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
            """
            params = []
            if code_session:
                sql_check += " AND f.code_session = %s"
                params.append(code_session)
            cursor.execute(sql_check, params)
            row = cursor.fetchone()
            total_recent = row["total"] if row else 0

            # 2) Cas : fournisseurs recents trouves
            if total_recent > 0:
                sql_recent = """
                    SELECT DISTINCT
                        fr.email_fournisseur,
                        fr.nom_entreprise,
                        fr.telephone,
                        fr.adresse,
                        f.date_facture_four AS derniere_fourniture
                    FROM fournisseurs fr
                    JOIN facture_fournisseur f
                        ON f.code_fournisseur = fr.email_fournisseur
                    WHERE f.date_facture_four >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
                    ORDER BY f.date_facture_four DESC
                """
                params = []
                if code_session:
                    sql_recent = sql_recent.replace("WHERE f.date_facture_four >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)",
                                                    "WHERE f.date_facture_four >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) AND f.code_session = %s")
                    params.append(code_session)
                cursor.execute(sql_recent, params)
                data = cursor.fetchall()

            # 3) Cas : aucun fournisseur recent -> top 5
            else:
                sql_top5 = """
                    SELECT
                        fr.email_fournisseur,
                        fr.nom_entreprise,
                        fr.telephone,
                        fr.adresse,
                        MAX(f.date_facture_four) AS derniere_fourniture
                    FROM fournisseurs fr
                    JOIN facture_fournisseur f
                        ON f.code_fournisseur = fr.email_fournisseur
                    GROUP BY fr.email_fournisseur, fr.nom_entreprise, fr.telephone, fr.adresse
                    ORDER BY derniere_fourniture DESC
                    LIMIT 5
                """
                params = []
                if code_session:
                    sql_top5 = sql_top5.replace("GROUP BY fr.email_fournisseur, fr.nom_entreprise, fr.telephone, fr.adresse",
                                                "WHERE f.code_session = %s GROUP BY fr.email_fournisseur, fr.nom_entreprise, fr.telephone, fr.adresse")
                    params.append(code_session)
                cursor.execute(sql_top5, params)
                data = cursor.fetchall()

        except pymysql.MySQLError as e:
            print("Erreur get_fournisseurs_recents :", e)

        finally:
            self.db.close()
        return data
