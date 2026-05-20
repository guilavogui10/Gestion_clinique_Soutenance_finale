"""
dao_audit_permission.py
-----------------------
DAO pour la gestion des audits de permissions.
Trace toutes les demandes d'autorisation et leurs résultats.
"""

import pymysql
from datetime import datetime
from typing import List, Optional, Dict
from connexion.db_connection import DBConnection


class AuditPermissionDAO:
    """DAO pour gérer les audits de permissions."""
    
    def __init__(self):
        self.db_connection = DBConnection()
    
    def creer_demande(
        self,
        code_demandeur: str,
        role_demandeur: str,
        est_responsable: bool,
        action: str,
        contexte: str,
        code_autorisateur: str,
        email_destinataire: str,
        code_otp_envoye: str = None,
        ip_demandeur: str = None
    ) -> Optional[int]:
        """
        Crée une nouvelle demande d'autorisation dans l'audit.
        
        Returns:
            ID de la demande créée ou None si erreur
        """
        conn = self.db_connection.connect()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO audit_permissions (
                    code_demandeur, role_demandeur, est_responsable,
                    action, contexte, code_autorisateur,
                    statut, code_otp_envoye, email_destinataire,
                    ip_demandeur
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    code_demandeur,
                    role_demandeur,
                    est_responsable,
                    action,
                    contexte,
                    code_autorisateur,
                    'en_attente',
                    code_otp_envoye,
                    email_destinataire,
                    ip_demandeur
                ))
                conn.commit()
                return cursor.lastrowid
        except pymysql.MySQLError as e:
            print(f"Erreur création demande audit: {e}")
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
    
    def mettre_a_jour_statut(
        self,
        identifiant_otp: str,
        statut: str,
        code_autorisateur: str = None
    ) -> bool:
        """
        Met à jour le statut d'une demande d'autorisation.
        
        Args:
            identifiant_otp: Identifiant unique de la demande
            statut: Nouveau statut (autorise, refuse, expire)
            code_autorisateur: Code de celui qui a autorisé/refusé
        
        Returns:
            True si mise à jour réussie
        """
        conn = self.db_connection.connect()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Extraire le code_demandeur et contexte de l'identifiant_otp
                # Format: {code_demandeur}_{action}_{contexte}
                parts = identifiant_otp.split('_', 2)
                if len(parts) < 3:
                    return False
                
                code_demandeur = parts[0]
                action = parts[1]
                contexte = parts[2] if len(parts) > 2 else ''
                
                sql = """
                UPDATE audit_permissions
                SET statut = %s,
                    date_reponse = %s,
                    code_autorisateur = COALESCE(%s, code_autorisateur)
                WHERE code_demandeur = %s
                  AND action = %s
                  AND contexte = %s
                  AND statut = 'en_attente'
                ORDER BY date_demande DESC
                LIMIT 1
                """
                cursor.execute(sql, (
                    statut,
                    datetime.now(),
                    code_autorisateur,
                    code_demandeur,
                    action,
                    contexte
                ))
                conn.commit()
                return cursor.rowcount > 0
        except pymysql.MySQLError as e:
            print(f"Erreur mise à jour statut audit: {e}")
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
    
    def obtenir_demandes_en_attente(
        self,
        code_autorisateur: str
    ) -> List[Dict]:
        """
        Récupère toutes les demandes en attente pour un autorisateur.
        
        Args:
            code_autorisateur: Code du responsable/DG
        
        Returns:
            Liste des demandes en attente
        """
        conn = self.db_connection.connect()
        if not conn:
            return []
        
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT 
                    id,
                    code_demandeur,
                    role_demandeur,
                    action,
                    contexte,
                    email_destinataire,
                    date_demande,
                    TIMESTAMPDIFF(SECOND, date_demande, NOW()) as secondes_ecoulees
                FROM audit_permissions
                WHERE code_autorisateur = %s
                  AND statut = 'en_attente'
                ORDER BY date_demande DESC
                """
                cursor.execute(sql, (code_autorisateur,))
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"Erreur récupération demandes en attente: {e}")
            return []
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
    
    def obtenir_historique_utilisateur(
        self,
        code_utilisateur: str,
        limite: int = 50
    ) -> List[Dict]:
        """
        Récupère l'historique des demandes d'un utilisateur.
        
        Args:
            code_utilisateur: Code de l'utilisateur
            limite: Nombre maximum de résultats
        
        Returns:
            Liste des demandes
        """
        conn = self.db_connection.connect()
        if not conn:
            return []
        
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT 
                    id,
                    action,
                    contexte,
                    statut,
                    code_autorisateur,
                    date_demande,
                    date_reponse,
                    TIMESTAMPDIFF(SECOND, date_demande, date_reponse) as temps_reponse_sec
                FROM audit_permissions
                WHERE code_demandeur = %s
                ORDER BY date_demande DESC
                LIMIT %s
                """
                cursor.execute(sql, (code_utilisateur, limite))
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"Erreur récupération historique: {e}")
            return []
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
    
    def obtenir_statistiques(
        self,
        date_debut: datetime = None,
        date_fin: datetime = None
    ) -> Dict:
        """
        Récupère des statistiques sur les demandes d'autorisation.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        conn = self.db_connection.connect()
        if not conn:
            return {}
        
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                where_clause = ""
                params = []
                
                if date_debut and date_fin:
                    where_clause = "WHERE date_demande BETWEEN %s AND %s"
                    params = [date_debut, date_fin]
                
                sql = f"""
                SELECT 
                    COUNT(*) as total_demandes,
                    SUM(CASE WHEN statut = 'autorise' THEN 1 ELSE 0 END) as autorisees,
                    SUM(CASE WHEN statut = 'refuse' THEN 1 ELSE 0 END) as refusees,
                    SUM(CASE WHEN statut = 'expire' THEN 1 ELSE 0 END) as expirees,
                    SUM(CASE WHEN statut = 'en_attente' THEN 1 ELSE 0 END) as en_attente,
                    AVG(TIMESTAMPDIFF(SECOND, date_demande, date_reponse)) as temps_moyen_reponse_sec
                FROM audit_permissions
                {where_clause}
                """
                cursor.execute(sql, params)
                return cursor.fetchone() or {}
        except pymysql.MySQLError as e:
            print(f"Erreur récupération statistiques: {e}")
            return {}
        finally:
            try:
                if conn and conn.open:
                    conn.close()
            except:
                pass
    
    def nettoyer_anciennes_demandes(self, jours: int = 90) -> int:
        """
        Supprime les demandes de plus de X jours.
        
        Args:
            jours: Nombre de jours à conserver
        
        Returns:
            Nombre de lignes supprimées
        """
        conn = self.db_connection.connect()
        if not conn:
            return 0
        
        try:
            with conn.cursor() as cursor:
                sql = """
                DELETE FROM audit_permissions
                WHERE date_demande < DATE_SUB(NOW(), INTERVAL %s DAY)
                """
                cursor.execute(sql, (jours,))
                conn.commit()
                return cursor.rowcount
        except pymysql.MySQLError as e:
            print(f"Erreur nettoyage anciennes demandes: {e}")
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
