import pymysql
import bcrypt
# On suppose que ton fichier s'appelle 'connexion_db.py'
from core.connexion_db import DBConnection
from models.modele_user import ModeleUser

class UserDAO:
    def __init__(self):
        self.db_connection = DBConnection()

    def _get_db_connection(self):
        # Méthode pour obtenir une nouvelle connexion pour chaque opération
        return DBConnection()

    def _hasher_mdp(self, mdp: str) -> str:
        """Hache le mot de passe avant de l'enregistrer."""
        mot_de_passe_bytes = mdp.encode('utf-8')
        sel = bcrypt.gensalt()
        mdp_hashe_bytes = bcrypt.hashpw(mot_de_passe_bytes, sel)
        return mdp_hashe_bytes.decode('utf-8')
    
    def generer_nouveau_code(self) -> str:
        """Génère un nouveau code unique comme 'U0001'."""
        conn = self.db_connection.connect()
        #connexion = self._get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Récupère le dernier code utilisateur par ordre décroissant
                sql = "SELECT code FROM utilisateur ORDER BY code DESC LIMIT 1"
                cursor.execute(sql)
                resultat = cursor.fetchone()
                
                dernier_numero = 0
                if resultat:
                    dernier_code = resultat[0]
                    # On extrait la partie numérique (ex: '0001')
                    dernier_numero = int(dernier_code[1:]) 
                
                # On incrémente le numéro et on le formate
                nouveau_numero = dernier_numero + 1
                nouveau_code = f"U{nouveau_numero:04d}" # Formatage en 4 chiffres avec des zéros
                return nouveau_code
        except Exception as e:
            print(f"Erreur lors de la génération du code : {e}")
            return None
        finally:
            conn.close()

    def enregistrer_utilisateur(self, user: ModeleUser):
        """Enregistre un nouvel utilisateur dans la base de données."""
        conn = self.db_connection.connect()
        try:
            with conn.cursor() as cursor:
                mdp_hashe = self._hasher_mdp(user.get_mdp())
                # Assurez-vous que la table 'personnel' contient une colonne 'photo_path'
                # et que vous avez un moyen de lier l'utilisateur au personnel.
                # Votre code actuel semble lier un utilisateur à un membre du personnel.
                # L'enregistrement de l'utilisateur n'inclut pas de chemin de photo, ce qui est correct.
                # C'est la fonction qui crée le personnel qui doit le faire.
                sql = "INSERT INTO utilisateur (code, mdp, role, personnel) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (user.get_code(), mdp_hashe, user.get_role(), user.get_id_personnel()))
                conn.commit()
                print(f"Utilisateur {user.get_code()} enregistré avec succès.")
                return True
        except pymysql.MySQLError as e:
            print(f"Erreur PyMySQL: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def modifier_utilisateur(self, user: ModeleUser):
        """Met à jour les informations d'un utilisateur existant."""
        conn = self.db_connection.connect()
        try:
            with conn.cursor() as cursor:
                mdp_hashe = self._hasher_mdp(user.get_mdp())
                sql = "UPDATE utilisateur SET mdp=%s, role=%s, personnel=%s WHERE code=%s"
                cursor.execute(sql, (mdp_hashe, user.get_role(), user.get_id_personnel(), user.get_code()))
                conn.commit()
                print(f"Utilisateur avec code '{user.get_code()}' modifié avec succès.")
        except pymysql.MySQLError as e:
            print(f"Erreur PyMySQL: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # La méthode de recherche doit être modifiée pour inclure le chemin de la photo
    def rechercher_utilisateur(self, code: str) -> dict:
        """ 
        Recherche un utilisateur par son code et joint les informations du personnel.
        """
        conn = self.db_connection.connect()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor: # Utilise un curseur de dictionnaire
                # REQUÊTE MODIFIÉE : Ajoute p.photo_path
                sql = """
                SELECT u.code, u.mdp, u.role, p.nom, p.prenom, p.mail, p.photo_path
                FROM utilisateur u
                JOIN personnel p ON u.personnel = p.code
                WHERE u.code = %s;
                """
                cursor.execute(sql, (code,))
                resultat = cursor.fetchone()
                
                if resultat:
                    return resultat
                return None
        except Exception as e:
            print(f"Erreur PyMySQL: {e}")
            return None
        finally:
            conn.close()

    def supprimer_utilisateur(self, code: str):
        """Supprime un utilisateur de la base de données."""
        conn = self.db_connection.connect()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM utilisateur WHERE code = %s"
                cursor.execute(sql, (code,))
                conn.commit()
                print(f"Utilisateur avec code '{code}' supprimé avec succès.")
        except pymysql.MySQLError as e:
            print(f"Erreur PyMySQL: {e}")
            conn.rollback()
        finally:
            conn.close()

    def rechercher_code_par_role(self, role: str) -> str:
        """
        Recherche le code d'un utilisateur en fonction de son rôle.
        Retourne le premier code trouvé.
        """
        conn = self.db_connection.connect()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor: # Utilise le curseur de dictionnaire pour plus de lisibilité
                sql = "SELECT code FROM utilisateur WHERE role = %s LIMIT 1"
                cursor.execute(sql, (role,))
                resultat = cursor.fetchone()
                
                if resultat:
                    return resultat['code'] # Renvoie le code
                
                return None
        except pymysql.MySQLError as e:
            print(f"Erreur PyMySQL: {e}")
            return None
        finally:
            conn.close()