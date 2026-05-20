"""
dao_otp_tentatives.py
---------------------
DAO pour gérer les tentatives OTP et le blocage après échecs.
"""

import pymysql
from datetime import datetime, timedelta
from typing import Optional, Dict
from connexion.db_connection import DBConnection


class OTPTentativesDAO:
    """DAO pour gérer les tentatives OTP."""
    
    # Configuration
    MAX_TENTATIVES = 3  # Nombre maximum de tentatives
    DUREE_BLOCAGE_MINUTES = 15  # Durée du blocage en minutes
    
    def __init__(self):
        self.db_connection = DBConnection()
    
    def creer_ou_obtenir_tentative(
        self,
        code_utilisateur: str,
        identifiant_otp: str
    ) -> Optional[Dict]:
        """
        Crée ou récupère un enregistrement de tentative OTP.
        
        Returns:
            Dictionnaire avec les informations de tentative
        """
        conn = self.db_connection.connect()
        if not conn:
            return None
        
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Vérifier si existe déjà
                sql_select = """
                SELECT * FROM otp_tentatives
                WHERE identifiant_otp = %s
                """
                cursor.execute(sql_select, (identifiant_otp,))
                tentative = cursor.fetchone()
                
                if tentative:
                    return tentative
                
                # Créer nouveau
                sql_insert = """
                INSERT INTO otp_tentatives (
                    code_utilisateur,
                    identifiant_otp,
                    nb_tentatives,
                    nb_echecs
                ) VALUES (%s, %s, 0, 0)
                """
                cursor.execute(sql_insert, (code_utilisateur, identifiant_otp))
                conn.commit()
                
                # Récupérer l'enregistrement créé
                cursor.execute(sql_select, (identifiant_otp,))
                return cursor.fetchone()
                
        except pymysql.MySQLError as e:
            print(f"Erreur création/obtention tentative: {e}")
            try:
                if conn and conn.open:
                    conn.rollback()
            except:
                pass
            return None
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
    
    def incrementer_tentative(
        self,
        identifiant_otp: str,
        est_echec: bool = False
    ) -> bool:
        """
        Incrémente le compteur de tentatives.
        
        Args:
            identifiant_otp: Identifiant unique de l'OTP
            est_echec: True si la tentative a échoué
        
        Returns:
            True si mise à jour réussie
        """
        conn = self.db_connection.connect()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                if est_echec:
                    sql = """
                    UPDATE otp_tentatives
                    SET nb_tentatives = nb_tentatives + 1,
                        nb_echecs = nb_echecs + 1,
                        date_derniere_tentative = %s
                    WHERE identifiant_otp = %s
                    """
                else:
                    sql = """
                    UPDATE otp_tentatives
                    SET nb_tentatives = nb_tentatives + 1,
                        date_derniere_tentative = %s
                    WHERE identifiant_otp = %s
                    """
                
                cursor.execute(sql, (datetime.now(), identifiant_otp))
                conn.commit()
                
                # Vérifier si on doit bloquer
                if est_echec:
                    self._verifier_et_bloquer(identifiant_otp)
                
                return cursor.rowcount > 0
        except pymysql.MySQLError as e:
            print(f"Erreur incrémentation tentative: {e}")
            try:
                if conn and conn.open:
                    conn.rollback()
            except:
                pass
            return False
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
    
    def _verifier_et_bloquer(self, identifiant_otp: str) -> None:
        """
        Vérifie si le nombre d'échecs dépasse le maximum et bloque si nécessaire.
        """
        conn = self.db_connection.connect()
        if not conn:
            return
        
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql_select = """
                SELECT nb_echecs FROM otp_tentatives
                WHERE identifiant_otp = %s
                """
                cursor.execute(sql_select, (identifiant_otp,))
                result = cursor.fetchone()
                
                if result and result['nb_echecs'] >= self.MAX_TENTATIVES:
                    sql_update = """
                    UPDATE otp_tentatives
                    SET est_bloque = TRUE,
                        date_blocage = %s
                    WHERE identifiant_otp = %s
                    """
                    cursor.execute(sql_update, (datetime.now(), identifiant_otp))
                    conn.commit()
        except pymysql.MySQLError as e:
            print(f"Erreur vérification blocage: {e}")
            try:
                if conn and conn.open:
                    conn.rollback()
            except:
                pass
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
    
    def est_bloque(self, identifiant_otp: str) -> bool:
        """
        Vérifie si un OTP est bloqué.
        
        Returns:
            True si bloqué, False sinon
        """
        conn = self.db_connection.connect()
        if not conn:
            return False
        
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT est_bloque, date_blocage
                FROM otp_tentatives
                WHERE identifiant_otp = %s
                """
                cursor.execute(sql, (identifiant_otp,))
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                if not result['est_bloque']:
                    return False
                
                # Vérifier si le blocage a expiré
                if result['date_blocage']:
                    date_deblocage = result['date_blocage'] + timedelta(
                        minutes=self.DUREE_BLOCAGE_MINUTES
                    )
                    if datetime.now() >= date_deblocage:
                        # Débloquer automatiquement
                        self.debloquer(identifiant_otp)
                        return False
                
                return True
        except pymysql.MySQLError as e:
            print(f"Erreur vérification blocage: {e}")
            return False
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
    
    def debloquer(self, identifiant_otp: str) -> bool:
        """
        Débloque un OTP et réinitialise les compteurs.
        
        Returns:
            True si déblocage réussi
        """
        conn = self.db_connection.connect()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                sql = """
                UPDATE otp_tentatives
                SET est_bloque = FALSE,
                    date_blocage = NULL,
                    nb_tentatives = 0,
                    nb_echecs = 0
                WHERE identifiant_otp = %s
                """
                cursor.execute(sql, (identifiant_otp,))
                conn.commit()
                return cursor.rowcount > 0
        except pymysql.MySQLError as e:
            print(f"Erreur déblocage: {e}")
            try:
                if conn and conn.open:
                    conn.rollback()
            except:
                pass
            return False
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
    
    def obtenir_info_tentative(self, identifiant_otp: str) -> Optional[Dict]:
        """
        Récupère les informations sur les tentatives d'un OTP.
        
        Returns:
            Dictionnaire avec les informations ou None
        """
        conn = self.db_connection.connect()
        if not conn:
            return None
        
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT 
                    code_utilisateur,
                    nb_tentatives,
                    nb_echecs,
                    est_bloque,
                    date_blocage,
                    date_derniere_tentative,
                    CASE 
                        WHEN est_bloque AND date_blocage IS NOT NULL THEN
                            TIMESTAMPDIFF(MINUTE, NOW(), 
                                DATE_ADD(date_blocage, INTERVAL %s MINUTE))
                        ELSE 0
                    END as minutes_restantes_blocage
                FROM otp_tentatives
                WHERE identifiant_otp = %s
                """
                cursor.execute(sql, (self.DUREE_BLOCAGE_MINUTES, identifiant_otp))
                return cursor.fetchone()
        except pymysql.MySQLError as e:
            print(f"Erreur récupération info tentative: {e}")
            return None
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
    
    def supprimer_tentative(self, identifiant_otp: str) -> bool:
        """
        Supprime un enregistrement de tentative (après validation réussie).
        
        Returns:
            True si suppression réussie
        """
        conn = self.db_connection.connect()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM otp_tentatives WHERE identifiant_otp = %s"
                cursor.execute(sql, (identifiant_otp,))
                conn.commit()
                return cursor.rowcount > 0
        except pymysql.MySQLError as e:
            print(f"Erreur suppression tentative: {e}")
            try:
                if conn and conn.open:
                    conn.rollback()
            except:
                pass
            return False
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
    
    def nettoyer_anciennes_tentatives(self, heures: int = 24) -> int:
        """
        Supprime les tentatives de plus de X heures.
        
        Args:
            heures: Nombre d'heures à conserver
        
        Returns:
            Nombre de lignes supprimées
        """
        conn = self.db_connection.connect()
        if not conn:
            return 0
        
        try:
            with conn.cursor() as cursor:
                sql = """
                DELETE FROM otp_tentatives
                WHERE date_creation < DATE_SUB(NOW(), INTERVAL %s HOUR)
                """
                cursor.execute(sql, (heures,))
                conn.commit()
                return cursor.rowcount
        except pymysql.MySQLError as e:
            print(f"Erreur nettoyage anciennes tentatives: {e}")
            try:
                if conn and conn.open:
                    conn.rollback()
            except:
                pass
            return 0
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
