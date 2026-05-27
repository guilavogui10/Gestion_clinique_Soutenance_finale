import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
from core.connexion_db import DBConnection
from models.modeles_chirurgie import Chirurgie # Assurez-vous du nom du fichier
from datetime import datetime
DictCursor = pymysql.cursors.DictCursor
import calendar


class ChirurgieDAO:
    """
    Classe DAO pour la gestion des chururgies.
    Architecture MVC : accès aux données uniquement.
    """

    def __init__(self):
        self.db = DBConnection()

    # =========================================================================
    # METHODES CRUD
    # =========================================================================

    def ajouter(self, chururgie: Chirurgie) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            chururgie.code = self._generer_code(cursor)
            query = """
                INSERT INTO chururgie (
                    code, libelle_chururgie, frais_chururgie,
                    statut_facture, date_chururgie,
                    code_session, code_personnel, code_acte, compte_rendu_operatoire
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                chururgie.code,
                chururgie.libelle_chururgie,
                chururgie.frais_chururgie,
                chururgie.statut_facture,
                chururgie.date_chururgie,
                chururgie.code_session,
                chururgie.code_personnel,
                chururgie.code_acte,
                chururgie.compte_rendu_operatoire or ""
            ))
            # Mise à jour du statut_patient dans visite
            nouveau_statut, code_visite = self._determiner_statut_et_visite(cursor, chururgie.code_acte)
            if code_visite:
                cursor.execute(
                    "UPDATE visite SET statut_patient=%s WHERE code_visite=%s",
                    (nouveau_statut, code_visite)
                )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur ajouter: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def modifier(self, chururgie: Chirurgie) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            query = """
                UPDATE chururgie SET
                    libelle_chururgie=%s, frais_chururgie=%s,
                    statut_facture=%s, date_chururgie=%s,
                    code_session=%s, code_personnel=%s,
                    code_acte=%s, compte_rendu_operatoire=%s
                WHERE code=%s
            """
            cursor.execute(query, (
                chururgie.libelle_chururgie,
                chururgie.frais_chururgie,
                chururgie.statut_facture,
                chururgie.date_chururgie,
                chururgie.code_session,
                chururgie.code_personnel,
                chururgie.code_acte,
                chururgie.compte_rendu_operatoire,
                chururgie.code
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur modifier: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    def supprimer(self, code: str) -> bool:
        conn = self.db.connect()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chururgie WHERE code=%s", (code,))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur supprimer: {e}")
            conn.rollback()
            return False
        finally:
            self.db.close()

    # =========================================================================
    # METHODES DE RECUPERATION
    # =========================================================================

    def obtenir_par_code(self, code: str):
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            query = """
                SELECT ch.*, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM chururgie ch
                LEFT JOIN acte_medical am ON ch.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE ch.code=%s
            """
            cursor.execute(query, (code,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur obtenir_par_code: {e}")
            return None
        finally:
            self.db.close()

    def lister_par_session(self, code_session: str) -> list:
        conn = self.db.connect()
        if not conn: return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT ch.*, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM chururgie ch
                LEFT JOIN acte_medical am ON ch.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE ch.code_session=%s 
                ORDER BY ch.date_chururgie DESC
            """
            cursor.execute(query, (code_session,))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur lister_par_session: {e}")
            return []
        finally:
            self.db.close()

    def rechercher_par_critere(self, critere: str, code_session: str) -> list:
        conn = self.db.connect()
        if not conn: return []
        try:
            cursor = conn.cursor()
            critere_like = f"%{critere}%"
            query = """
                SELECT ch.*, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM chururgie ch
                LEFT JOIN acte_medical am ON ch.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE ch.code_session=%s
                AND (
                    ch.code LIKE %s OR 
                    ch.libelle_chururgie LIKE %s OR 
                    p.nom LIKE %s OR 
                    p.prenom LIKE %s
                )
                ORDER BY ch.date_chururgie DESC
            """
            cursor.execute(query, (code_session, critere_like, critere_like, critere_like, critere_like))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur rechercher_par_critere: {e}")
            return []
        finally:
            self.db.close()

    def rechercher_par_libelle(self, code_session: str, libelle: str) -> list:
        """Recherche les chirurgies par libellé (LIKE) dans une session."""
        if not code_session:
            return []
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT ch.*, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM chururgie ch
                LEFT JOIN acte_medical am ON ch.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                WHERE ch.code_session = %s
                  AND ch.libelle_chururgie LIKE %s
                ORDER BY ch.date_chururgie DESC
            """
            cursor.execute(query, (code_session, f"%{libelle}%"))
            rows = cursor.fetchall()
            return [self._row_to_object(row) for row in rows]
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur rechercher_par_libelle: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # MÉTHODES STATISTIQUES (CARDS)
    # =========================================================================

    def nombre_chururgies_aujourd_hui(self, code_session: str) -> int:
        """Card 'Chirurgies du Jour' : Compte les chirurgies créées aujourd'hui."""
        conn = self.db.connect()
        if not conn: return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM chururgie
                WHERE code_session = %s
                  AND DATE(date_chururgie) = CURDATE()
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur nombre_chururgies_aujourd_hui: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_total_par_session(self, code_session: str) -> int:
        """Card 'Total Session' : Compte toutes les chirurgies de la session."""
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM chururgie
                WHERE code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur nombre_total_par_session: {e}")
            return 0
        finally:
            self.db.close()

    def nombre_chururgies_en_attente(self, code_session: str) -> int:
        """
        Card 'Chirurgies en Attente' :
        Compte les visites avec statut_patient IN ('Attente chirurgie','En chirurgie')
        et sans encore d'enregistrement dans la table chururgie.
        """
        conn = self.db.connect()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT v.code_visite) AS total
                FROM visite v
                INNER JOIN acte_visite av   ON av.code_visite = v.code_visite
                INNER JOIN acte_medical am  ON am.code_acte = av.code_acte
                                           AND am.type_acte = 'chirurgie'
                WHERE v.code_session = %s
                AND v.statut_patient IN ('Attente chirurgie', 'En chirurgie')
                AND NOT EXISTS (
                    SELECT 1 FROM chururgie ch WHERE ch.code_acte = am.code_acte
                )
            """, (code_session,))
            result = cursor.fetchone()
            return result['total'] if result else 0
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur nombre_chururgies_en_attente: {e}")
            return 0
        finally:
            self.db.close()

    def montant_total_chirurgie_aujourdhui(self, code_session: str) -> float:
        """Card 'Montant du Jour' : Montant total des chirurgies d'aujourd'hui."""
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(frais_chururgie) AS total
                FROM chururgie
                WHERE code_session = %s
                  AND DATE(date_chururgie) = CURDATE()
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur montant_total_chirurgie_aujourdhui: {e}")
            return 0.0
        finally:
            self.db.close()

    def montant_total_chirurgie_par_session(self, code_session: str) -> float:
        """Card 'Montant Session' : Montant total de toutes les chirurgies de la session."""
        conn = self.db.connect()
        if not conn:
            return 0.0
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(frais_chururgie) AS total
                FROM chururgie
                WHERE code_session = %s
            """, (code_session,))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur montant_total_chirurgie_par_session: {e}")
            return 0.0
        finally:
            self.db.close()

    def revenu_total(self, code_session: str) -> float:
        """Alias pour montant_total_chirurgie_par_session (compatibilité)."""
        return self.montant_total_chirurgie_par_session(code_session)

    # =========================================================================
    # MÉTHODES PATIENTS & PERSONNEL
    # =========================================================================

    def patients_en_attente_chururgie(self, code_session: str) -> list:
        """Retourne la liste des patients en attente ou en cours de chirurgie."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT DISTINCT
                    v.code_visite, v.date_visite, v.type_visite, v.urgent, v.statut_patient,
                    c.code AS code_consultation, c.date_consultation, c.diagnostique,
                    am.code_acte AS code_acte,
                    p.code_patient, p.nom, p.prenom, p.telephone
                FROM visite v
                INNER JOIN patients p       ON v.code_patient = p.code_patient
                INNER JOIN acte_visite av   ON av.code_visite = v.code_visite
                INNER JOIN acte_medical am  ON am.code_acte   = av.code_acte
                                           AND am.type_acte   = 'chirurgie'
                LEFT JOIN  consultation c   ON c.code          = am.code_consultation
                WHERE v.code_session = %s
                AND v.statut_patient IN ('Attente chirurgie', 'En chirurgie')
                AND NOT EXISTS (
                    SELECT 1 FROM chururgie ch WHERE ch.code_acte = am.code_acte
                )
                ORDER BY v.urgent DESC, v.date_visite ASC
            """
            cursor.execute(query, (code_session,))
            rows = cursor.fetchall()
            print(f"[ChirurgieDAO] patients_en_attente_chururgie({code_session}): {len(rows)} résultat(s)")
            return rows
        except Exception as e:
            print(f"[ChirurgieDAO] ERREUR patients_en_attente_chururgie: {e}")
            import traceback; traceback.print_exc()
            return []
        finally:
            self.db.close()

    def chururgies_par_personnel(self, code_session: str) -> list:
        """Nombre de chirurgies groupées par personnel (statistiques)."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    per.nom, 
                    per.prenom, 
                    COUNT(*) AS nombre,
                    SUM(c.frais_chururgie) AS total_frais
                FROM chururgie c
                INNER JOIN personnel per ON c.code_personnel = per.code
                WHERE c.code_session = %s
                GROUP BY per.code, per.nom, per.prenom
                ORDER BY nombre DESC
            """, (code_session,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur chururgies_par_personnel: {e}")
            return []
        finally:
            self.db.close()

    def lister_personnel(self) -> list:
        """Retourne la liste de tout le personnel médical."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT code, nom, prenom, fonction
                FROM personnel
                ORDER BY nom ASC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur lister_personnel: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # MÉTHODES PRIVÉES
    # =========================================================================

    def _generer_code(self, cursor) -> str:
        """Génère un code unique (ex: CHR001)."""
        try:
            cursor.execute("SELECT code FROM chururgie ORDER BY code DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                last_code = row['code']
                last_num = int(last_code[3:])
                return f"CHR{last_num + 1:03d}"
            else:
                return "CHR001"
        except Exception:
            return "CHR" + datetime.now().strftime("%H%M%S")

    def _row_to_object(self, row) -> Chirurgie:
        """Convertit une ligne DB en objet Chirurgie."""
        obj = Chirurgie(
            code                  = row['code'],
            libelle_chururgie     = row['libelle_chururgie'],
            frais_chururgie       = row['frais_chururgie'],
            statut_facture        = row['statut_facture'],
            date_chururgie        = row['date_chururgie'],
            code_session          = row['code_session'],
            code_personnel        = row['code_personnel'],
            code_acte             = row['code_acte'],
            compte_rendu_operatoire = row.get('compte_rendu_operatoire')
        )
        obj.patient_nom    = row.get('patient_nom', "")
        obj.patient_prenom = row.get('patient_prenom', "")
        return obj

    def _determiner_statut_et_visite(self, cursor, code_acte: str) -> tuple:
        """Récupère le code_visite d'exécution via acte_visite (role='execution').
        Retourne (prochain_statut, code_visite).
        
        IMPORTANT : On met à jour UNIQUEMENT la visite d'exécution (role='execution'),
        PAS la visite d'origine (role='origine') pour éviter la duplication dans la file d'attente.
        """
        try:
            # Récupérer le code_visite d'exécution depuis acte_visite avec role='execution'
            cursor.execute(
                "SELECT code_visite FROM acte_visite WHERE code_acte=%s AND role_visite='execution' LIMIT 1",
                (code_acte,)
            )
            row = cursor.fetchone()
            if not row:
                # Si pas de visite d'exécution, récupérer depuis la consultation (cas acte "maintenant")
                cursor.execute(
                    "SELECT code_consultation FROM acte_medical WHERE code_acte=%s", (code_acte,)
                )
                row_cons = cursor.fetchone()
                if not row_cons:
                    return "Attente payement", None
                code_consultation = row_cons.get('code_consultation') if isinstance(row_cons, dict) else row_cons[0]
                if not code_consultation:
                    return "Attente payement", None
                cursor.execute(
                    "SELECT code_visite, prescription_produit FROM consultation WHERE code=%s",
                    (code_consultation,)
                )
                row_visite = cursor.fetchone()
                if not row_visite:
                    return "Attente payement", None
                code_visite  = row_visite.get('code_visite')  if isinstance(row_visite, dict) else row_visite[0]
                prescription = row_visite.get('prescription_produit') if isinstance(row_visite, dict) else row_visite[1]
                statut = "Attente pharmacie" if prescription == "Oui" else "Attente payement"
                return statut, code_visite
            
            # Visite d'exécution trouvée
            code_visite = row.get('code_visite') if isinstance(row, dict) else row[0]
            # Vérifier si prescription
            cursor.execute(
                "SELECT code_consultation FROM acte_medical WHERE code_acte=%s", (code_acte,)
            )
            row_cons = cursor.fetchone()
            if row_cons:
                code_consultation = row_cons.get('code_consultation') if isinstance(row_cons, dict) else row_cons[0]
                if code_consultation:
                    cursor.execute(
                        "SELECT prescription_produit FROM consultation WHERE code=%s",
                        (code_consultation,)
                    )
                    row_presc = cursor.fetchone()
                    if row_presc:
                        prescription = row_presc.get('prescription_produit') if isinstance(row_presc, dict) else row_presc[0]
                        statut = "Attente pharmacie" if prescription == "Oui" else "Attente payement"
                        return statut, code_visite
            
            return "Attente payement", code_visite
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur _determiner_statut_et_visite: {e}")
            return "Attente payement", None

    # =========================================================================
    # MÉTHODES UTILITAIRES STATISTIQUES (HELPERS)
    # =========================================================================

    @staticmethod
    def _stats_mensuels_int() -> dict:
        """Retourne un dictionnaire de mois initialisé à 0 (entiers)."""
        return {
            'Jan': 0, 'Fév': 0, 'Mar': 0, 'Avr': 0, 'Mai': 0, 'Juin': 0,
            'Juil': 0, 'Août': 0, 'Sep': 0, 'Oct': 0, 'Nov': 0, 'Déc': 0
        }

    @staticmethod
    def _stats_mensuels_float() -> dict:
        """Retourne un dictionnaire de mois initialisé à 0.0 (flottants)."""
        return {
            'Jan': 0.0, 'Fév': 0.0, 'Mar': 0.0, 'Avr': 0.0, 'Mai': 0.0, 'Juin': 0.0,
            'Juil': 0.0, 'Août': 0.0, 'Sep': 0.0, 'Oct': 0.0, 'Nov': 0.0, 'Déc': 0.0
        }

    @staticmethod
    def _mois_mapping() -> dict:
        """Mapping numéro de mois -> étiquette abrégée."""
        return {
            1: 'Jan', 2: 'Fév', 3: 'Mar', 4: 'Avr', 5: 'Mai', 6: 'Juin',
            7: 'Juil', 8: 'Août', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Déc'
        }

    @staticmethod
    def _jours_a_considerer_pour_moyenne(annee: int, mois: int, today) -> int:
        """
        Règle métier pour le calcul des moyennes:
        - Mois courant: du 1er jusqu'à aujourd'hui (inclus)
        - Mois passés/futurs: nombre total de jours du mois
        """
        if annee == today.year and mois == today.month:
            return today.day
        return calendar.monthrange(annee, mois)[1]
    
    # =========================================================================
    # MÉTHODES COMPLÈTES & DÉTAILS
    # =========================================================================

    def chururgie_complete(self, code_chururgie: str):
        """Retourne une chirurgie avec infos patient et personnel (JOIN)."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    ch.*,
                    p.nom           AS patient_nom,
                    p.prenom        AS patient_prenom,
                    p.telephone     AS patient_telephone,
                    p.adresse       AS patient_adresse,
                    p.naissance     AS patient_date_naissance,
                    per.nom         AS personnel_nom,
                    per.prenom      AS personnel_prenom,
                    per.fonction    AS personnel_fonction
                FROM chururgie ch
                LEFT JOIN acte_medical am ON ch.code_acte = am.code_acte
                LEFT JOIN consultation c  ON am.code_consultation = c.code
                LEFT JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN patients p      ON v.code_patient = p.code_patient
                LEFT JOIN personnel per   ON ch.code_personnel = per.code
                WHERE ch.code = %s
            """
            cursor.execute(query, (code_chururgie,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur chururgie_complete: {e}")
            return None
        finally:
            self.db.close()

    def obtenir_par_acte(self, code_acte: str):
        """Retourne la chirurgie liée à un acte medical."""
        conn = self.db.connect()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chururgie WHERE code_acte=%s", (code_acte,))
            row = cursor.fetchone()
            return self._row_to_object(row) if row else None
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur obtenir_par_acte: {e}")
            return None
        finally:
            self.db.close()

    def historique_patient(self, code_patient: str) -> list:
        """Retourne l'historique complet des chirurgies d'un patient."""
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            query = """
                SELECT ch.*, per.nom AS personnel_nom, per.prenom AS personnel_prenom
                FROM chururgie ch
                INNER JOIN acte_medical am ON ch.code_acte = am.code_acte
                INNER JOIN consultation c  ON am.code_consultation = c.code
                INNER JOIN visite v        ON c.code_visite = v.code_visite
                LEFT JOIN  personnel per   ON ch.code_personnel = per.code
                WHERE v.code_patient = %s
                ORDER BY ch.date_chururgie DESC
            """
            cursor.execute(query, (code_patient,))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur historique_patient: {e}")
            return []
        finally:
            self.db.close()

    def top_libelles(self, code_session: str, limite: int = 10) -> list:
        """Retourne les types de chirurgies les plus fréquents."""
        conn = self.db.connect()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT libelle_chururgie, COUNT(*) AS nombre
                FROM chururgie
                WHERE code_session=%s AND libelle_chururgie IS NOT NULL
                GROUP BY libelle_chururgie
                ORDER BY nombre DESC LIMIT %s
            """, (code_session, limite))
            return cursor.fetchall()
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur top_libelles: {e}")
            return []
        finally:
            self.db.close()

    # =========================================================================
    # MÉTHODES STATISTIQUES & GRAPHES - NOMBRE PAR PÉRIODE
    # =========================================================================

    def nombre_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """
        Retourne le nombre de chirurgies par jour pour un mois donné.
        Les jours sans activité sont inclus avec 0.
        - Si annee/mois non fournis: mois courant.
        - Pour le mois courant: jours 1..aujourd'hui.
        - Pour un autre mois: jours 1..fin du mois.
        """
        today = datetime.now().date()
        annee = annee or today.year
        mois = mois or today.month

        nb_jours_mois = calendar.monthrange(annee, mois)[1]
        dernier_jour = today.day if (annee == today.year and mois == today.month) else nb_jours_mois
        stats = {f"{j:02d}": 0 for j in range(1, dernier_jour + 1)}

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DAY(date_chururgie) AS num_jour, COUNT(*) AS total
                FROM chururgie      
                WHERE code_session=%s
                  AND YEAR(date_chururgie)=%s
                  AND MONTH(date_chururgie)=%s
                GROUP BY DAY(date_chururgie)
            """, (code_session, annee, mois))
            for row in cursor.fetchall():
                j = int(row['num_jour'])
                if 1 <= j <= dernier_jour:
                    stats[f"{j:02d}"] = int(row['total']) if row['total'] else 0
            return stats
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur nombre_par_jour: {e}")
            return stats
        finally:
            self.db.close()

    def nombre_par_mois(self, code_session: str) -> dict:
        """
        Graphe 'Nombre de chirurgies par mois' :
        Retourne le nombre de chirurgies pour chaque mois de l'année.
        """
        stats = self._stats_mensuels_int()
        mois_mapping = self._mois_mapping()
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MONTH(date_chururgie) AS num_mois, COUNT(*) AS total
                FROM chururgie WHERE code_session=%s
                GROUP BY MONTH(date_chururgie)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = row['total']
            return stats
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur nombre_par_mois: {e}")
            return stats
        finally:
            self.db.close()
    # =========================================================================
    # MÉTHODES STATISTIQUES & GRAPHES - MONTANT PAR PÉRIODE
    # =========================================================================

    def montant_par_jour(self, code_session: str, annee: int = None, mois: int = None) -> dict:
        """
        Retourne le montant des chirurgies par jour pour un mois donné.
        Les jours sans activité sont inclus avec 0.
        - Si annee/mois non fournis: mois courant.
        - Pour le mois courant: jours 1..aujourd'hui.
        - Pour un autre mois: jours 1..fin du mois.
        """
        today = datetime.now().date()
        annee = annee or today.year
        mois = mois or today.month

        nb_jours_mois = calendar.monthrange(annee, mois)[1]
        dernier_jour = today.day if (annee == today.year and mois == today.month) else nb_jours_mois
        stats = {f"{j:02d}": 0.0 for j in range(1, dernier_jour + 1)}

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DAY(date_chururgie) AS num_jour, SUM(frais_chururgie) AS total
                FROM chururgie
                WHERE code_session=%s
                  AND YEAR(date_chururgie)=%s
                  AND MONTH(date_chururgie)=%s
                GROUP BY DAY(date_chururgie)
            """, (code_session, annee, mois))
            for row in cursor.fetchall():
                j = int(row['num_jour'])
                if 1 <= j <= dernier_jour:
                    stats[f"{j:02d}"] = float(row['total']) if row['total'] else 0.0
            return stats
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur montant_par_jour: {e}")
            return stats
        finally:
            self.db.close()

    def montant_par_mois(self, code_session: str) -> dict:
        """
        Graphe 'Montant des chirurgies par mois' :
        Retourne le montant total des chirurgies pour chaque mois.
        """
        stats = self._stats_mensuels_float()
        mois_mapping = self._mois_mapping()
        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MONTH(date_chururgie) AS num_mois, 
                       SUM(frais_chururgie) AS total
                FROM chururgie 
                WHERE code_session=%s
                GROUP BY MONTH(date_chururgie)
            """, (code_session,))
            for row in cursor.fetchall():
                m = row['num_mois']
                if m in mois_mapping:
                    stats[mois_mapping[m]] = float(row['total']) if row['total'] else 0.0
            return stats
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur montant_par_mois: {e}")
            return stats
        finally:
            self.db.close()
    # =========================================================================
    # MÉTHODES STATISTIQUES & GRAPHES - MOYENNES
    # =========================================================================

    def moyenne_montant_journalier_mois(self, code_session: str) -> dict:
        """
        Retourne la moyenne journalière des montants par mois (jours sans activité inclus).
        - Mois courant: division par le nombre de jours écoulés (1..aujourd'hui)
        - Mois passés: division par le nombre total de jours du mois
        """
        stats = self._stats_mensuels_float()
        mois_mapping = self._mois_mapping()
        today = datetime.now().date()

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT YEAR(date_chururgie) AS annee,
                       MONTH(date_chururgie) AS num_mois,
                       SUM(frais_chururgie) AS total_mois
                FROM chururgie
                WHERE code_session=%s
                GROUP BY YEAR(date_chururgie), MONTH(date_chururgie)
            """, (code_session,))

            for row in cursor.fetchall():
                num_mois = int(row['num_mois'])
                annee = int(row['annee'])
                if num_mois not in mois_mapping:
                    continue

                jours = self._jours_a_considerer_pour_moyenne(annee, num_mois, today)
                total_mois = float(row['total_mois']) if row['total_mois'] else 0.0
                stats[mois_mapping[num_mois]] = (total_mois / jours) if jours > 0 else 0.0

            return stats
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur moyenne_montant_journalier_mois: {e}")
            return stats
        finally:
            self.db.close()

    def revenu_moyen_par_mois(self, code_session: str) -> dict:
        """
        Alias pour moyenne_montant_journalier_mois (compatibilité).
        Moyenne journalière des montants de chirurgie par mois.
        """
        return self.moyenne_montant_journalier_mois(code_session)

    def moyenne_chirurgies_journalieres_mois(self, code_session: str) -> dict:
        """
        Retourne la moyenne journalière du nombre de chirurgies par mois
        (jours sans activité inclus).
        - Mois courant: division par le nombre de jours écoulés (1..aujourd'hui)
        - Mois passés: division par le nombre total de jours du mois
        """
        stats = self._stats_mensuels_float()
        mois_mapping = self._mois_mapping()
        today = datetime.now().date()

        conn = self.db.connect()
        if not conn:
            return stats
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT YEAR(date_chururgie) AS annee,
                       MONTH(date_chururgie) AS num_mois,
                       COUNT(*) AS total_mois
                FROM chururgie
                WHERE code_session=%s
                GROUP BY YEAR(date_chururgie), MONTH(date_chururgie)
            """, (code_session,))

            for row in cursor.fetchall():
                num_mois = int(row['num_mois'])
                annee = int(row['annee'])
                if num_mois not in mois_mapping:
                    continue

                jours = self._jours_a_considerer_pour_moyenne(annee, num_mois, today)
                total_mois = int(row['total_mois']) if row['total_mois'] else 0
                stats[mois_mapping[num_mois]] = (float(total_mois) / jours) if jours > 0 else 0.0

            return stats
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur moyenne_chirurgies_journalieres_mois: {e}")
            return stats
        finally:
            self.db.close()

    def moyenne_chirurgies_par_mois(self, code_session: str) -> dict:
        """
        Alias pour moyenne_chirurgies_journalieres_mois (compatibilité).
        Retourne la moyenne journalière du nombre de chirurgies par mois.
        """
        return self.moyenne_chirurgies_journalieres_mois(code_session)
    # =========================================================================
    # MÉTHODES DE RECHERCHE AVANCÉE & FILTRAGE
    # =========================================================================

    def rechercher_entre_dates(self, code_session: str, date_debut, date_fin) -> list:
        """
        Recherche les chirurgies entre deux dates (incluses).
        date_debut et date_fin : objet datetime.date ou str au format YYYY-MM-DD
        Retourne une liste d'objets Chirurgie.
        """
        if not code_session:
            return []
        
        # Convertir en string si nécessaire
        if hasattr(date_debut, 'strftime'):
            date_debut = date_debut.strftime('%Y-%m-%d')
        if hasattr(date_fin, 'strftime'):
            date_fin = date_fin.strftime('%Y-%m-%d')

        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT c.*, v.code_patient, p.nom AS patient_nom, p.prenom AS patient_prenom
                FROM chururgie c
                LEFT JOIN acte_medical am ON c.code_acte = am.code_acte
                LEFT JOIN consultation cons ON am.code_consultation = cons.code
                LEFT JOIN visite v ON cons.code_visite = v.code_visite
                INNER JOIN patients p ON v.code_patient = p.code_patient
                WHERE c.code_session=%s AND DATE(c.date_chururgie) BETWEEN %s AND %s
                ORDER BY c.date_chururgie DESC
            """
            cursor.execute(query, (code_session, date_debut, date_fin))
            result = cursor.fetchall()
            return [self._row_to_object(row) for row in result]
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur rechercher_entre_dates: {e}")
            return []
        finally:
            self.db.close()

    def chirurgies_par_patient_par_mois(self, code_session: str, code_patient: str = None) -> dict:
        """
        Retourne le nombre de chirurgies par mois pour chaque patient (ou un patient spécifique).
        Format : { "Jan": { "P001": 2, "P002": 1 }, "Fév": { ... }, ... }
        ou si code_patient est spécifié : { "Jan": 2, "Fév": 1, ... }
        """
        stats = self._stats_mensuels_int()
        mois_mapping = self._mois_mapping()
        
        conn = self.db.connect()
        if not conn:
            return stats

        try:
            cursor = conn.cursor(DictCursor)
            
            if code_patient:
                # Un patient spécifique
                query = """
                    SELECT MONTH(c.date_chururgie) AS num_mois, COUNT(*) AS total
                    FROM chururgie c
                    LEFT JOIN acte_medical am   ON c.code_acte = am.code_acte
                    LEFT JOIN consultation cons  ON am.code_consultation = cons.code
                    LEFT JOIN visite v           ON cons.code_visite = v.code_visite
                    WHERE c.code_session=%s AND v.code_patient=%s
                    GROUP BY MONTH(c.date_chururgie)
                """
                cursor.execute(query, (code_session, code_patient))
                for row in cursor.fetchall():
                    m = row['num_mois']
                    if m in mois_mapping:
                        stats[mois_mapping[m]] = row['total']
            else:
                # Tous les patients
                query = """
                    SELECT MONTH(c.date_chururgie) AS num_mois, 
                           v.code_patient,
                           COUNT(*) AS total
                    FROM chururgie c
                    LEFT JOIN acte_medical am   ON c.code_acte = am.code_acte
                    LEFT JOIN consultation cons  ON am.code_consultation = cons.code
                    LEFT JOIN visite v           ON cons.code_visite = v.code_visite
                    WHERE c.code_session=%s
                    GROUP BY MONTH(c.date_chururgie), v.code_patient
                """
                cursor.execute(query, (code_session,))
                
                # Réorganiser en dict { mois: { patient: count } }
                stats_by_patient = {}
                for row in cursor.fetchall():
                    m = row['num_mois']
                    if m in mois_mapping:
                        mois_label = mois_mapping[m]
                        if mois_label not in stats_by_patient:
                            stats_by_patient[mois_label] = {}
                        stats_by_patient[mois_label][row['code_patient']] = row['total']
                
                stats = stats_by_patient if stats_by_patient else stats
            
            return stats
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur chirurgies_par_patient_par_mois: {e}")
            return {}
        finally:
            self.db.close()

    def codes_patients_session(self, code_session: str) -> list:
        """
        Retourne la liste de tous les patients dans la table patients.
        Le champ a_consulte indique s'ils ont déjà une chirurgie dans la session donnée.
        """
        conn = self.db.connect()
        if not conn:
            return []
        try:
            cursor = conn.cursor(DictCursor)
            query = """
                SELECT p.code_patient, p.nom, p.prenom,
                       CASE WHEN EXISTS(
                           SELECT 1
                           FROM chururgie c
                           LEFT JOIN acte_medical am   ON c.code_acte = am.code_acte
                           LEFT JOIN consultation cons  ON am.code_consultation = cons.code
                           LEFT JOIN visite v2           ON cons.code_visite = v2.code_visite
                           WHERE v2.code_patient = p.code_patient AND v2.code_session = %s
                       ) THEN 1 ELSE 0 END AS a_consulte
                FROM patients p
                ORDER BY p.nom ASC, p.prenom ASC
            """
            cursor.execute(query, (code_session,))
            result = cursor.fetchall()
            return result
        except Exception as e:
            print(f"[ChirurgieDAO] Erreur codes_patients_session: {e}")
            return []
        finally:
            self.db.close()
