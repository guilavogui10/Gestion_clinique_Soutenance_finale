import pymysql
import pymysql.cursors # Pour utiliser DictCursor
import pymysql
#from pymysqlpool.pool import Pool # Importe la classe Pool
import traceback
import os

class DBConnection:
    def __init__(self, host="localhost", user="root", password="", database="soutenance", port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None # Initialise l'attribut de connexion à None

    def connect(self):
        """
        Tente d'établir une connexion à la base de données.
        Si une connexion existante est ouverte, elle la ferme d'abord.
        Retourne l'objet de connexion ou None en cas d'erreur.
        """
        # Si une connexion existe déjà et est toujours ouverte, la fermer d'abord.
        # pymysql.Connection.open est un attribut booléen qui indique si la connexion est active.
        if self.connection and self.connection.open:
            try:
                print("DBConnection: Fermeture de l'ancienne connexion existante...")
                self.connection.close()
            except pymysql.MySQLError as e:
                print(f"DBConnection: Avertissement - Erreur lors de la fermeture de l'ancienne connexion: {e}")
            finally:
                self.connection = None # S'assurer que l'attribut est réinitialisé

        try:
            # Tente d'établir une nouvelle connexion
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                charset='utf8mb4', # Encodage recommandé pour gérer tous les caractères
                cursorclass=pymysql.cursors.DictCursor # Utilise DictCursor par défaut
            )
            print("DBConnection: Connexion à la base de données réussie.")
            return self.connection

        except pymysql.MySQLError as err:
            import traceback # Pour afficher la trace complète de l'erreur
            print("DBConnection: Erreur de connexion à la base de données : ", err)
            traceback.print_exc() # Affiche la pile d'appels pour le débogage
            self.connection = None # S'assurer que la connexion est None en cas d'échec
            return None

    def close(self):
        """
        Ferme la connexion à la base de données si elle est ouverte.
        """
        if self.connection and self.connection.open:
            try:
                self.connection.close()
                print("DBConnection: Connexion à la base de données fermée.")
            except pymysql.MySQLError as e:
                print(f"DBConnection: Erreur lors de la fermeture de la connexion: {e}")
            finally:
                self.connection = None # S'assurer que l'attribut est réinitialisé après la fermeture
