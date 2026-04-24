import pymysql
from core.connexion_db import DBConnection
from models.model_patient import Patient
DictCursor = pymysql.cursors.DictCursor

class PatientDao:
    def __init__(self):
        self.db_manager = DBConnection()

        # methode de generation automatique de code patient
    def generate_code_patient(self):
        conn = self.db_manager.connect()
        if not conn:
            return False
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute(
                    "SELECT code_patient FROM patients ORDER BY code_patient DESC LIMIT 1"
                )
                row = cursor.fetchone()

                if row:
                    last_code = int(row["code_patient"][3:])
                    new_code = f"PAT{last_code + 1:03d}"
                else:
                    new_code = "PAT001"

                return new_code
        finally:
            conn.close()

    # methode d'ajout de patient dans la base de donnée
    def createPatient(self, patient:Patient):
        conn = self.db_manager.connect()
        if not conn:
            return False
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """INSERT INTO patients(code_patient, nom, prenom, telephone, naissance,genre, profession, adresse ) 
                VALUES
                (%s, %s, %s, %s,%s,%s,%s,%s)
                """
                cursor.execute(sql,(
                    patient.get_code_patient(),
                    patient.get_nom(),
                    patient.get_prenom(),
                    patient.get_telephone(),
                    patient.get_naissance(),
                    patient.get_genre(),
                    patient.get_profession(),
                    patient.get_adresse(),

                ))
                conn.commit()
                return True, f"patient ajouté avec succès !"

        except pymysql.MySQLError as e:
            conn.rollback()
            return False , f"Erreur d'ajout du patient : {e}"

        finally:
            conn.close()

    # methode de modification d'un patient
    def updatePatient(self, patient: Patient):
        # appelle de la methode connexion
        conn = self.db_manager.connect()
        if not conn:
            return False , f"Erreur de connexion"
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                        UPDATE patients SET
                        nom = %s,
                        prenom = %s,
                        telephone = %s,
                        naissance = %s, 
                        genre = %s,
                        profession = %s,
                        adresse = %s
                        WHERE code_patient = %s
                """
                cursor.execute(sql,(
                    patient.get_nom(),
                    patient.get_prenom(),
                    patient.get_telephone(),
                    patient.get_naissance(),
                    patient.get_genre(),
                    patient.get_profession(),
                    patient.get_adresse(),
                    patient.get_code_patient()
                ))
                conn.commit()
                return True , f"patient modifié avec succès"
        except pymysql.MySQLError as e:
            conn.rollback()
            return False , f"Erreur de modification du patient: {e}"
        finally:
            conn.close()

    # methode de lecture de tous les patients
    def reedAllPatient(self):
        conn= self.db_manager.connect()
        if not conn:
            return []
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("""
                                SELECT * FROM patients
                               """)
                rows = cursor.fetchall()
                # conversion des données brutes en objet
                liste_patient = []
                for row in rows:
                    # creation d'un objet patient pour chaque ligne de la db
                    patient = Patient(code_patient=row['code_patient'],
                                      nom=row["nom"],
                                      prenom=row["prenom"],
                                      telephone=row["telephone"],
                                      naissance=row["naissance"],
                                      genre=row["genre"],
                                      profession=row["profession"],
                                      adresse=row["adresse"]
                                      )
                    liste_patient.append(patient)
                return liste_patient # ici on retourne liste object pas de dictionnaire
        except pymysql.MySQLError as e:
            print("Erreur de lecture des patients:", e)
            return []
        finally:
            conn.close()
        
    # methode pour lister un patient par son code_patient
    def reed_by_code_patient(self, code_patient):
        conn = self.db_manager.connect()
        if not conn:
            return None
        try:
            with conn.cursor(DictCursor) as cursor:
                slq = "SELECT * FROM patients WHERE code_patient= %s"
                cursor.execute(slq, (code_patient,))
                row = cursor.fetchone() # utilisation de fechone pour recuperer une seule ligne
                if row:
                    # conversion des données dictionnaire en objet
                    
                    patient = Patient(
                        code_patient= row["code_patient"],
                        nom= row["nom"],
                        prenom= row["prenom"],
                        telephone= row["telephone"],
                        naissance=row["naissance"],
                        genre=row["genre"],
                        profession=row["profession"],
                        adresse= row["adresse"]
                    )
                    return patient
                else:
                    return None # aucun patient retrouvé
        except pymysql.MySQLError as e:
            print(f"Erreur de lecture d'un patient:{e}")
            return None
        finally:
            conn.close()

    # methode de lecture par des patients par sexe
    def reed_by_genre_patient(self, sexe):
        conn = self.db_manager.connect()
        if not conn:
            return []
        # declaration de la liste des patients
        liste_patients = []
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = "SELECT * FROM patients WHERE genre = %s"
                cursor.execute(sql,(sexe,))
                rows = cursor.fetchall()
                # parcourt des dictionnaire pour transformer en objet
                for row in rows:
                    patient = Patient(
                        code_patient= row["code_patient"],
                        nom= row["nom"],
                        prenom= row["prenom"],
                        telephone= row["telephone"],
                        naissance=row["naissance"],
                        genre= row["genre"],
                        profession=row["profession"],
                        adresse= row["adresse"]
                    )
                    liste_patients.append(patient)
                return liste_patients
        except pymysql.MySQLError as e:
            print(f"Erreur de lecture par sexe des patient dans le dao: {e}")
            return []
        finally:
            conn.close()

            
                
        

    # methode de lecture des patients par criteres: code, nom, date
    def reed_by_critere_patient(self, critere):
        conn = self.db_manager.connect()
        if not conn:
            return []
        #declaration d'une liste de patients
        patients = []
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                        SELECT * FROM patients WHERE
                        code_patient LIKE %s
                        OR adresse LIKE %s
                        OR telephone LIKE %s
                        OR naissance LIKE %s
                        OR prenom LIKE %s
                    """
                # On entoure le critère de % pour que la recherche soit globale
                valeur_recherche = f"%{critere}%"
                cursor.execute(sql, (valeur_recherche,valeur_recherche, valeur_recherche,valeur_recherche,valeur_recherche))
                rows = cursor.fetchall()

                # parcourt de la liste de dictionnaire
                for row in rows:
                    # creation de l'objet patient pour chaque ligne trouvé
                    patient = Patient(
                        code_patient= row["code_patient"],
                        nom= row["nom"],
                        prenom= row["prenom"],
                        telephone= row["telephone"],
                        naissance= row["naissance"],
                        genre= row["genre"],
                        profession= row["profession"],
                        adresse= row["adresse"]
                    )
                    patients.append(patient)
                return patients         
        except pymysql.MySQLError as e:
            print(f"Erreur de lecture des patients dans le dao : {e}")
            return []

        finally:
            conn.close()
    
    # methode de statistiques des patients
    def stat_patients(self):
        """
       retourner un dictionnaire contenant les statistiques détaillées des patients
        """
        stats = {
            'total': 0,
            'filles': 0,
            'garçons': 0,
            'enfants': 0,
            'jeunes': 0,
            'adultes': 0,
        }
        conn = self.db_manager.connect()
        if not conn:
            return stats
        try:
            with conn.cursor(DictCursor) as cursor:
                # 1 premiere requete: compter le total et par genre
                sql = """
                        SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN genre = 'Femme' THEN 1 ELSE 0 END) as filles,
                        SUM(CASE WHEN genre = 'Homme' THEN 1 ELSE 0 END) as garçons
                        FROM patients
                    """
                cursor.execute(sql)
                row_total_et_genre = cursor.fetchone()
                if row_total_et_genre:
                    stats['total']= row_total_et_genre['total'] or 0
                    stats['filles'] = row_total_et_genre['filles'] or 0
                    stats['garçons']= row_total_et_genre['garçons'] or 0
                
                # 2 deuxieme requete: compter par tranche d'age
                # utilisation du timestamdif pour calculer l'age à partir de la colonne naissance
                sql_age = """
                            SELECT 
                            SUM(CASE WHEN TIMESTAMPDIFF(YEAR, naissance, CURDATE()) < 18 THEN 1 ELSE 0 END) as enfants,
                            SUM(CASE WHEN TIMESTAMPDIFF(YEAR, naissance, CURDATE()) BETWEEN 18 AND 45 THEN 1 ELSE 0 END) as jeunes,
                            SUM(CASE WHEN TIMESTAMPDIFF(YEAR, naissance, CURDATE())>45 THEN 1 ELSE 0 END) as adultes
                            FROM patients
                        """
                cursor.execute(sql_age)
                row_age = cursor.fetchone()
                if row_age:
                    stats["enfants"] = row_age["enfants"] or 0
                    stats["jeunes"] = row_age["jeunes"] or 0
                    stats["adultes"] = row_age["adultes"] or 0
                
                return stats

        except pymysql.MySQLError as e:
            print(f"Erreur de comptage des statistiques des patients: {e}")
            return stats
        finally:
            conn.close()
    
        

