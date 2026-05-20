"""
init_audit_tables.py
--------------------
Script pour initialiser les tables d'audit et de tentatives OTP.
A executer une seule fois apres l'installation.
"""

import pymysql
import os
import sys

# Ajouter le repertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connexion.db_connection import DBConnection


def creer_tables():
    """Cree les tables d'audit et de tentatives OTP."""
    
    print("=" * 70)
    print("INITIALISATION DES TABLES D'AUDIT")
    print("=" * 70)
    
    db = DBConnection()
    conn = db.connect()
    
    if not conn:
        print("ERREUR : Impossible de se connecter a la base de donnees")
        return False
    
    try:
        cursor = conn.cursor()
        
        # ====================================================================
        # Table audit_permissions
        # ====================================================================
        print("\nCreation de la table 'audit_permissions'...")
        
        sql_audit = """
        CREATE TABLE IF NOT EXISTS audit_permissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            
            -- Informations sur le demandeur
            code_demandeur VARCHAR(20) NOT NULL,
            role_demandeur VARCHAR(100) NOT NULL,
            est_responsable BOOLEAN DEFAULT FALSE,
            
            -- Informations sur l'action
            action VARCHAR(50) NOT NULL,
            contexte TEXT,
            
            -- Informations sur l'autorisation
            code_autorisateur VARCHAR(20),
            statut VARCHAR(20) NOT NULL,
            
            -- Informations techniques
            code_otp_envoye VARCHAR(10),
            email_destinataire VARCHAR(255),
            
            -- Horodatage
            date_demande DATETIME DEFAULT CURRENT_TIMESTAMP,
            date_reponse DATETIME NULL,
            
            -- Metadonnees
            ip_demandeur VARCHAR(45),
            user_agent TEXT,
            
            INDEX idx_demandeur (code_demandeur),
            INDEX idx_autorisateur (code_autorisateur),
            INDEX idx_statut (statut),
            INDEX idx_date_demande (date_demande)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(sql_audit)
        print("OK - Table 'audit_permissions' creee avec succes")
        
        # ====================================================================
        # Table otp_tentatives
        # ====================================================================
        print("\nCreation de la table 'otp_tentatives'...")
        
        sql_tentatives = """
        CREATE TABLE IF NOT EXISTS otp_tentatives (
            id INT AUTO_INCREMENT PRIMARY KEY,
            
            -- Identification
            code_utilisateur VARCHAR(20) NOT NULL,
            identifiant_otp VARCHAR(255) NOT NULL,
            
            -- Compteurs
            nb_tentatives INT DEFAULT 0,
            nb_echecs INT DEFAULT 0,
            
            -- Statut
            est_bloque BOOLEAN DEFAULT FALSE,
            date_blocage DATETIME NULL,
            
            -- Horodatage
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
            date_derniere_tentative DATETIME NULL,
            
            UNIQUE KEY unique_otp (identifiant_otp),
            INDEX idx_utilisateur (code_utilisateur),
            INDEX idx_bloque (est_bloque)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(sql_tentatives)
        print("OK - Table 'otp_tentatives' creee avec succes")
        
        conn.commit()
        
        # ====================================================================
        # Verification
        # ====================================================================
        print("\nVerification des tables creees...")
        
        cursor.execute("SHOW TABLES LIKE 'audit_permissions'")
        if cursor.fetchone():
            print("OK - Table 'audit_permissions' existe")
        else:
            print("ERREUR - Table 'audit_permissions' introuvable")
        
        cursor.execute("SHOW TABLES LIKE 'otp_tentatives'")
        if cursor.fetchone():
            print("OK - Table 'otp_tentatives' existe")
        else:
            print("ERREUR - Table 'otp_tentatives' introuvable")
        
        print("\n" + "=" * 70)
        print("INITIALISATION TERMINEE AVEC SUCCES")
        print("=" * 70)
        print("\nLes tables suivantes ont ete creees :")
        print("  - audit_permissions : Tracabilite des demandes d'autorisation")
        print("  - otp_tentatives : Limitation des tentatives OTP")
        print("\nVous pouvez maintenant utiliser le systeme de permissions.")
        
        return True
        
    except pymysql.MySQLError as e:
        print(f"\nERREUR MySQL : {e}")
        conn.rollback()
        return False
        
    except Exception as e:
        print(f"\nERREUR inattendue : {e}")
        conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()


def verifier_tables_existantes():
    """Verifie si les tables existent deja."""
    
    db = DBConnection()
    conn = db.connect()
    
    if not conn:
        return False, False
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES LIKE 'audit_permissions'")
        audit_existe = cursor.fetchone() is not None
        
        cursor.execute("SHOW TABLES LIKE 'otp_tentatives'")
        tentatives_existe = cursor.fetchone() is not None
        
        return audit_existe, tentatives_existe
        
    except Exception as e:
        print(f"Erreur lors de la verification : {e}")
        return False, False
        
    finally:
        if conn:
            conn.close()


def main():
    """Point d'entree principal."""
    
    print("\nScript d'initialisation des tables d'audit\n")
    
    # Verifier si les tables existent deja
    audit_existe, tentatives_existe = verifier_tables_existantes()
    
    if audit_existe and tentatives_existe:
        print("ATTENTION - Les tables existent deja.")
        reponse = input("\nVoulez-vous les recreer ? (o/N) : ").strip().lower()
        
        if reponse != 'o':
            print("\nOperation annulee.")
            return
        
        print("\nATTENTION : Les donnees existantes seront perdues !")
        confirmation = input("Etes-vous sur ? Tapez 'OUI' pour confirmer : ").strip()
        
        if confirmation != 'OUI':
            print("\nOperation annulee.")
            return
        
        # Supprimer les tables existantes
        db = DBConnection()
        conn = db.connect()
        try:
            cursor = conn.cursor()
            print("\nSuppression des tables existantes...")
            cursor.execute("DROP TABLE IF EXISTS otp_tentatives")
            cursor.execute("DROP TABLE IF EXISTS audit_permissions")
            conn.commit()
            print("OK - Tables supprimees")
        except Exception as e:
            print(f"ERREUR lors de la suppression : {e}")
            return
        finally:
            if conn:
                conn.close()
    
    # Creer les tables
    if creer_tables():
        print("\nOK - Initialisation reussie !")
    else:
        print("\nERREUR - Echec de l'initialisation")
        sys.exit(1)


if __name__ == "__main__":
    main()
