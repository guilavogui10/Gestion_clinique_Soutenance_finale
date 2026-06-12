import pymysql
import pymysql.cursors
import json
import os
import datetime
from decimal import Decimal

# Fonction pour gérer la sérialisation des dates et des décimales en JSON
def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} non sérialisable")

def get_last_backup_time(tracker_file):
    if os.path.exists(tracker_file):
        with open(tracker_file, 'r') as f:
            return f.read().strip()
    return "1970-01-01 00:00:00"

def update_last_backup_time(tracker_file, current_time):
    with open(tracker_file, 'w') as f:
        f.write(current_time)

def backup_incrementiel():
    # --- CONFIGURATION ---
    db_host = "localhost"
    db_user = "root"
    db_password = ""
    db_name = "soutenance"
    
    backup_dir = "sauvegardes_incrementielles"
    tracker_file = os.path.join(backup_dir, "last_backup.txt")
    
    # Créer le dossier de sauvegarde s'il n'existe pas
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # Obtenir la date de la dernière sauvegarde
    last_backup = get_last_backup_time(tracker_file)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_fichier = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"--- Démarrage de la sauvegarde incrémentielle ---")
    print(f"Dernière sauvegarde : {last_backup}")
    
    try:
        # Connexion à la base de données
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 1. Obtenir la liste de toutes les tables de la base
            cursor.execute("SHOW TABLES")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            
            backup_data = {}
            total_records_saved = 0

            # 2. Interroger chaque table pour les enregistrements modifiés
            for table in tables:
                # On suppose que vous avez ajouté une colonne 'date_modification'
                # Si la colonne n'existe pas, cette requête échouera, donc on utilise un try-except
                try:
                    sql = f"SELECT * FROM `{table}` WHERE date_modification > %s"
                    cursor.execute(sql, (last_backup,))
                    rows = cursor.fetchall()
                    
                    if rows:
                        backup_data[table] = rows
                        total_records_saved += len(rows)
                        print(f"Table '{table}' : {len(rows)} nouveaux/modifiés enregistrements.")
                    else:
                        print(f"Table '{table}' : Aucun changement.")
                except pymysql.MySQLError as e:
                    # Si la colonne date_modification n'existe pas encore sur une table
                    print(f"⚠️ Table '{table}' ignorée (la colonne 'date_modification' est-elle manquante ?) - Erreur: {e.args[1]}")

            # 3. Sauvegarder les données dans un fichier JSON
            if total_records_saved > 0:
                filename = os.path.join(backup_dir, f"backup_{timestamp_fichier}.json")
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, default=json_serial, indent=4, ensure_ascii=False)
                print(f"\nOK: Sauvegarde réussie : {total_records_saved} enregistrements écrits dans {filename}")
                
                # Mettre à jour le fichier de suivi du temps
                update_last_backup_time(tracker_file, current_time)
            else:
                print("\nINFO: Aucune nouvelle donnée à sauvegarder depuis la dernière fois.")
                update_last_backup_time(tracker_file, current_time)

    except pymysql.MySQLError as e:
        print(f"Erreur de connexion à la base de données : {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    backup_incrementiel()
