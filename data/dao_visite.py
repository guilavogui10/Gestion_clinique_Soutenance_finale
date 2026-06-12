"""
DAO (Data Access Object) pour la gestion des visites
Gère toutes les opérations CRUD et statistiques liées aux visites médicales
"""

import pymysql
from core.connexion_db import DBConnection
from models.model_visite import Visite

DictCursor = pymysql.cursors.DictCursor


class Visitedao:
    """Classe DAO pour la gestion des visites dans la base de données"""
    
    def __init__(self):
        """Initialise le gestionnaire de connexion à la base de données"""
        self.db_manager = DBConnection()
    
    # ==================== GÉNÉRATION DE CODE ====================
    
    def generate_code_visite(self):
        """
        Génère automatiquement un code unique pour une nouvelle visite
        Format: VIST001, VIST002, VIST003...
        
        Returns:
            str: Code visite généré (ex: "VIST005")
        """
        conn = self.db_manager.connect()
        if not conn:
            return "VIST001"  # Code par défaut si connexion échoue
        
        try:
            with conn.cursor(DictCursor) as cursor:
                # Récupère le dernier code visite enregistré
                cursor.execute("SELECT code_visite FROM visite ORDER BY code_visite DESC LIMIT 1")
                row = cursor.fetchone()
                
                if row:
                    try:
                        # Extrait la partie numérique (VIST008 -> "008")
                        last_code_str = row["code_visite"][4:]
                        last_code_int = int(last_code_str)
                        new_code = f"VIST{last_code_int + 1:03d}"
                    except (ValueError, TypeError):
                        # Sécurité si le format est incorrect
                        new_code = "VIST001"
                else:
                    # Première visite dans la base
                    new_code = "VIST001"
                    
                return new_code
        finally:
            conn.close()
    
    # ==================== OPÉRATIONS CRUD ====================
    
    def createVisite(self, visite: Visite):
        """
        Crée une nouvelle visite dans la base de données
        
        Args:
            visite (Visite): Objet visite à enregistrer
            
        Returns:
            tuple: (bool, str) - (succès, message)
        """
        conn = self.db_manager.connect()
        if not conn:
            return False, "Erreur de connexion à la base de données"
        
        try:
            with conn.cursor(DictCursor) as cursor:
                # Déterminer le statut_patient selon le type de visite
                type_visite = visite.get_type_visite().lower()
                
                if type_visite in ["rendez-vous", "rendez vous", "vip"]:
                    statut_patient = "Attente rendez-vous"
                elif type_visite in ["immédiat", "immediat", "contrôle", "controle"]:
                    statut_patient = "Attente consultation"
                else:
                    # Par défaut pour tout autre type
                    statut_patient = "Attente consultation"
                
                sql = """
                    INSERT INTO visite (
                        code_visite, code_patient, code_session, type_visite, 
                        statut_visite, statut_patient, urgent, date_visite
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    visite.get_code_visite(),
                    visite.get_code_patient(),
                    visite.get_code_session(),
                    visite.get_type_visite(),
                    visite.get_statut_visite(),
                    statut_patient,
                    visite.get_urgent(),
                    visite.get_date_visite()
                ))
                conn.commit()
                return True, "Visite créée avec succès !"
        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur lors de la création : {e}"
        finally:
            conn.close()
    
    def deleteVisite(self, code_visite: str) -> tuple:
        conn = self.db_manager.connect()
        if not conn:
            return False, "Erreur de connexion"
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM visite WHERE code_visite = %s", (code_visite,))
                conn.commit()
                return True, "Visite supprimée"
        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur suppression visite : {e}"
        finally:
            conn.close()

    def reedAllvisite(self):
        """
        Récupère toutes les visites de la base de données
        
        Returns:
            list: Liste d'objets Visite
        """
        conn = self.db_manager.connect()
        if not conn:
            return []
        
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute("SELECT * FROM visite")
                rows = cursor.fetchall()
                
                # Conversion des dictionnaires en objets Visite
                liste_visite = []
                for row in rows:
                    visite = Visite(
                        code_visite=row["code_visite"],
                        code_patient=row["code_patient"],
                        code_session=row["code_session"],
                        type_visite=row["type_visite"],
                        statut_visite=row["statut_visite"],
                        statut_patient=row["statut_patient"],
                        urgent=row["urgent"],
                        date_visite=row["date_visite"],
                        date_debut_consultation=row.get("date_debut_consultation")
                    )
                    liste_visite.append(visite)
                return liste_visite
        finally:
            conn.close()
    
    def updateVisite(self, visite: Visite):
        """
        Met à jour une visite existante
        
        Args:
            visite (Visite): Objet visite avec les nouvelles données
            
        Returns:
            tuple: (bool, str) - (succès, message)
        """
        conn = self.db_manager.connect()
        if not conn:
            return False, "Erreur de connexion à la base"
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                    UPDATE visite SET
                        code_patient = %s,
                        code_session = %s,
                        type_visite = %s,
                        statut_visite = %s,
                        statut_patient = %s,
                        urgent = %s,
                        date_visite = %s
                    WHERE code_visite = %s
                """
                cursor.execute(sql, (
                    visite.get_code_patient(),
                    visite.get_code_session(),
                    visite.get_type_visite(),
                    visite.get_statut_visite(),
                    visite.get_statut_patient(),
                    visite.get_urgent(),
                    visite.get_date_visite(),
                    visite.get_code_visite()
                ))
                conn.commit()
                return True, "Visite modifiée avec succès !"
        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur de modification : {e}"
        finally:
            conn.close()
    
    def reeVisite_ByCode_visite(self, code_visite):
        """
        Récupère une visite spécifique par son code
        
        Args:
            code_visite (str): Code de la visite à rechercher
            
        Returns:
            Visite: Objet Visite ou None si non trouvé
        """
        conn = self.db_manager.connect()
        if not conn:
            return None
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = "SELECT * FROM visite WHERE code_visite = %s"
                cursor.execute(sql, (code_visite,))
                row = cursor.fetchone()
                
                if row:
                    visite = Visite(
                        code_visite=row["code_visite"],
                        code_patient=row["code_patient"],
                        code_session=row["code_session"],
                        type_visite=row["type_visite"],
                        statut_visite=row["statut_visite"],
                        statut_patient=row["statut_patient"],
                        urgent=row["urgent"],
                        date_visite=row["date_visite"],
                        date_debut_consultation=row.get("date_debut_consultation")
                    )
                    return visite
                return None
        except pymysql.MySQLError as e:
            print(f"Erreur de lecture : {e}")
            return None
        finally:
            conn.close()
    
    # ==================== STATISTIQUES ====================
    
    def stat_visites_mensuelles(self, code_session: str):
        """
        Calcule le nombre de visites par mois pour une session donnée
        
        Args:
            code_session (str): Code de la session (année)
            
        Returns:
            dict: Dictionnaire avec les mois en clés et le nombre de visites en valeurs
        """
        # Initialisation avec tous les mois à zéro
        stats = {
            'Jan': 0, 'Fév': 0, 'Mar': 0, 'Avr': 0, 'Mai': 0, 'Juin': 0,
            'Juil': 0, 'Août': 0, 'Sep': 0, 'Oct': 0, 'Nov': 0, 'Déc': 0
        }
        
        # Mapping numéro de mois -> nom abrégé
        mois_mapping = {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Juin',
            7: 'Juil', 8: 'Août', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

        conn = self.db_manager.connect()
        if not conn:
            return stats
            
        try:
            with conn.cursor(DictCursor) as cursor:
                # Groupe les visites par mois
                sql = """
                    SELECT MONTH(date_visite) as num_mois, COUNT(*) as total
                    FROM visite
                    WHERE code_session = %s
                    GROUP BY MONTH(date_visite)
                """
                cursor.execute(sql, (code_session,))
                rows = cursor.fetchall()
                
                # Remplit le dictionnaire avec les résultats
                for row in rows:
                    m_idx = row['num_mois']
                    if m_idx in mois_mapping:
                        stats[mois_mapping[m_idx]] = row['total']
                            
                return stats
        except pymysql.MySQLError as e:
            print(f"Erreur SQL : {e}")
            return stats
        finally:
            conn.close()
    
    def stat_evolutive_par_age(self, code_session: str):
        """
        Calcule l'évolution mensuelle des visites par tranche d'âge
        - Enfants : < 18 ans
        - Jeunes : 18-45 ans
        - Adultes : > 45 ans
        
        Args:
            code_session (str): Code de la session
            
        Returns:
            dict: Dictionnaire avec 3 listes de 12 valeurs (une par mois)
        """
        # Initialisation : 12 mois pour chaque catégorie
        stats = {
            'enfants': [0] * 12,
            'jeunes': [0] * 12,
            'adultes': [0] * 12
        }
        
        conn = self.db_manager.connect()
        if not conn:
            return stats
            
        try:
            with conn.cursor(DictCursor) as cursor:
                # JOIN avec la table patients pour calculer l'âge
                sql = """
                    SELECT 
                        MONTH(v.date_visite) as mois,
                        SUM(CASE WHEN TIMESTAMPDIFF(YEAR, p.naissance, CURDATE()) < 18 THEN 1 ELSE 0 END) as enfants,
                        SUM(CASE WHEN TIMESTAMPDIFF(YEAR, p.naissance, CURDATE()) BETWEEN 18 AND 45 THEN 1 ELSE 0 END) as jeunes,
                        SUM(CASE WHEN TIMESTAMPDIFF(YEAR, p.naissance, CURDATE()) > 45 THEN 1 ELSE 0 END) as adultes
                    FROM visite v
                    JOIN patients p ON v.code_patient = p.code_patient
                    WHERE v.code_session = %s
                    GROUP BY MONTH(v.date_visite)
                    ORDER BY mois
                """
                cursor.execute(sql, (code_session,))
                rows = cursor.fetchall()
                
                # Remplit les listes (index 0 = Janvier, index 11 = Décembre)
                for row in rows:
                    m_idx = row['mois'] - 1
                    stats['enfants'][m_idx] = int(row['enfants'] or 0)
                    stats['jeunes'][m_idx] = int(row['jeunes'] or 0)
                    stats['adultes'][m_idx] = int(row['adultes'] or 0)
                
                return stats
        finally:
            conn.close()
    
    # ==================== DÉTAILS COMPLETS ====================
    
    def get_details_complets_visite(self, code_visite: str):
        """
        Récupère toutes les activités liées à une visite via la table acte_medical
        (consultations, examens, chirurgies, prescriptions, lunettes)
        
        Args:
            code_visite (str): Code de la visite
            
        Returns:
            dict: Dictionnaire avec toutes les activités et leurs actes médicaux
        """
        details = {
            'consultations': [],
            'examens': [],
            'chirurgies': [],
            'prescriptions': [],
            'lunettes': []
        }
        
        conn = self.db_manager.connect()
        if not conn:
            return details
            
        try:
            with conn.cursor(DictCursor) as cursor:
                # 1. Consultations (directement liées à la visite)
                cursor.execute(
                    "SELECT diagnostique, resultat_consultation FROM consultation WHERE code_visite = %s",
                    (code_visite,)
                )
                details['consultations'] = cursor.fetchall()

                # 2. Examens (via acte_medical)
                cursor.execute("""
                    SELECT e.libelle_examen, e.resultat_examen, e.conclusion_medicale,
                           a.decision_medicale, a.choix_patient, a.statu_acte
                    FROM examen e
                    INNER JOIN acte_medical a ON e.code_acte = a.code_acte
                    WHERE a.code_visite_origine = %s OR a.code_visite_execution = %s
                """, (code_visite, code_visite))
                details['examens'] = cursor.fetchall()

                # 3. Chirurgies (via acte_medical)
                cursor.execute("""
                    SELECT c.libelle_chururgie, c.date_chururgie,
                           a.decision_medicale, a.choix_patient, a.statu_acte
                    FROM chururgie c
                    INNER JOIN acte_medical a ON c.code_acte = a.code_acte
                    WHERE a.code_visite_origine = %s OR a.code_visite_execution = %s
                """, (code_visite, code_visite))
                details['chirurgies'] = cursor.fetchall()

                # 4. Prescriptions (via acte_medical)
                cursor.execute("""
                    SELECT p.designation, p.quantite_prescript, p.prix_applique,
                           a.decision_medicale, a.choix_patient, a.statu_acte
                    FROM prescription_produit p
                    INNER JOIN acte_medical a ON p.code_acte = a.code_acte
                    WHERE a.code_visite_origine = %s OR a.code_visite_execution = %s
                """, (code_visite, code_visite))
                details['prescriptions'] = cursor.fetchall()

                # 5. Commandes de lunettes (via acte_medical)
                cursor.execute("""
                    SELECT l.numero_cadre, l.numero_verre, l.prix, l.statut,
                           a.decision_medicale, a.choix_patient, a.statu_acte
                    FROM commandeslunettes l
                    INNER JOIN acte_medical a ON l.code_acte = a.code_acte
                    WHERE a.code_visite_origine = %s OR a.code_visite_execution = %s
                """, (code_visite, code_visite))
                details['lunettes'] = cursor.fetchall()

            return details
        except pymysql.MySQLError as e:
            print(f"Erreur lors de la récupération des détails : {e}")
            return details
        finally:
            conn.close()
    
    # ==================== SUIVI DE PROGRESSION ====================
    
    def get_all_visites_suivi(self, code_session: str):
        """
        Récupère toutes les visites d'une session pour le tableau de progression
        
        Args:
            code_session (str): Code de la session
            
        Returns:
            list: Liste d'objets Visite triés par date décroissante
        """
        visites_objets = []
        conn = self.db_manager.connect()
        if not conn:
            return []
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = "SELECT * FROM visite WHERE code_session = %s ORDER BY date_visite DESC"
                cursor.execute(sql, (code_session,))
                rows = cursor.fetchall()
                
                for row in rows:
                    visite = Visite(
                        code_visite=row["code_visite"],
                        code_patient=row["code_patient"],
                        code_session=row["code_session"],
                        type_visite=row["type_visite"],
                        statut_visite=row["statut_visite"],
                        statut_patient=row["statut_patient"],
                        urgent=row["urgent"],
                        date_visite=row["date_visite"],
                        date_debut_consultation=row.get("date_debut_consultation")
                    )
                    visites_objets.append(visite)
                
                return visites_objets
        except Exception as e:
            print(f"Erreur : {e}")
            return []
        finally:
            conn.close()
    
    def update_progression_visite(self, code_visite, nouveau_statut_patient):
        """
        Met à jour le statut de progression d'un patient dans son parcours
        Si le statut devient "Libéré", la visite est marquée comme "terminée"
        
        Args:
            code_visite (str): Code de la visite
            nouveau_statut_patient (str): Nouveau statut (ex: "En consultation")
            
        Returns:
            bool: True si succès, False sinon
        """
        conn = self.db_manager.connect()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Met à jour le statut patient
                sql = "UPDATE visite SET statut_patient = %s WHERE code_visite = %s"
                cursor.execute(sql, (nouveau_statut_patient, code_visite))
                
                # Si le patient est libéré, on termine la visite
                if nouveau_statut_patient.lower() == "libéré":
                    sql_fin = "UPDATE visite SET statut_visite = 'terminée' WHERE code_visite = %s"
                    cursor.execute(sql_fin, (code_visite,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Erreur de mise à jour : {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ==================== GESTION DES PRIORITÉS ====================
    
    def getAllVisitesPrioritaires(self, code_session: str):
        """
        Récupère toutes les visites avec les urgences en priorité
        Inclut les informations du patient (nom, prénom, téléphone)
        
        Args:
            code_session (str): Code de la session
            
        Returns:
            list: Liste d'objets Visite avec attributs patient ajoutés
        """
        liste_visites = []
        conn = self.db_manager.connect()
        if not conn:
            return []

        try:
            with conn.cursor(DictCursor) as cursor:
                # Tri : urgences d'abord, puis par date décroissante
                sql = """
                    SELECT 
                        v.*, 
                        p.nom, 
                        p.prenom, 
                        p.telephone
                    FROM visite v
                    INNER JOIN patients p ON v.code_patient = p.code_patient
                    WHERE v.code_session = %s
                    ORDER BY v.urgent DESC, v.date_visite DESC
                """
                cursor.execute(sql, (code_session,))
                rows = cursor.fetchall()

                for row in rows:
                    visite = Visite(
                        code_visite=row["code_visite"],
                        code_patient=row["code_patient"],
                        code_session=row["code_session"],
                        type_visite=row["type_visite"],
                        statut_visite=row["statut_visite"],
                        statut_patient=row["statut_patient"],
                        urgent=row["urgent"],
                        date_visite=row["date_visite"],
                        date_debut_consultation=row.get("date_debut_consultation")
                    )
                    
                    # Ajout dynamique des attributs patient
                    visite.nom_patient = row["nom"]
                    visite.prenom_patient = row["prenom"]
                    visite.tel_patient = row["telephone"]

                    liste_visites.append(visite)
                    
                return liste_visites
        except pymysql.MySQLError as e:
            print(f"Erreur lors de la récupération : {e}")
            return []
        finally:
            conn.close()
    
    def searchVisitesByKeyword(self, code_session: str, mot_cle: str):
        """
        Recherche des visites par nom, prénom ou code visite
        Maintient les urgences en priorité
        
        Args:
            code_session (str): Code de la session
            mot_cle (str): Mot-clé de recherche
            
        Returns:
            list: Liste d'objets Visite correspondants
        """
        liste_resultats = []
        conn = self.db_manager.connect()
        if not conn:
            return []

        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                    SELECT 
                        v.*, 
                        p.nom, 
                        p.prenom, 
                        p.telephone
                    FROM visite v
                    INNER JOIN patients p ON v.code_patient = p.code_patient
                    WHERE v.code_session = %s 
                    AND (p.nom LIKE %s OR p.prenom LIKE %s OR v.code_visite LIKE %s)
                    ORDER BY v.urgent DESC, v.date_visite DESC
                """
                search_pattern = f"%{mot_cle}%"
                cursor.execute(sql, (code_session, search_pattern, search_pattern, search_pattern))
                rows = cursor.fetchall()

                for row in rows:
                    visite = Visite(
                        code_visite=row["code_visite"],
                        code_patient=row["code_patient"],
                        code_session=row["code_session"],
                        type_visite=row["type_visite"],
                        statut_visite=row["statut_visite"],
                        statut_patient=row["statut_patient"],
                        urgent=row["urgent"],
                        date_visite=row["date_visite"],
                        date_debut_consultation=row.get("date_debut_consultation")
                    )
                    visite.nom_patient = row["nom"]
                    visite.prenom_patient = row["prenom"]
                    visite.tel_patient = row["telephone"]

                    liste_resultats.append(visite)
                    
                return liste_resultats
        except pymysql.MySQLError as e:
            print(f"Erreur lors de la recherche : {e}")
            return []
        finally:
            conn.close()
    
    # ==================== CALCULS DE DURÉE ====================
    
    def calculer_duree_actuelle(self, code_visite):
        conn = self.db_manager.connect()
        if not conn:
            return "Service inconnu : 0h 0min"
        
        try:
            with conn.cursor(DictCursor) as cursor:
                # ABS(TIMESTAMPDIFF...) évite les chiffres négatifs si l'heure serveur 
                # et l'heure de l'appli sont légèrement décalées
                sql = """
                    SELECT 
                        IFNULL(statut_patient, 'Accueil') as service, 
                        ABS(TIMESTAMPDIFF(MINUTE, date_visite, NOW())) as duree_minutes
                    FROM visite 
                    WHERE code_visite = %s
                """
                cursor.execute(sql, (code_visite,))
                row = cursor.fetchone()
                
                if row:
                    # Nettoyage du nom du service (évite "service None")
                    service = row['service'] if row['service'] else "Accueil"
                    
                    # Calcul propre
                    total_min = int(row['duree_minutes'] or 0)
                    heures = total_min // 60
                    minutes = total_min % 60
                    
                    return f"{service} : {heures}h {minutes}min"
                
                return "Non trouvé : 0h 0min"
        finally:
            conn.close()
    
    def get_duree_totale_visite(self, code_visite):
        """
        Calcule la durée totale d'une visite terminée
        
        Args:
            code_visite (str): Code de la visite
            
        Returns:
            str: Durée en minutes ou message si en cours
        """
        conn = self.db_manager.connect()
        if not conn:
            return "Erreur de connexion"
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                    SELECT TIMESTAMPDIFF(MINUTE, date_visite, NOW()) as duree
                    FROM visite 
                    WHERE code_visite = %s AND statut_visite = 'terminée'
                """
                cursor.execute(sql, (code_visite,))
                row = cursor.fetchone()
                return f"{row['duree']} min" if row else "Visite en cours..."
        finally:
            conn.close()
    
    # ==================== ALERTES & ANALYSES ====================
    
    def verifier_alerte_statut_patient(self, code_visite, limite_alerte=20):
        """
        Vérifie si un patient dépasse le temps d'attente acceptable
        
        Args:
            code_visite (str): Code de la visite
            limite_alerte (int): Temps limite en minutes (défaut: 20)
            
        Returns:
            tuple: (alerte_active, temps_attente, statut_actuel)
        """
        conn = self.db_manager.connect()
        if not conn:
            return False, 0, None
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                    SELECT statut_patient, TIMESTAMPDIFF(MINUTE, date_visite, NOW()) as temps_attente
                    FROM visite 
                    WHERE code_visite = %s
                """
                cursor.execute(sql, (code_visite,))
                row = cursor.fetchone()
                
                if row:
                    attente = row['temps_attente']
                    statut = row['statut_patient']
                    
                    # Alerte si le patient est en attente trop longtemps
                    if "attente" in statut.lower() and attente > limite_alerte:
                        return True, attente, statut
                
                return False, 0, None
        finally:
            conn.close()

    def verifier_alertes_batch(self, codes_visites: list, limite_alerte=20):
        """
        Vérifie en une seule requête (batch) si plusieurs patients dépassent 
        le temps d'attente acceptable.
        
        Args:
            codes_visites (list): Liste des codes visite
            limite_alerte (int): Temps limite en minutes (défaut: 20)
            
        Returns:
            list: Liste des alertes actives [{'code_visite': ..., 'temps_attente': ..., 'statut': ...}]
        """
        if not codes_visites:
            return []
            
        conn = self.db_manager.connect()
        if not conn:
            return []
        
        try:
            with conn.cursor(DictCursor) as cursor:
                format_strings = ','.join(['%s'] * len(codes_visites))
                sql = f"""
                    SELECT code_visite, statut_patient, TIMESTAMPDIFF(MINUTE, date_visite, NOW()) as temps_attente
                    FROM visite 
                    WHERE code_visite IN ({format_strings})
                """
                cursor.execute(sql, tuple(codes_visites))
                rows = cursor.fetchall()
                
                alertes = []
                for row in rows:
                    attente = row['temps_attente']
                    statut = row['statut_patient']
                    
                    if statut and "attente" in statut.lower() and attente > limite_alerte:
                        alertes.append({
                            'code_visite': row['code_visite'],
                            'temps_attente': attente,
                            'statut': statut
                        })
                return alertes
        except Exception as e:
            print(f"Erreur verifier_alertes_batch: {e}")
            return []
        finally:
            conn.close()
    
    def get_analyse_performance_soiree(self, code_session: str):
        """
        Analyse la performance globale d'une session
        Calcule la durée moyenne totale et par statut
        
        Args:
            code_session (str): Code de la session
            
        Returns:
            dict: Statistiques de performance
        """
        conn = self.db_manager.connect()
        stats = {'moyenne_globale': 0, 'details_par_statut': []}
        if not conn:
            return stats
        
        try:
            with conn.cursor(DictCursor) as cursor:
                # 1. Durée moyenne globale pour les visites terminées
                sql_totale = """
                    SELECT AVG(TIMESTAMPDIFF(MINUTE, date_visite, NOW())) as moyenne_totale
                    FROM visite 
                    WHERE code_session = %s AND statut_visite = 'terminée'
                """
                cursor.execute(sql_totale, (code_session,))
                res_total = cursor.fetchone()
                stats['moyenne_globale'] = round(res_total['moyenne_totale'] or 0, 1)

                # 2. Nombre de visites par statut patient (clés alignées avec StatutBar)
                sql_details = """
                    SELECT 
                        statut_patient  AS statut,
                        COUNT(*)        AS nombre
                    FROM visite 
                    WHERE code_session = %s
                    GROUP BY statut_patient
                    ORDER BY nombre DESC
                """
                cursor.execute(sql_details, (code_session,))
                stats['details_par_statut'] = cursor.fetchall()
                
            return stats
        except pymysql.MySQLError as e:
            print(f"Erreur get_analyse_performance_soiree: {e}")
            return stats
        finally:
            conn.close()
    
    def get_visites_actives_avec_duree(self, code_session: str) -> list:
        """
        Retourne toutes les visites actives (non terminées) de la session
        avec le nom du patient, le statut courant et deux durées :
          - duree_totale_minutes : depuis la création de la visite
          - duree_service_minutes : depuis l'entrée dans le service courant
                                     (date_entre du dernier acte_visite actif)

        Returns:
            list[dict]: [{code_visite, nom, prenom, type_visite,
                          statut_patient, urgent,
                          duree_totale_minutes, duree_service_minutes}]
        """
        conn = self.db_manager.connect()
        if not conn:
            return []
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                    SELECT
                        v.code_visite,
                        v.type_visite,
                        v.statut_patient,
                        v.urgent,
                        p.nom,
                        p.prenom,
                        ABS(TIMESTAMPDIFF(MINUTE, v.date_visite, NOW())) AS duree_totale_minutes,
                        ABS(TIMESTAMPDIFF(MINUTE, av_last.derniere_entree, NOW())) AS duree_service_minutes
                    FROM visite v
                    INNER JOIN patients p ON v.code_patient = p.code_patient
                    LEFT JOIN (
                        SELECT code_visite, MAX(date_entre) AS derniere_entree
                        FROM acte_visite
                        WHERE date_sortie IS NULL
                          AND date_entre IS NOT NULL
                        GROUP BY code_visite
                    ) av_last ON av_last.code_visite = v.code_visite
                    WHERE v.code_session = %s
                      AND LOWER(COALESCE(v.statut_visite, '')) != 'terminée'
                      AND v.statut_patient NOT IN (
                            'Libéré', 'Liberé', 'libéré',
                            'Examen terminé', 'Examen termine'
                      )
                    ORDER BY v.urgent DESC, v.date_visite ASC
                """
                cursor.execute(sql, (code_session,))
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"Erreur get_visites_actives_avec_duree: {e}")
            return []
        finally:
            conn.close()

    def get_analyse_flux_hebdomadaire(self):
        """
        Analyse le flux de visites par jour de la semaine
        Permet d'identifier les jours les plus chargés
        
        Returns:
            list: Liste de dictionnaires {jour, total}
        """
        conn = self.db_manager.connect()
        if not conn:
            return []
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                    SELECT 
                        DAYNAME(date_visite)    AS jour,
                        COUNT(*)                AS total
                    FROM visite
                    GROUP BY DAYOFWEEK(date_visite), DAYNAME(date_visite)
                    ORDER BY DAYOFWEEK(date_visite)
                """
                cursor.execute(sql)
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"Erreur get_analyse_flux_hebdomadaire: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== GESTION DES SESSIONS ====================
    
    def get_code_session_active(self):
        """
        Récupère le code de la session actuellement active
        
        Returns:
            str: Code session ou None si aucune session active
        """
        conn = self.db_manager.connect()
        if not conn:
            return None
            
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = "SELECT code_session FROM annee WHERE statut = %s LIMIT 1"
                cursor.execute(sql, ("En_cours",))
                resultat = cursor.fetchone()
                
                if resultat:
                    return resultat['code_session']
                else:
                    print("Info : Aucune session active trouvée")
                    return None
        except Exception as e:
            print(f"Erreur lors de la récupération de la session active : {e}")
            return None
        finally:
            conn.close()
    
    def get_statistiques_performance_session(self, code_session: str) -> dict:
        default = {
            'duree_moyenne': 0, 'attente_max': 0, 'visites_actives': 0,
            'tendance': '+0%', 'efficacite': 0, 'satisfaction': 0
        }
        if not code_session:
            return default

        conn = self.db_manager.connect()
        if not conn:
            return default

        try:
            with conn.cursor(DictCursor) as cursor:

                # Durée moyenne visites terminées
                cursor.execute("""
                    SELECT COALESCE(AVG(TIMESTAMPDIFF(MINUTE, date_visite, NOW())), 0) AS valeur
                    FROM visite WHERE code_session = %s AND statut_visite = 'terminée'
                """, (code_session,))
                duree_moyenne = int(cursor.fetchone()['valeur'] or 0)

                # Attente max visites actives
                cursor.execute("""
                    SELECT COALESCE(MAX(TIMESTAMPDIFF(MINUTE, date_visite, NOW())), 0) AS valeur
                    FROM visite WHERE code_session = %s AND statut_visite != 'terminée'
                """, (code_session,))
                attente_max = int(cursor.fetchone()['valeur'] or 0)

                # Visites actives
                cursor.execute("""
                    SELECT COUNT(*) AS valeur FROM visite
                    WHERE code_session = %s AND statut_visite != 'terminée'
                """, (code_session,))
                visites_actives = int(cursor.fetchone()['valeur'] or 0)

                # Tendance vs session précédente
                cursor.execute("""
                    SELECT COUNT(*) AS valeur FROM visite WHERE code_session = %s
                """, (code_session,))
                total_actuel = int(cursor.fetchone()['valeur'] or 0)

                cursor.execute("""
                    SELECT code_session FROM annee
                    WHERE code_session != %s ORDER BY code_session DESC LIMIT 1
                """, (code_session,))
                row_prev = cursor.fetchone()
                tendance = "+0%"
                if row_prev:
                    cursor.execute("""
                        SELECT COUNT(*) AS valeur FROM visite WHERE code_session = %s
                    """, (row_prev['code_session'],))
                    total_prev = int(cursor.fetchone()['valeur'] or 0)
                    if total_prev > 0:
                        pct = round(((total_actuel - total_prev) / total_prev) * 100)
                        tendance = f"+{pct}%" if pct >= 0 else f"{pct}%"

                # Efficacité : % visites terminées en <= 90 min
                cursor.execute("""
                    SELECT COUNT(*) AS valeur FROM visite
                    WHERE code_session = %s AND statut_visite = 'terminée'
                """, (code_session,))
                total_terminees = int(cursor.fetchone()['valeur'] or 0)

                cursor.execute("""
                    SELECT COUNT(*) AS valeur FROM visite
                    WHERE code_session = %s AND statut_visite = 'terminée'
                    AND TIMESTAMPDIFF(MINUTE, date_visite, NOW()) <= 90
                """, (code_session,))
                dans_delai = int(cursor.fetchone()['valeur'] or 0)

                efficacite = round((dans_delai / total_terminees) * 100) if total_terminees > 0 else 0
                penalite = max(0, min(30, (attente_max - 60) // 2)) if attente_max > 60 else 0
                satisfaction = max(0, round(efficacite * 0.7 + (100 - penalite) * 0.3))

            return {
                'duree_moyenne':   duree_moyenne,
                'attente_max':     attente_max,
                'visites_actives': visites_actives,
                'tendance':        tendance,
                'efficacite':      efficacite,
                'satisfaction':    satisfaction
            }
        except pymysql.MySQLError as e:
            print(f"Erreur get_statistiques_performance_session: {e}")
            return default
        finally:
            conn.close()

    def get_nombre_visites_aujourdhui(self, code_session: str) -> int:
        """
        Récupère le nombre de visites créées aujourd'hui pour une session.
        
        Args:
            code_session (str): Code de la session
            
        Returns:
            int: Nombre de visites créées aujourd'hui
        """
        conn = self.db_manager.connect()
        if not conn:
            return 0
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                    SELECT COUNT(*) AS total
                    FROM visite
                    WHERE code_session = %s
                    AND DATE(date_visite) = CURDATE()
                """
                cursor.execute(sql, (code_session,))
                result = cursor.fetchone()
                return int(result['total'] or 0)
        except pymysql.MySQLError as e:
            print(f"Erreur get_nombre_visites_aujourdhui: {e}")
            return 0
        finally:
            conn.close()
    
    def get_nombre_visites_terminees(self, code_session: str) -> int:
        """
        Récupère le nombre total de visites terminées pour une session.
        
        Args:
            code_session (str): Code de la session
            
        Returns:
            int: Nombre de visites terminées
        """
        conn = self.db_manager.connect()
        if not conn:
            return 0
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                    SELECT COUNT(*) AS total
                    FROM visite
                    WHERE code_session = %s
                    AND statut_visite = 'terminée'
                """
                cursor.execute(sql, (code_session,))
                result = cursor.fetchone()
                return int(result['total'] or 0)
        except pymysql.MySQLError as e:
            print(f"Erreur get_nombre_visites_terminees: {e}")
            return 0
        finally:
            conn.close()
    
    def get_nombre_urgences(self, code_session: str) -> int:
        """
        Récupère le nombre de visites marquées comme urgentes pour une session.
        
        Args:
            code_session (str): Code de la session
            
        Returns:
            int: Nombre d'urgences
        """
        conn = self.db_manager.connect()
        if not conn:
            return 0
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                    SELECT COUNT(*) AS total
                    FROM visite
                    WHERE code_session = %s
                    AND urgent = 'Oui'
                """
                cursor.execute(sql, (code_session,))
                result = cursor.fetchone()
                return int(result['total'] or 0)
        except pymysql.MySQLError as e:
            print(f"Erreur get_nombre_urgences: {e}")
            return 0
        finally:
            conn.close()
    
    # ==================== GESTION CONSULTATION ====================
    
    def demarrer_consultation(self, code_visite: str) -> tuple:
        """
        Démarre la consultation pour une visite.
        - Renseigne date_debut_consultation
        - Change statut_patient à "En consultation"
        
        Args:
            code_visite (str): Code de la visite
            
        Returns:
            tuple: (bool, str) - (succès, message)
        """
        conn = self.db_manager.connect()
        if not conn:
            return False, "Erreur de connexion"
        
        try:
            with conn.cursor(DictCursor) as cursor:
                # Vérifier que la visite existe et est en attente consultation
                cursor.execute(
                    "SELECT statut_patient FROM visite WHERE code_visite = %s",
                    (code_visite,)
                )
                row = cursor.fetchone()
                if not row:
                    return False, "Visite introuvable"
                
                if row['statut_patient'] != "Attente consultation":
                    return False, f"La visite doit être en 'Attente consultation' (statut actuel: {row['statut_patient']})"
                
                # Mettre à jour
                sql = """
                    UPDATE visite 
                    SET date_debut_consultation = %s,
                        statut_patient = 'En consultation'
                    WHERE code_visite = %s
                """
                from datetime import datetime
                cursor.execute(sql, (datetime.now(), code_visite))
                conn.commit()
                return True, "Consultation démarrée avec succès"
        except pymysql.MySQLError as e:
            conn.rollback()
            return False, f"Erreur lors du démarrage: {e}"
        finally:
            conn.close()
    
    def get_durees_consultation(self, code_visite: str) -> dict:
        """
        Calcule les durées pour la consultation.
        - Durée attente = date_debut_consultation - date_visite
        - Durée consultation = date_creation_consultation - date_debut_consultation
        
        Args:
            code_visite (str): Code de la visite
            
        Returns:
            dict: {duree_attente_min, duree_consultation_min}
        """
        conn = self.db_manager.connect()
        if not conn:
            return {'duree_attente_min': None, 'duree_consultation_min': None}
        
        try:
            with conn.cursor(DictCursor) as cursor:
                sql = """
                    SELECT 
                        v.date_visite,
                        v.date_debut_consultation,
                        c.date_creation as date_creation_consultation
                    FROM visite v
                    LEFT JOIN consultation c ON c.code_visite = v.code_visite
                    WHERE v.code_visite = %s
                """
                cursor.execute(sql, (code_visite,))
                row = cursor.fetchone()
                
                if not row:
                    return {'duree_attente_min': None, 'duree_consultation_min': None}
                
                from datetime import datetime
                date_visite = row['date_visite']
                date_debut = row['date_debut_consultation']
                date_fin = row['date_creation_consultation']
                
                duree_attente = None
                duree_consultation = None
                
                # Durée d'attente
                if date_debut and date_visite:
                    delta = date_debut - date_visite
                    duree_attente = int(delta.total_seconds() / 60)
                elif date_visite:
                    # En cours d'attente
                    delta = datetime.now() - date_visite
                    duree_attente = int(delta.total_seconds() / 60)
                
                # Durée de consultation
                if date_fin and date_debut:
                    delta = date_fin - date_debut
                    duree_consultation = int(delta.total_seconds() / 60)
                elif date_debut:
                    # En cours de consultation
                    delta = datetime.now() - date_debut
                    duree_consultation = int(delta.total_seconds() / 60)
                
                return {
                    'duree_attente_min': duree_attente,
                    'duree_consultation_min': duree_consultation
                }
        except Exception as e:
            print(f"Erreur get_durees_consultation: {e}")
            return {'duree_attente_min': None, 'duree_consultation_min': None}
        finally:
            conn.close()

    def lister_sessions(self, limite: int = 50) -> list:
        """Retourne les codes de session depuis la table annee."""
        conn = self.db_manager.connect()
        if not conn:
            return []
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute(
                    "SELECT code_session FROM annee ORDER BY code_session DESC LIMIT %s",
                    (limite,)
                )
                return cursor.fetchall() or []
        except Exception as e:
            print(f"[VisiteDAO] Erreur lister_sessions: {e}")
            return []
        finally:
            conn.close()

    def lister_sessions_completes(self, limite: int = 50) -> list:
        """Retourne code_session, nom_session, date_debut, date_fin, statut depuis annee."""
        conn = self.db_manager.connect()
        if not conn:
            return []
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute(
                    "SELECT code_session, nom_session, date_debut, date_fin, statut "
                    "FROM annee ORDER BY code_session DESC LIMIT %s",
                    (limite,)
                )
                return cursor.fetchall() or []
        except Exception as e:
            print(f"[VisiteDAO] Erreur lister_sessions_completes: {e}")
            return []
        finally:
            conn.close()

    def get_session_from_visite(self, code_visite: str) -> str:
        """Retourne le code_session d'une visite par son code."""
        visite = self.reeVisite_ByCode_visite(code_visite)
        return visite.get_code_session() if visite else None

    def get_plage_session(self, code_session: str) -> dict | None:
        """Retourne nom_session, date_debut et date_fin pour une session donnée."""
        conn = self.db_manager.connect()
        if not conn:
            return None
        try:
            with conn.cursor(DictCursor) as cursor:
                cursor.execute(
                    "SELECT nom_session, date_debut, date_fin FROM annee WHERE code_session = %s LIMIT 1",
                    (code_session,)
                )
                return cursor.fetchone()
        except Exception as e:
            print(f"[Visitedao] Erreur get_plage_session: {e}")
            return None
        finally:
            conn.close()

    def _update_statut_visite_import(self, cursor, code_visite: str, statut: str) -> None:
        """
        UPDATE visite.statut_patient en mode import — reçoit curseur externe.
        Pas de gestion de connexion ni de commit.
        """
        cursor.execute(
            "UPDATE visite SET statut_patient = %s WHERE code_visite = %s",
            (statut, code_visite)
        )
