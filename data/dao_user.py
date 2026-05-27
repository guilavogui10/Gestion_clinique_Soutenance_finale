import bcrypt
import pymysql

from core.connexion_db import DBConnection
from models.modele_user import ModeleUser


class UserDAO:
    def __init__(self):
        self.db_connection = DBConnection()

    def _hasher_mdp(self, mdp: str) -> str:
        """Hache le mot de passe avant de l'enregistrer."""
        mot_de_passe_bytes = mdp.encode("utf-8")
        sel = bcrypt.gensalt()
        mdp_hashe_bytes = bcrypt.hashpw(mot_de_passe_bytes, sel)
        return mdp_hashe_bytes.decode("utf-8")

    def generer_nouveau_code(self) -> str | None:
        """Genere un nouveau code unique comme 'U0001'."""
        conn = self.db_connection.connect()
        if not conn:
            return None

        try:
            with conn.cursor() as cursor:
                sql = "SELECT code FROM utilisateur ORDER BY code DESC LIMIT 1"
                cursor.execute(sql)
                resultat = cursor.fetchone()

                dernier_numero = 0
                if resultat:
                    dernier_code = resultat["code"] if isinstance(resultat, dict) else resultat[0]
                    dernier_numero = int(dernier_code[1:])

                nouveau_numero = dernier_numero + 1
                return f"U{nouveau_numero:04d}"
        except Exception as e:
            print(f"Erreur lors de la generation du code : {e}")
            return None
        finally:
            conn.close()

    def enregistrer_utilisateur(self, user: ModeleUser) -> bool:
        """Enregistre un nouvel utilisateur dans la base de donnees."""
        conn = self.db_connection.connect()
        if not conn:
            return False

        try:
            with conn.cursor() as cursor:
                mdp_hashe = self._hasher_mdp(user.get_mdp())
                sql = "INSERT INTO utilisateur (code, mdp, role, personnel) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (user.get_code(), mdp_hashe, user.get_role(), user.get_id_personnel()))
                conn.commit()
                print(f"Utilisateur {user.get_code()} enregistre avec succes.")
                return True
        except pymysql.MySQLError as e:
            print(f"Erreur PyMySQL: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def modifier_utilisateur(self, user: ModeleUser) -> None:
        """Met a jour les informations d'un utilisateur existant."""
        conn = self.db_connection.connect()
        if not conn:
            return

        try:
            with conn.cursor() as cursor:
                mdp_hashe = self._hasher_mdp(user.get_mdp())
                sql = "UPDATE utilisateur SET mdp=%s, role=%s, personnel=%s WHERE code=%s"
                cursor.execute(sql, (mdp_hashe, user.get_role(), user.get_id_personnel(), user.get_code()))
                conn.commit()
                print(f"Utilisateur avec code '{user.get_code()}' modifie avec succes.")
        except pymysql.MySQLError as e:
            print(f"Erreur PyMySQL: {e}")
            conn.rollback()
        finally:
            conn.close()

    def rechercher_utilisateur(self, code: str) -> dict | None:
        """
        Recherche un utilisateur par son code et joint les informations du personnel.
        """
        conn = self.db_connection.connect()
        if not conn:
            return None

        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT u.code, u.mdp, u.role, u.personnel AS code_personnel,
                       p.nom, p.prenom, p.mail, p.contact, p.photo_path, p.fonction, p.est_responsable
                FROM utilisateur u
                JOIN personnel p ON u.personnel = p.code
                WHERE u.code = %s
                """
                cursor.execute(sql, (code,))
                return cursor.fetchone()
        except Exception as e:
            print(f"Erreur PyMySQL: {e}")
            return None
        finally:
            conn.close()

    def supprimer_utilisateur(self, code: str) -> None:
        """Supprime un utilisateur de la base de donnees."""
        conn = self.db_connection.connect()
        if not conn:
            return

        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM utilisateur WHERE code = %s"
                cursor.execute(sql, (code,))
                conn.commit()
                print(f"Utilisateur avec code '{code}' supprime avec succes.")
        except pymysql.MySQLError as e:
            print(f"Erreur PyMySQL: {e}")
            conn.rollback()
        finally:
            conn.close()

    def rechercher_code_par_login(self, identifiant: str) -> str | None:
        """
        Recherche le code d'un utilisateur a partir d'un identifiant de connexion.
        Recherche par (par ordre de priorite implicite dans le WHERE) :
        1. code utilisateur (u.code)
        2. email (p.mail)
        3. contact/telephone (p.contact)
        4. code personnel (u.personnel)
        5. role (u.role)
        """
        conn = self.db_connection.connect()
        if not conn:
            return None

        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT u.code 
                FROM utilisateur u
                LEFT JOIN personnel p ON u.personnel = p.code
                WHERE u.code = %s 
                   OR p.mail = %s 
                   OR p.contact = %s 
                   OR u.personnel = %s 
                   OR u.role = %s
                LIMIT 1
                """
                cursor.execute(sql, (identifiant, identifiant, identifiant, identifiant, identifiant))
                resultat = cursor.fetchone()
                if resultat:
                    return resultat["code"]
        except Exception as e:
            print(f"Erreur rechercher_code_par_login: {e}")
            return None
        finally:
            conn.close()
        return None

    def rechercher_utilisateurs_par_login(self, identifiant: str) -> list[dict]:
        """
        Recherche TOUS les utilisateurs correspondant a un identifiant.
        Cela permet de gerer le cas où plusieurs utilisateurs ont le même rôle
        et tentent de se connecter avec le nom de leur rôle (ex: 'Chirurgien').
        """
        conn = self.db_connection.connect()
        if not conn:
            return []

        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT u.code, u.mdp, u.role, u.personnel AS code_personnel,
                       p.nom, p.prenom, p.mail, p.contact, p.photo_path, p.fonction, p.est_responsable
                FROM utilisateur u
                LEFT JOIN personnel p ON u.personnel = p.code
                WHERE u.code = %s 
                   OR p.mail = %s 
                   OR p.contact = %s 
                   OR u.personnel = %s 
                   OR u.role = %s
                """
                cursor.execute(sql, (identifiant, identifiant, identifiant, identifiant, identifiant))
                return cursor.fetchall()
        except Exception as e:
            print(f"Erreur rechercher_utilisateurs_par_login: {e}")
            return []
        finally:
            conn.close()

    def rechercher_code_par_role(self, role: str) -> str | None:
        return self.rechercher_code_par_login(role)

    def rechercher_par_code_personnel(self, code_personnel: str) -> dict | None:
        """
        Recherche un utilisateur via le code personnel lie.
        Permet d'identifier un utilisateur precis parmi ceux du meme role.
        """
        conn = self.db_connection.connect()
        if not conn:
            return None

        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT u.code, u.mdp, u.role, u.personnel AS code_personnel,
                       p.nom, p.prenom, p.mail, p.contact, p.photo_path, p.fonction, p.est_responsable
                FROM utilisateur u
                JOIN personnel p ON u.personnel = p.code
                WHERE u.personnel = %s
                """
                cursor.execute(sql, (code_personnel,))
                return cursor.fetchone()
        except pymysql.MySQLError as e:
            print(f"Erreur PyMySQL: {e}")
            return None
        finally:
            conn.close()
