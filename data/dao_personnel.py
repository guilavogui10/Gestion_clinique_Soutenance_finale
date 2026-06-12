import pymysql
from connexion.db_connection import DBConnection
from models.modele_personnel import ModelePersonnel

class PersonnelDAO:
    def __init__(self):
        self.db_connection = DBConnection()

    def _row_to_modele(self, row):
        if not row:
            return None
        return ModelePersonnel(
            row.get("code"),
            row.get("nom"),
            row.get("prenom"),
            row.get("adresse"),
            row.get("date_naissance"),
            row.get("contact"),
            row.get("mail"),
            row.get("fonction"),
            row.get("photo_path"),
            row.get("est_responsable", 0),
        )

    def _rows_to_modeles(self, rows):
        return [self._row_to_modele(row) for row in rows]

    def generer_nouveau_code(self) -> str:
        """Génère un code unique pour le personnel comme P0001, P0002..."""
        conn = self.db_connection.connect()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Récupère le max numérique du code existant
                cursor.execute("SELECT MAX(CAST(SUBSTRING(code, 2) AS UNSIGNED)) AS max_id FROM personnel WHERE code LIKE 'P%'")
                result = cursor.fetchone()
                max_id = result['max_id'] if result and result['max_id'] is not None else 0
                new_id = max_id + 1
                return f"P{new_id:04d}"
        except pymysql.MySQLError as e:
            print(f"Erreur DAO Personnel: Impossible de générer le code : {e}")
            return "P0001"
        finally:
            if conn:
                conn.close()


    def enregistrer_personnel(self, personnel: ModelePersonnel):
        """Enregistre un nouveau personnel dans la base de données."""
        conn = self.db_connection.connect()
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO personnel (code, nom, prenom, adresse, date_naissance, contact, mail, fonction, photo_path, est_responsable)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    personnel.get_code(),
                    personnel.get_nom(),
                    personnel.get_prenom(),
                    personnel.get_adresse(),
                    personnel.get_date_naissance(),
                    personnel.get_contact(),
                    personnel.get_mail(),
                    personnel.get_fonction(),
                    personnel.get_photo_path(),
                    personnel.get_est_responsable(),
                ))
                conn.commit()
                return True
        except pymysql.MySQLError as e:
            print(f"Erreur PyMySQL: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()


    def modifier_personnel(self, personnel:ModelePersonnel):
        """
        Met à jour un personnel via son code.
        """
        conn = self.db_connection.connect()
        try:
            with conn.cursor() as cursor:
                sql = """
                UPDATE personnel
                SET nom=%s, prenom=%s, adresse=%s, date_naissance=%s,
                    contact=%s, mail=%s, fonction=%s, photo_path=%s, est_responsable=%s
                WHERE code=%s
                """
                cursor.execute(sql, (
                    personnel.get_nom(),
                    personnel.get_prenom(),
                    personnel.get_adresse(),
                    personnel.get_date_naissance(),
                    personnel.get_contact(),
                    personnel.get_mail(),
                    personnel.get_fonction(),
                    personnel.get_photo_path(),
                    personnel.get_est_responsable(),
                    personnel.get_code()
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print("Erreur lors de la modification du personnel :", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
        
    def supprimer_par_mail(self, mail):
        """
        Supprime un personnel via son email.
        """
        conn = self.db_connection.connect()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM personnel WHERE mail=%s"
                cursor.execute(sql, (mail,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print("Erreur suppression personnel :", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()



    def rechercher(self, critere):
        """
        Recherche par contact OU par mail.
        """
        conn = self.db_connection.connect()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT * FROM personnel
                WHERE contact LIKE %s OR mail LIKE %s
                """
                filtre = "%" + (critere or "") + "%"
                cursor.execute(sql, (filtre, filtre))
                return self._rows_to_modeles(cursor.fetchall())
        except Exception as e:
            print("Erreur recherche personnel :", e)
            return []
        finally:
            if conn:
                conn.close()



    def lister_tout(self):
        """
        Retourne toute la liste du personnel.
        """
        conn = self.db_connection.connect()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT * FROM personnel ORDER BY nom ASC"
                cursor.execute(sql)
                return self._rows_to_modeles(cursor.fetchall())
        except Exception as e:
            print("Erreur listing personnel :", e)
            return []
        finally:
            if conn:
                conn.close()



    def nombre_total(self):
        """
        Retourne le nombre total de personnels.
        """
        conn = self.db_connection.connect()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT COUNT(*) as total FROM personnel"
                cursor.execute(sql)
                result = cursor.fetchone()
                if not result:
                    return 0
                if isinstance(result, dict):
                    return result.get('total', 0)
                return result[0]
        except Exception as e:
            print("Erreur nombre total :", e)
            return 0
        finally:
            if conn:
                conn.close()



    def obtenir_par_code(self, code):
        """
        Retourne un personnel selon son code.
        Utile pour pré-remplir le formulaire de modification.
        """
        conn = self.db_connection.connect()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT * FROM personnel WHERE code=%s"
                cursor.execute(sql, (code,))
                return self._row_to_modele(cursor.fetchone())
        except Exception as e:
            print("Erreur obtenir par code :", e)
            return None
        finally:
            if conn:
                conn.close()

    def get_responsable(self, fonction: str) -> dict | None:
        """
        Retourne toutes les informations du responsable d'un service (fonction).
        Utilisé par Vault pour envoyer le code OTP de déverrouillage par email.
        """
        conn = self.db_connection.connect()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT *
                FROM personnel
                WHERE LOWER(fonction) = LOWER(%s) AND est_responsable = 1
                LIMIT 1
                """
                cursor.execute(sql, (fonction,))
                return cursor.fetchone()
        except Exception as e:
            print("Erreur get_responsable :", e)
            return None
        finally:
            if conn:
                conn.close()

    def compter_par_fonction(self) -> dict:
        """
        Compte le nombre de personnels par fonction.
        Retourne un dictionnaire {fonction: nombre}
        """
        conn = self.db_connection.connect()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT fonction, COUNT(*) as nombre
                FROM personnel
                GROUP BY fonction
                ORDER BY fonction
                """
                cursor.execute(sql)
                results = cursor.fetchall()
                return {row['fonction']: row['nombre'] for row in results}
        except Exception as e:
            print("Erreur compter_par_fonction :", e)
            return {}
        finally:
            if conn:
                conn.close()

    def lister_pour_formulaire(self, roles: list = None) -> list:
        """Retourne le personnel formaté pour les dropdowns (code + label)."""
        conn = self.db_connection.connect()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                if roles:
                    placeholders = ','.join(['%s'] * len(roles))
                    cursor.execute(f"""
                        SELECT code, CONCAT(nom, ' ', prenom) AS label
                        FROM personnel
                        WHERE fonction IN ({placeholders})
                        ORDER BY nom ASC LIMIT 200
                    """, roles)
                else:
                    cursor.execute("""
                        SELECT code, CONCAT(nom, ' ', prenom) AS label
                        FROM personnel
                        ORDER BY nom ASC LIMIT 200
                    """)
                return cursor.fetchall() or []
        except Exception as e:
            print("Erreur lister_pour_formulaire :", e)
            return []
        finally:
            if conn:
                conn.close()
