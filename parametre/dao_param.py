# /dao/CabinetDAO.py

import pymysql
# Assurez-vous d'importer votre classe de connexion DBConnection
from connexion.db_connection import DBConnection 
from parametre.model_param import Parametre # Importe le Modèle créé ci-dessus

DictCursor = pymysql.cursors.DictCursor

class CabinetDAO:
    def __init__(self):
        self.db_manager = DBConnection() 

    def get_info_cabinet(self):
        conn = self.db_manager.connect()
        if not conn:
            return None
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """SELECT nom_cabinet, logo, adresse, email, telephone, 
                         devise, fuseau_horaire, format_date, format_heure, notes, date_creation 
                         FROM cabinet LIMIT 1"""
                cursor.execute(sql)
                return cursor.fetchone()
        except pymysql.MySQLError as e:
            print(f"Erreur DAO Cabinet: {e}")
            return None


    
    def insert_info_cabinet(self, cabinet_obj: Parametre):

        conn = self.db_manager.connect()
        if not conn:
            return False, "Erreur de connexion à la base."

        try:
            with conn.cursor(DictCursor) as cursor:

                # Vérifier s’il existe déjà une ligne SANS ouvrir une deuxième connexion !
                cursor.execute("SELECT id FROM cabinet LIMIT 1")
                existe = cursor.fetchone()

                if existe:
                    return False, "Les informations du cabinet existent déjà. Utilisez update_info_cabinet pour les modifier."

                sql = """
                    INSERT INTO cabinet (nom_cabinet, logo, adresse, email, telephone, 
                                       devise, fuseau_horaire, format_date, format_heure, notes, date_creation)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    cabinet_obj.get_nom_cabinet(),
                    cabinet_obj.get_logo(),
                    cabinet_obj.get_adresse(),
                    cabinet_obj.get_email(),
                    cabinet_obj.get_telephone(),
                    cabinet_obj.get_devise(),
                    cabinet_obj.get_fuseau_horaire(),
                    cabinet_obj.get_format_date(),
                    cabinet_obj.get_format_heure(),
                    cabinet_obj.get_notes(),
                    cabinet_obj.get_date_creation()
                ))
                conn.commit()
                return True, "Informations du cabinet insérées avec succès."

        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur insertion: {e}"


    def update_info_cabinet(self, cabinet_obj: Parametre):

        conn = self.db_manager.connect()
        if not conn:
            return False, "Erreur de connexion à la base."

        try:
            with conn.cursor(DictCursor) as cursor:

                # Vérifie qu’il existe bien une ligne avec id = 1
                cursor.execute("SELECT id FROM cabinet WHERE id = 0")
                existe = cursor.fetchone()

                if not existe:
                    return False, "Impossible de mettre à jour : aucune ligne avec id = 0."

                sql = """
                    UPDATE cabinet
                    SET nom_cabinet = %s, logo = %s, adresse = %s, email = %s, telephone = %s,
                        devise = %s, fuseau_horaire = %s, format_date = %s, format_heure = %s, notes = %s, date_creation = %s
                    WHERE id = 0
                """

                cursor.execute(sql, (
                    cabinet_obj.get_nom_cabinet(),
                    cabinet_obj.get_logo(),
                    cabinet_obj.get_adresse(),
                    cabinet_obj.get_email(),
                    cabinet_obj.get_telephone(),
                    cabinet_obj.get_devise(),
                    cabinet_obj.get_fuseau_horaire(),
                    cabinet_obj.get_format_date(),
                    cabinet_obj.get_format_heure(),
                    cabinet_obj.get_notes(),
                    cabinet_obj.get_date_creation()
                ))

                conn.commit()
                return True, "Informations du cabinet mises à jour avec succès."

        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur mise à jour: {e}"
